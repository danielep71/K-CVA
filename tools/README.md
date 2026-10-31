# Repository tooling

Run `python tools/check_repository.py` for portable repository validation.
See [CI and dependency updates](../docs/CI.md) for pinned prerequisites, coverage,
local/hosted evidence and dependency review rules. The workflow's stable check
name is Repository integrity; required-check and strict up-to-date enforcement
are configured under #12 and were demonstrated under #13.

check_issues.py audits issue metadata and configuration; test_check_issues.py
exercises that policy. Live issue auditing remains a separate read-only workflow.
check_vba_*.py and vba_lexer.py are the static VBA checks, with fixtures in
test_check_vba.py; see docs/CI.md for their rules and limits.
check_test_cases.py checks the numerical test-case files against
docs/methodology/TEST_CASES.md, with fixtures in test_check_test_cases.py;
test_vba_harness.py checks what the VBA harness source can show without Excel.
check_changelog.py checks CHANGELOG.md and VERSION against RELEASING.md, with
fixtures in test_check_changelog.py; it never tags or publishes.
check_excel_run.py checks the evidence folder of an Excel run against its
commit (INSTALLATION.md, Recording an Excel run), with fixtures in
test_check_excel_run.py; it is not a gate, since it needs a host run.
check_links.py checks relative Markdown links and their anchors by GitHub's
slug rule; check_external_links.py, run weekly by the External links
workflow, reports broken http(s) links; both have fixtures in
test_check_links.py (docs/CI.md, Markdown links).
check_workflows.py parses the workflows as YAML and checks their permissions,
timeouts, pins, checkout credentials and the required check
(docs/CI.md, Workflow rules), with fixtures in test_check_workflows.py.
requirements.txt locks the Python packages the checks use (PyYAML,
markdown-it-py, Ruff, mypy and their dependencies) with the hash of every wheel; pyproject.toml
configures Ruff and strict mypy (docs/CI.md, Python quality gates).
traffic_history.py merges traffic API responses into the traffic-history
branch (docs/TRAFFIC.md), with fixtures in test_traffic_history.py. Build and
evidence scripts may be added here with their own contracts. Regulatory
reference derivations belong in tests/derivations, never in repository policy
checks. Python tooling is not shipped as part of the workbook runtime; no
numerical engine is validated here.
