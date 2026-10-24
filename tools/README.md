# Repository tooling

Run `python tools/check_repository.py` for portable repository validation.
See [CI and dependency updates](../docs/CI.md) for pinned prerequisites, coverage,
local/hosted evidence and dependency review rules. The workflow's stable check
name is Repository integrity; required-check and strict up-to-date enforcement
are configured under #12. Controlled enforcement verification remains #13.

check_issues.py audits issue metadata and configuration; test_check_issues.py
exercises that policy. Live issue auditing remains a separate read-only workflow.
check_vba_*.py and vba_lexer.py are the static VBA checks, with fixtures in
test_check_vba.py; see docs/CI.md for their rules and limits. Build and
evidence scripts may be added here with their own contracts. Regulatory
reference derivations belong in tests/derivations, never in repository policy
checks. Python tooling is not shipped as part of the workbook runtime; no
numerical engine is validated here.
