# Developer setup and VBA import/export

**Setup only:** no production VBA component, template or workbook exists yet;
tests/modules holds the test harness and its neutral example suite (#10). The
procedures below define the convention for components; they have not been
executed in Excel. The first real host run belongs to #11.
Contribution rules are in [CONTRIBUTING.md](CONTRIBUTING.md); portable CI is documented in
[docs/CI.md](docs/CI.md).

## Host policy

The intended initial target is Microsoft 365 Excel desktop on Windows, 64-bit.
No Excel build is currently tested or certified. Windows 32-bit, older perpetual
Excel versions, Mac and web are not supported targets for this baseline.
Adding support requires a recorded decision and evidence.

Use only the default VBA, Excel, OLE Automation and Office references supplied
by the target Excel installation. Record their exact versions in host evidence;
no additional reference is approved. Check Tools > References for MISSING
entries before compilation. Any new reference needs a reviewed dependency
decision. Python is tooling/reference testing only and is never called by the
workbook. Follow organizational macro policy; do not weaken security settings.

<a id="tested-environments"></a>

| Tested environment | Commit | Evidence |
| --- | --- | --- |
| None yet | Not applicable | Pending the first [recorded Excel run](#recording-an-excel-run) (#11) |

## Obtain an exact source revision

With authorized access to the private repository:

```sh
git clone https://github.com/danielep71/K-CVA.git
cd K-CVA
git switch release/0.1.0
git rev-parse HEAD
git status --short
```

Record the full SHA and start from a clean checkout. Task branches are cut from
release/0.1.0 under [governance](docs/GOVERNANCE.md).
Use a Git checkout for VBA import: .gitattributes produces CRLF working files.
Raw downloads and source archives use stored blobs and do not apply the checkout
conversion, even though archives retain configuration. Do not mix revisions.

<a id="developer-setup"></a>

## Developer setup

| Prerequisite | Version | Used for |
| --- | --- | --- |
| Git | Any current release | Checkout with the repository's line-ending rules |
| Python | 3.12.14 (the CI baseline) | `tools/check_repository.py` and its standard-library checks |
| Node.js | 24.22.1 (the CI baseline) | Label scripts and their self-tests; built-in modules only |
| Microsoft 365 Excel, Windows, 64-bit | Not yet tested (#11) | Importing, compiling and running VBA ([host policy](#host-policy)) |

No pip or npm package is installed. The first run downloads actionlint 1.7.12
and verifies it against [tools/actionlint-lock.json](tools/actionlint-lock.json)
([CI](docs/CI.md)). From the repository root, run every check:

```sh
python tools/check_repository.py
```

It ends with one `PASS` or `FAIL` line per check and exits nonzero on any
failure. Stage new files before running it: untracked files are not checked.
Other Python and Node versions may work; the declared versions are what CI
runs, and evidence records the versions actually used.

Where evidence goes:

| Evidence | Location |
| --- | --- |
| Repository checks: one log per check and a JSON report with the checkout commit, tracked-file hashes and tool versions | `test-results/integrity/` (ignored, not committed); CI uploads it as an artifact kept 30 days |
| Harness log | The Immediate window, or `TEST_Harness.SaveLog` to `test-results/` or a folder outside the checkout ([running the harness](#running-the-harness)) |
| Excel run: the three logs, the exported modules and `host.txt` | An evidence folder such as `test-results/excel-run/` (ignored, not committed); the `check_excel_run.py` report is copied into the issue or pull request ([recording an Excel run](#recording-an-excel-run)) |
| Other retained, reviewed evidence tied to a commit | `tests/evidence/` |

## Importing VBA into Excel

1. Create a disposable blank workbook, or use an explicitly approved future
   macro-free source template. Save an .xlsm outside the checkout or under
   test-results/. No template exception is currently approved.
2. Open the VBE (Alt+F11), select that workbook's project and check references.
   Confirm the target workbook explicitly; never rely on whichever is active.
3. Import .bas/.cls components from src/core, src/classes and src/modules,
   then standard .bas adapters from src/workbook. Sort filenames for repeatable
   imports. Skip absent directories. Compile only after the full component set
   is present. Start fresh to avoid duplicate or obsolete components.
4. Import .frm files from src/forms with their .frx companions alongside them;
   never import .frx separately.
5. For ThisWorkbook and sheet document modules, do not import exported .cls
   files as ordinary classes. Map each file to the existing document component
   by its code name, creating required sheets only as the future build contract
   specifies. Paste executable/declaration code into that component, excluding
   serialized VERSION/BEGIN/END headers and all Attribute metadata lines.
   Hidden attributes require a reviewed round-trip method before such components
   are accepted; do not silently lose them.
6. Development workbooks may additionally import tests/modules, which holds
   the harness and its example suite ([running the harness](#running-the-harness)).
   Production workbooks exclude tests and examples.
7. Run Debug > Compile VBAProject, save and run the documented tests when they
   exist. Record the full SHA, Excel build/bitness, Windows version, references,
   commands/entry points and outputs. Reopen in a clean session when required.

Manual import does not require enabling Trust access to the VBA project object
model. Enable execution only through approved organizational controls.

## Exporting changes

Export changed components into a temporary directory first. Preserve their VBE
headers and metadata; verify filename stems against Attribute VB_Name.
For document modules, export the existing component as .cls for comparison,
then update the matching src/workbook file after reviewing code name and hidden
attribute differences. Never replace the workbook component by importing that
.cls. Form .frm/.frx changes are reviewed and copied as a pair.

Compare exports with the exact checkout, reject non-ASCII source and unexpected
case/metadata changes, then copy intended changes into the correct source paths.
Do not hand-edit binary .frx files. Git normalizes source line endings on add.

Run the checks before committing ([developer setup](#developer-setup)):

```sh
python tools/check_repository.py
```

These checks validate repository infrastructure, not VBA compilation or CVA
correctness. See [CI coverage and prerequisites](docs/CI.md). The
[VBA static checks](docs/CI.md#vba-static-checks) are part of that command and
are not compilation. Required-check and strict up-to-date enforcement are
configured under #12 and were demonstrated under #13
([demonstrated enforcement](docs/GOVERNANCE.md#demonstrated-enforcement)).

<a id="running-the-harness"></a>

## Running the harness

Not yet run: the first host run, with its evidence, is #11; to record a run
as evidence, follow [recording an Excel run](#recording-an-excel-run). In a
**development** workbook built as above, open the Immediate window
(**Ctrl+G**) and type:

```text
TEST_Examples.RunExampleTests
```

It runs the example suite through `TEST_Harness` and writes one record per
line. A passing run ends with:

```text
RESULT=PASS; suite=examples; operation=PASS; completeness=COMPLETE; cases=12; assertions=27; failures=0; cleanup=PASS; recovery=NONE
```

Anything else, or the error *Suite examples did not pass*, is a failure. Two
more entry points show the failure paths and are expected to fail:

| Entry point | Expected end |
| --- | --- |
| `TEST_Examples.RunExampleTestsWithInjectedFailure` | `RESULT=FAIL`, `operation=FAIL`, `completeness=COMPLETE`, `failures=1`, then *Suite examples did not pass* |
| `TEST_Examples.RunExampleTestsWithSkippedCase` | `RESULT=FAIL`, `operation=PASS`, `completeness=INCOMPLETE`, `cases=11`, `assertions=25`, `failures=1`, then *Suite examples did not pass* |

- **Complete log.** The Immediate window keeps only its last 200 lines. To
  keep the whole run, type `TEST_Harness.SaveLog "<folder>\examples.log"`
  after it, with a folder outside the checkout or the ignored
  `test-results/` directory.
- **Recovery.** A run that stopped half way, or that changed Excel settings it
  did not restore, leaves `recovery=REQUIRED`, and the next run is refused.
  Check **File → Options → Formulas** (calculation) and the other settings the
  log names, then type `TEST_Harness.ResetTests`.
- **What it proves.** The suite exercises the harness itself: assertions,
  tolerances, error values, raised errors, completeness and the cleanup
  pattern. It contains no CVA calculation, and a passing run validates none.
  The log format is in [tests/README.md](tests/README.md#log-format).

<a id="recording-an-excel-run"></a>

## Recording an Excel run

The evidence that a commit's VBA was imported, compiled and run on a host,
for [#11](https://github.com/danielep71/K-CVA/issues/11) and for every later
issue or pull request that cites an Excel run. It needs no self-hosted
runner, no change to the macro-security level and no *Trust access to the
VBA project object model*.

1. **Fix the candidate.** In a clone with no local changes
   (`git status --short` prints nothing), type `git switch --detach <commit>`,
   then `git rev-parse HEAD` for the full SHA.
2. **Make the evidence folder**, for example `test-results\excel-run\` in the
   checkout (ignored by Git), with an empty `exported\` folder inside.
3. **Build a development workbook** from that checkout as in
   [importing VBA into Excel](#importing-vba-into-excel), with the modules of
   `tests/modules/`.
4. **Compile** with **Debug → Compile VBAProject**.
5. **Run.** In the Immediate window type, with the full path of the folder
   and no trailing backslash:

   ```text
   TEST_Examples.SaveExampleEvidence "C:\path\to\test-results\excel-run"
   ```

   It runs the suite normally, with the injected failure and with the
   skipped case, and saves each complete log as `examples.log`,
   `injected.log` and `skipped.log`. Each run prints a `SAVED=` line: the
   normal run with `error=0`, the two failure runs with the error *Suite
   examples did not pass*. The errors are printed, not raised, so that all
   three logs are written.
6. **Export the modules back.** In the VBE, right-click each module →
   **Export File**, into `exported\`, under its own name
   (`TEST_Examples.bas`, `TEST_Harness.bas`). Do not edit the exported files.
7. **Write `host.txt`** in the folder:

   ```text
   windows=Windows 11 Pro, version 24H2, OS build 26100.4061
   references=Visual Basic For Applications; Microsoft Excel 16.0 Object Library; OLE Automation; Microsoft Office 16.0 Object Library
   compile=PASS
   ```

   `windows` is what `winver` shows. `references` lists the boxes ticked
   in **Tools → References**, separated by `; `. Write `compile=PASS` only if
   step 4 completed with no error; otherwise write what it reported.
8. **Check** the folder against the commit, with Python 3.12 or later and Git:

   ```sh
   python tools/check_excel_run.py test-results/excel-run --commit <commit>
   ```

   It must end with `excel-run: PASS`. It prints the commit, the host and
   the Git blob id of every imported component.
9. **Record.** Copy the report into the issue or pull request and add a row
   to [tested environments](#tested-environments). The folder stays outside
   Git: its exported modules would be second copies of the VBA components.

`check_excel_run.py` reads only the folder and the commit:

| It fails when | Because |
| --- | --- |
| An exported module differs from the commit's file, or one is missing or extra | The workbook was not built from that commit |
| A log is missing or empty, does not end with `RESULT`, holds more than one run, or a line is not a `KEY=value` record | The log is incomplete |
| A record is missing, extra or out of the order in which the commit's suite writes it, or an unexpected error (`ERROR`) is logged | The run did not execute the suite as written |
| The normal run is not `RESULT=PASS`, or its cases and assertions differ from the commit's suite in name or order | The run did not pass as written |
| `CLEANUP` is not `PASS` or `RECOVERY` is not `NONE` in any of the three logs | Cleanup failed |
| The two failure runs do not end as [documented](#running-the-harness), or fail anything but their own failure: the injected run its one designated assertion, with the expected value the suite injects and the same values in each record, the skipped-case run only `harness.completeness` | The failure paths did not behave |
| `ENVIRONMENT` lacks a field, differs between the logs, or Office is not 64-bit | The host is unknown or not the supported target |
| `host.txt` lacks a field, the references are not exactly the four [default](#host-policy) ones, or `compile` is not `PASS` | The host record is incomplete |

It cannot see Excel: the compile result, the references and the Windows
build are the runner's own record. A PASS says the evidence is consistent
with the commit; it validates no CVA calculation.

## Git hygiene verification

```sh
git check-attr text eol diff merge -- src/core/CORE_Example.bas src/forms/frmExample.frx
git check-ignore -v --no-index test-results/run.log sample.xlsm .env
git add --renormalize --dry-run .
```

The example component paths are probes, not installed components. Inspect any
normalization before applying it. Stage only intended changes, then run
git diff --cached --check. Retained reviewed evidence goes in tests/evidence;
disposable output goes in test-results. Ignore rules do not remove already
tracked files and are not a secret scanner.

See [house style](docs/VBA_HOUSE_STYLE.md),
[architecture](docs/REPOSITORY_STRUCTURE.md), [security](SECURITY.md) and
[provenance](NOTICE.md).
