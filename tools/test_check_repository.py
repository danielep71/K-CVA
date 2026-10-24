"""Regressions for whitespace validation in clean and local Git checkouts."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_repository import whitespace_commands


class WhitespaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.autocrlf', 'false')

    def git(self, *args):
        return subprocess.check_output(['git', *args], stderr=subprocess.STDOUT)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture')

    def outcomes(self):
        return {name: subprocess.run(command, capture_output=True).returncode
                for name, command in whitespace_commands()}

    def test_clean_committed_trailing_whitespace_fails(self):
        Path('fixture.txt').write_bytes(b'bad trailing space \n')
        self.commit()
        self.assertEqual(self.git('status', '--porcelain'), b'')
        # The former implementation passes on precisely this bad checkout.
        self.assertEqual(self.git('diff', '--check', 'HEAD'), b'')
        self.assertNotEqual(self.outcomes()['whitespace-committed'], 0)

    def test_clean_text_crlf_and_binary_pass(self):
        Path('.gitattributes').write_text('*.cmd text eol=crlf\n*.bin binary\n')
        Path('fixture.txt').write_bytes(b'clean\n')
        Path('fixture.cmd').write_bytes(b'echo clean\r\n')
        Path('fixture.bin').write_bytes(b'\x00binary \n')
        self.commit()
        self.assertEqual(set(self.outcomes().values()), {0})

    def test_local_staged_and_unstaged_whitespace_fail(self):
        Path('fixture.txt').write_bytes(b'clean\n')
        self.commit()
        Path('fixture.txt').write_bytes(b'bad\t\n')
        self.assertNotEqual(self.outcomes()['whitespace-local'], 0)
        self.git('add', 'fixture.txt')
        self.assertNotEqual(self.outcomes()['whitespace-local'], 0)


if __name__ == '__main__':
    unittest.main()
