# Verification

No numerical CVA test suite or host certification exists yet. This directory
holds the deterministic regression scaffold (#10): the VBA harness, its
neutral example suite and the test-case files. Evidence and host smoke
validation are #11. The repository tooling has its own tests in
[tools/](../tools/README.md).

| Location | Holds |
| --- | --- |
| `modules/` | VBA test modules: the harness `TEST_Harness` and the neutral example suite `TEST_Examples`. The case runner and the CVA suites come with the calculation |
| `fixtures/` | Synthetic inputs: counterparties, netting sets, hedges |
| `expected/` | Expected results, each with its provenance |
| `derivations/` | Python reference derivations that compute expected values from the documented method, separately from the code under test; created with the first one |
| `evidence/` | Deliberately retained, reviewed evidence tied to a source commit. An Excel run's evidence folder stays outside Git; its report is recorded in the issue ([recording an Excel run](../INSTALLATION.md#recording-an-excel-run), #11) |

The fixture and expected-result format, reference classes, tolerances and
completeness rules are defined in
[TEST_CASES.md](../docs/methodology/TEST_CASES.md) (#8) and checked by
`python tools/check_repository.py` (gate `test-cases`). The only case is an
illustrative format example.

- Fixtures are **synthetic**. Never commit real counterparties, portfolios,
  exposures, ratings or market data ([SECURITY.md](../SECURITY.md)).
- Test modules call the facade or the core directly; they never enter the
  production import set.
- Disposable run output belongs in `test-results/` at the repository root and
  is not committed.
- A scaffold pass does not certify a regulatory calculation. Reference
  calculations cite the methodology and explain their independence from
  production VBA. See [architecture](../docs/REPOSITORY_STRUCTURE.md) for
  contracts and placement.

<a id="vba-harness"></a>

## VBA harness

`TEST_Harness` runs one suite at a time. A suite calls `BeginRun` with its
name and its expected case and assertion counts, `BeginCase` with a
lower-case kebab-case identifier for each case, the assertions, and
`EndRun`. Each case has its own error handler that calls `RecordCaseError`,
so that one failing case does not stop the others.

| Assertion | Passes when |
| --- | --- |
| `AssertEqualDouble` | `Actual = Expected` exactly; only for results exact in binary |
| `AssertNear` | The difference is at most `max(absolute, relative × abs(Expected))`, both tolerances stated, as in [TEST_CASES.md](../docs/methodology/TEST_CASES.md#tolerance) |
| `AssertEqualText` | The texts are equal, compared binary |
| `AssertTrue` | The condition the suite evaluated is true |
| `AssertErrorValue` | The value is the given worksheet error, such as `#VALUE!` |
| `AssertRaised` | The `Err.Number` captured after the call is the expected one (0: nothing raised) |

A run passes only when every assertion passed, no unexpected error occurred,
exactly the expected cases and assertions ran, and Excel's `Calculation`,
`DisplayAlerts`, `EnableEvents` and `ScreenUpdating` are as they were at the
start. A skipped or extra case or assertion makes the run `INCOMPLETE`,
which is a failure. The harness never changes those settings itself.

`TEST_Examples` also holds the reference implementation of the cleanup
pattern of [VBA_HOUSE_STYLE.md](../docs/VBA_HOUSE_STYLE.md#operation-and-cleanup-outcomes),
`RunExampleOperation`, with its failure-path cases: a successful operation, a
primary failure with failed cleanup, a capture that fails part-way, a change
that fails after its restoration was registered, each restoration failing on
its own, and a cleanup-only failure. How to run the suite is in
[INSTALLATION.md](../INSTALLATION.md#running-the-harness).

<a id="log-format"></a>

### Log format

One record per line, `KEY=value`, with further fields separated by `; `.
`RUN` and `ENVIRONMENT` come first; `CASE`, `ASSERT`, `ERROR` and `FAILURE`
follow as the run reaches them; the summary records come last, in the order
of the table:

| Record | Fields |
| --- | --- |
| `RUN=<suite>` | `mode` (`NORMAL` or a deliberate failure mode), `expected_cases`, `expected_assertions`, `started` |
| `ENVIRONMENT=` | `host`, `version`, `build` (`Application.Build`), `os`, `office` (`64-bit` or `32-bit`), `runtime` (`VBA7` or `VBA6`) |
| `CASE=<case-id>` | One per case, in run order |
| `ASSERT=<case-id>/<name>` | `status` (`PASS` or `FAIL`); on failure, the expected and actual values |
| `FAILURE=<id>` | One per failure: an assertion, `<case-id>.unexpected-error`, `runner.unexpected-error`, `harness.case-id`, `harness.no-case` or `harness.completeness`, with its detail |
| `ERROR=<case-id>` or `ERROR=run` | `number`, `source`, `description` of an unexpected error |
| `CASES=<n>`, `ASSERTIONS=<n>` | `expected` |
| `FAILURES=<n>` | `errors` |
| `PRIMARY_FAILURE=<id>` | The first failure of the run, when there is one |
| `CLEANUP=PASS` or `FAIL` | `detail`: the settings compared, or those that changed |
| `RECOVERY=NONE` or `REQUIRED` | `reason`, `action`, when required |
| `RESULT=PASS` or `FAIL` | `suite`; `operation`, what ran: `PASS`, `FAIL` (an assertion or a case identifier failed) or `ERROR` (an unexpected error); `completeness` (`COMPLETE` or `INCOMPLETE`); `cases`, `assertions`, `failures`; `cleanup`; `recovery` |

`RESULT` is always the last record of a run. A refused start writes a
`RESULT=FAIL` with `operation=NOT_RUN` and a `RECOVERY=REQUIRED` record, and
`ResetTests` writes `RESET=DONE`. Case identifiers and assertion names are
fixed in the suite's source, so two logs of the same commit can be compared
line by line, apart from `started` and `ENVIRONMENT`.

The harness runs only in Excel and has not been run yet: compiling and
running it on the intended host is #11, recorded as in
[recording an Excel run](../INSTALLATION.md#recording-an-excel-run) and
checked against its commit by `tools/check_excel_run.py`. Without Excel,
`tools/test_vba_harness.py` checks what the source can show: the example
suite's counts equal its cases and assertions, every case runs once with a
unique identifier, and every documented record is written.
