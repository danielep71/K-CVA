# Repository tooling

Existing tools: check_issues.py audits issue metadata and configuration;
test_check_issues.py exercises that policy. Their presence does not imply that
universal repository CI or numerical verification has been implemented.

Run existing checks from the repository root:

```sh
python tools/check_issues.py --check-config
python -m unittest discover -s tools -p 'test_check_issues.py'
```

Universal CI belongs to #6; static architecture checks to #9. Build and evidence
scripts may be added here with their own contracts. Regulatory reference
derivations belong in tests/derivations, never in repository policy checks.
Python tooling is not shipped as part of the workbook runtime.
