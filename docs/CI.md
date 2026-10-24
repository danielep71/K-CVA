# Repository integrity

Run from a Git checkout with Python 3.12.14, Node.js 24.22.1 and Git on PATH:

```sh
python tools/check_repository.py
```

This is the local and CI entry point. It exits nonzero on any failed check.
Python uses only the standard library; Node uses only built-in modules. No pip
or npm packages are required. The declared versions are the CI baseline; local
versions are recorded in evidence. Issue triage uses the same pinned Python
version; all label fixture, detection and reconciliation jobs explicitly set up
the same pinned Node version. The first run downloads actionlint 1.7.12
from its official release and verifies the platform archive against
[the checksum lock](../tools/actionlint-lock.json). Later runs reverify the cached
archive and extract only the named executable. Supported tooling platforms are
Linux, Windows and macOS on x64/ARM64. This is not Excel host certification.

The command checks issue configuration, all Python tooling tests, canonical
label self-tests, drift self-tests and CLI evidence regressions, Python/Node/JSON
syntax, relative Markdown links, action SHA pins, checkout credential settings,
workflow syntax/expressions with actionlint, and whitespace in all committed
content plus local staged/unstaged changes. The committed check compares HEAD
with Git's empty tree, so it works in clean and shallow CI checkouts without
fetching parent history. Untracked files must be staged to enter local checks.
Git's whitespace rules and binary-file handling apply.
Actionlint's optional ShellCheck and Pyflakes integrations are explicitly off
so local and hosted validation have the same declared dependencies. No VBA
compiler, CVA engine, numerical certification or live issue audit is implied.
Static VBA checks belong to #9; live issue triage retains its separate workflow.

`test-results/integrity/` contains individual logs and a JSON report with the
actual checkout commit, dirty flag, tracked-file SHA-256 digests, tool versions,
commands and exit codes. Stage intended new files before a local run so they
are included in tracked-file checks. A dirty local run describes those files,
not an immutable clean commit. CI tests GitHub's PR merge checkout and records
the PR head separately. Evidence is uploaded even on failure, named with the
checkout SHA, run ID and attempt, and retained for 30 days. Setup failures may
prevent report creation; upload then fails rather than claiming evidence exists.
Download selected evidence before expiry if it must be retained under #11.

The stable job/check name is **Repository integrity**. It runs without path
filters on PRs targeting main/release/**, pushes to those branches, and manual
dispatch. It has contents:read only and does not receive a write token. Required
check enforcement and up-to-date-branch rules remain #12; a workflow alone does
not configure branch protection.

## Dependency updates

Dependabot checks GitHub Actions weekly, targets release/0.1.0, assigns
@danielep71 and uses existing ci/P3 labels. Configuration becomes active when
present on the default branch. PRs have no milestone; create/link an issue with
the milestone when work needs tracking. There is no automatic approval, merge
or alert dismissal. Review release notes, provenance and the complete action
SHA, run integrity checks, and follow the final-head review policy.

Runtime baselines and actionlint's checksum lock are manually reviewed updates;
Dependabot does not update that custom lock. Obtain replacement archive digests
from the official release metadata/checksums, inspect the release and update all
supported platform entries together. Actions pins remain full commit SHAs.
