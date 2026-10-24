"""Portable, read-only repository checks; evidence describes the tested tree."""
from pathlib import Path
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results' / 'integrity'


def actionlint():
    lock = json.loads((ROOT / 'tools/actionlint-lock.json').read_text())
    machine = {'x86_64': 'amd64', 'amd64': 'amd64', 'aarch64': 'arm64', 'arm64': 'arm64'}.get(platform.machine().lower())
    key = platform.system().lower() + '_' + str(machine)
    if key not in lock['assets']:
        raise RuntimeError('Unsupported actionlint platform: ' + key)
    asset = lock['assets'][key]
    archive = ROOT / '.cache' / ('actionlint-' + asset['sha256'])
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists():
        with urllib.request.urlopen(asset['url'], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != asset['sha256']:
            raise RuntimeError('actionlint download checksum mismatch')
        archive.write_bytes(data)
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != asset['sha256']:
        raise RuntimeError('actionlint cache checksum mismatch')
    name = 'actionlint.exe' if os.name == 'nt' else 'actionlint'
    if os.name == 'nt':
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            binary = package.read(name)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as package:
            binary = package.extractfile(name).read()
    executable = archive.parent / name
    executable.write_bytes(binary)
    executable.chmod(0o755)
    return str(executable)


def whitespace_commands():
    """Check all committed content, then local changes, without needing history."""
    empty_tree = subprocess.check_output(
        ['git', 'hash-object', '-t', 'tree', '--stdin'], input=b''
    ).decode().strip()
    return [
        ('whitespace-committed', ['git', 'diff', '--check', empty_tree, 'HEAD']),
        ('whitespace-local', ['git', 'diff', '--check', 'HEAD']),
    ]


def main():
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    paths = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    tracked = [p for p in paths if p]
    files = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in tracked if Path(p).is_file()}
    report = {
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'])),
        'github_head_sha': os.environ.get('PR_HEAD_SHA'),
        'python': sys.version, 'platform': platform.platform(),
        'files_sha256': files, 'checks': [],
        'scope': 'Repository infrastructure only; no numerical or Excel certification',
    }
    def run(name, command):
        try:
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
            output, code = result.stdout, result.returncode
        except (OSError, subprocess.TimeoutExpired) as error:
            output, code = str(error), 1
        (OUT / (name + '.log')).write_text(output, encoding='utf-8')
        report['checks'].append({'name': name, 'command': command, 'exit_code': code})
        print(name + ': ' + ('PASS' if code == 0 else 'FAIL'), flush=True)
        if code:
            print(output, flush=True)
    try:
        run('node-version', ['node', '--version'])
        run('issue-config', [sys.executable, 'tools/check_issues.py', '--check-config'])
        run('python-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_*.py'])
        run('label-sync', ['node', '.github/scripts/labels-sync.mjs', '--self-test'])
        run('label-drift', ['node', '.github/scripts/labels-drift.mjs', '--self-test'])
        run('label-evidence', ['node', '--test', '.github/scripts/test-labels-drift.mjs'])
        for path in tracked:
            if path.endswith('.mjs'):
                run('syntax-' + Path(path).stem, ['node', '--check', path])
            if path.endswith('.py'):
                compile(Path(path).read_text(encoding='utf-8'), path, 'exec')
            if path.endswith('.json'):
                json.loads(Path(path).read_text(encoding='utf-8'))
        for path in tracked:
            if path.endswith('.md'):
                for target in re.findall(r'\]\(([^)]+)\)', Path(path).read_text(encoding='utf-8')):
                    if '://' not in target and not target.startswith(('#', 'mailto:')):
                        if not (Path(path).parent / target.split('#')[0]).exists():
                            raise RuntimeError('Missing relative link: ' + path + ': ' + target)
        workflows = sorted(str(p) for p in Path('.github/workflows').glob('*.y*ml'))
        for path in workflows:
            text = Path(path).read_text()
            for use in re.findall(r'uses:\s*(\S+)', text):
                if not re.fullmatch(r'[\w.-]+/[\w./-]+@[0-9a-f]{40}', use):
                    raise RuntimeError('Unpinned action: ' + use)
            if 'actions/checkout@' in text and 'persist-credentials: false' not in text:
                raise RuntimeError('Checkout credentials persist: ' + path)
        validator = actionlint()
        run('actionlint-version', [validator, '-version'])
        run('workflow-validation', [validator, '-shellcheck=', '-pyflakes=', *workflows])
        for name, command in whitespace_commands():
            run(name, command)
    except Exception as error:
        report['checks'].append({'name': 'repository-validation', 'exit_code': 1, 'error': str(error)})
        print(str(error), file=sys.stderr)
    report['status'] = 'pass' if all(x['exit_code'] == 0 for x in report['checks']) else 'fail'
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
