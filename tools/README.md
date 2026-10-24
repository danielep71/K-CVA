# Repository tooling

Run `python tools/check_repository.py` for portable repository validation.
See [CI and dependency updates](../docs/CI.md) for pinned prerequisites, coverage,
local/hosted evidence and dependency review rules. The workflow's stable check
name is Repository integrity; required-check enforcement remains #12.

check_issues.py audits issue metadata and configuration; test_check_issues.py
exercises that policy. Live issue auditing remains a separate read-only workflow.
Static architecture checks follow in #9. Build and evidence scripts may be added
here with their own contracts. Regulatory reference derivations belong in
tests/derivations, never in repository policy checks. Python tooling is not
shipped as part of the workbook runtime; no numerical engine is validated here.
