"""Regressions for committed whitespace and verified actionlint archive retrieval."""
import hashlib
import http.client
import io
import os
import socket
import subprocess
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from check_repository import verified_archive, whitespace_commands


class WhitespaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.autocrlf', 'false')

    def git(self, *args: str) -> bytes:
        return subprocess.check_output(['git', *args], stderr=subprocess.STDOUT)

    def commit(self) -> None:
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture')

    def outcomes(self) -> dict[str, int]:
        return {name: subprocess.run(command, capture_output=True, check=False).returncode
                for name, command in whitespace_commands()}

    def test_clean_committed_trailing_whitespace_fails(self) -> None:
        Path('fixture.txt').write_bytes(b'bad trailing space \n')
        self.commit()
        self.assertEqual(self.git('status', '--porcelain'), b'')
        # The former implementation passes on precisely this bad checkout.
        self.assertEqual(self.git('diff', '--check', 'HEAD'), b'')
        self.assertNotEqual(self.outcomes()['whitespace-committed'], 0)

    def test_clean_text_crlf_and_binary_pass(self) -> None:
        Path('.gitattributes').write_text('*.cmd text eol=crlf\n*.bin binary\n')
        Path('fixture.txt').write_bytes(b'clean\n')
        Path('fixture.cmd').write_bytes(b'echo clean\r\n')
        Path('fixture.bin').write_bytes(b'\x00binary \n')
        self.commit()
        self.assertEqual(set(self.outcomes().values()), {0})

    def test_local_staged_and_unstaged_whitespace_fail(self) -> None:
        Path('fixture.txt').write_bytes(b'clean\n')
        self.commit()
        Path('fixture.txt').write_bytes(b'bad\t\n')
        self.assertNotEqual(self.outcomes()['whitespace-local'], 0)
        self.git('add', 'fixture.txt')
        self.assertNotEqual(self.outcomes()['whitespace-local'], 0)


class ArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / 'cache' / 'actionlint-digest'
        self.payload = b'locked fixture archive'
        self.digest = hashlib.sha256(self.payload).hexdigest()
        self.url = 'https://example.invalid/archive'

    def load(self) -> bytes:
        return verified_archive(self.archive, self.url, self.digest)

    def test_valid_cache_never_uses_network(self) -> None:
        self.archive.parent.mkdir()
        self.archive.write_bytes(self.payload)
        with patch('check_repository.urllib.request.urlopen') as request:
            self.assertEqual(self.load(), self.payload)
            request.assert_not_called()

    def test_corrupt_cache_rejected_without_download(self) -> None:
        self.archive.parent.mkdir()
        self.archive.write_bytes(b'corrupt')
        with patch('check_repository.urllib.request.urlopen') as request:
            with self.assertRaisesRegex(RuntimeError, 'cache checksum mismatch'):
                self.load()
            request.assert_not_called()

    def test_transient_failures_then_success(self) -> None:
        failures = [urllib.error.HTTPError(self.url, 504, 'gateway', Message(), None),
                    TimeoutError('read'), http.client.IncompleteRead(b'part')]
        with patch('check_repository.urllib.request.urlopen',
                   side_effect=[*failures, io.BytesIO(self.payload)]) as request, \
                patch('check_repository.time.sleep') as sleep:
            self.assertEqual(self.load(), self.payload)
            self.assertEqual(request.call_count, 4)
            self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 4, 8])
        self.assertEqual(self.archive.read_bytes(), self.payload)
        self.assertEqual(list(self.archive.parent.iterdir()), [self.archive])

    def test_exhaustion_leaves_no_cache(self) -> None:
        with patch('check_repository.urllib.request.urlopen',
                   side_effect=urllib.error.URLError(TimeoutError('read'))) as request, \
                patch('check_repository.time.sleep'):
            with self.assertRaisesRegex(RuntimeError, 'after 4 attempts'):
                self.load()
            self.assertEqual(request.call_count, 4)
        self.assertFalse(self.archive.exists())

    def test_permanent_http_and_url_errors_not_retried(self) -> None:
        for error in [urllib.error.HTTPError(self.url, 404, 'missing', Message(), None),
                      urllib.error.URLError('invalid certificate'),
                      urllib.error.URLError(socket.gaierror(socket.EAI_NONAME, 'unknown host'))]:
            with self.subTest(error=error), \
                    patch('check_repository.urllib.request.urlopen', side_effect=error) as request, \
                    patch('check_repository.time.sleep') as sleep:
                with self.assertRaises(type(error)):
                    self.load()
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()
                self.assertFalse(self.archive.exists())

    def test_temporary_dns_failure_is_retried(self) -> None:
        error = urllib.error.URLError(socket.gaierror(socket.EAI_AGAIN, 'temporary DNS failure'))
        with patch('check_repository.urllib.request.urlopen',
                   side_effect=[error, io.BytesIO(self.payload)]) as request, \
                patch('check_repository.time.sleep') as sleep:
            self.assertEqual(self.load(), self.payload)
            self.assertEqual(request.call_count, 2)
            sleep.assert_called_once_with(2)

    def test_wrong_download_hash_not_cached_or_retried(self) -> None:
        with patch('check_repository.urllib.request.urlopen', return_value=io.BytesIO(b'wrong')) as request, \
                patch('check_repository.time.sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError, 'download checksum mismatch'):
                self.load()
            self.assertEqual(request.call_count, 1)
            sleep.assert_not_called()
        self.assertFalse(self.archive.exists())

    def test_failed_atomic_publish_removes_temporary_file(self) -> None:
        with patch('check_repository.urllib.request.urlopen', return_value=io.BytesIO(self.payload)), \
                patch.object(Path, 'replace', side_effect=OSError('disk error')), self.assertRaises(OSError):
            self.load()
        self.assertEqual(list(self.archive.parent.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
