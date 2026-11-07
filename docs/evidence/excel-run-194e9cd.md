# Excel scaffold run on integrated main

Issue #11. Report supplied by the maintainer in the project conversation on
2026-11-07 after running `tools/Record-KCVA-ExcelRun.cmd` on Windows.
Candidate: `194e9cd322b5a86a58bf54e025d931b17cc13276` (main integration #164).

## Retained validator report

The following is the maintainer-supplied validator output. Local filesystem
paths and the command-window prompt are omitted; no runtime record is invented.

```text
Candidate commit: 194e9cd322b5a86a58bf54e025d931b17cc13276
Environment: host=Microsoft Excel; version=16.0; build=20430; os=Windows (64-bit) NT 10.00; office=64-bit; runtime=VBA7
Windows: Windows 11 Enterprise, version 25H2, OS build 26200.9711
References: Visual Basic For Applications; Microsoft Excel 16.0 Object Library; OLE Automation; Microsoft Office 16.0 Object Library
Compile: PASS
Imported components (Git blob ids at the commit):
  TEST_Examples.bas 4cfb38aa8ae3c51b5f2df6152b74818a3c8ce9bb
  TEST_Harness.bas 1a3e60b90c781e71109ce87b9cedae0bc9ef10c5
excel-run: PASS (evidence checked against the commit; Excel is not run here and no CVA calculation is validated)
```

The surrounding recorder output confirms import of both modules, compile PASS,
and saving `examples.log`, `injected.log` and `skipped.log`, followed by export
and the successful check. This supersedes the pending main-run status in #11;
the earlier branch trial remains separate historical evidence.

## Interpretation and limits

The maintainer executed Excel. The Python checker then validated its output
against the candidate; its wording "Excel is not run here" describes the
checker, not the preceding recorder steps. A checker PASS requires the normal
suite to pass, the injected failure and skipped-case runs to fail as specified,
and cleanup/recovery records to match the contract. It does not mean all three
logs contain `RESULT=PASS`.

The full logs, exported modules and `host.txt` remain in the maintainer's
local evidence folder. They were not attached for independent revalidation;
this retained report is operator-supplied evidence, not a second execution.
No independent claim about the actual VBA-project-access registry value is
made from this excerpt. No CVA formula, production workbook, other Excel build,
32-bit host, Mac or web environment is validated or certified by this run.

## Source and static corroboration

A clean detached checkout of the same main commit passed all 24 repository
integrity gates and 238 Python tests on Linux, with `dirty=false`, Python
3.12.14 and Node 24.22.1. The 14 Excel-evidence validator fixtures also passed
separately. Git independently confirms both component blob IDs above.
Main hosted integrity run 42415055917 and CodeQL run 42415055915 passed.
These are static corroboration, not substitutes for the maintainer's host run.

This evidence-recording change modifies documentation only. It does not alter
the candidate's VBA components, recorder or validator; the run remains bound
to the full SHA above. Later candidate changes must be assessed explicitly at
closeout rather than silently rebinding this evidence to another commit.
