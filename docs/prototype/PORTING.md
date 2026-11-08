# Prototype port — issue #180

This is a mechanical intake port, not numerical, regulatory or Excel acceptance.
The maintainer scoped v0.2.0 to porting and tooling on 2026-11-08. Formula
remediation, regulatory validation and new functionality remain later work.

## Source and provenance

The [original archive](K-CVA-Prototype.zip) is preserved byte for byte from
[intake commit 8abe872](https://github.com/danielep71/K-CVA/blob/8abe872f17dd7ea005c07ed8d42790945988ca9c/docs/prototype/K-CVA-Prototype.zip).
Its verified SHA256 is
`d756a85d23223b54c1ce4e94693b03e9a35c6e8d694f631d98ef8a4fd71036bb`.
[INTAKE_SHA256.json](INTAKE_SHA256.json) preserves the original member hashes;
[PORT_MANIFEST.json](PORT_MANIFEST.json) maps every archive member to its
destination and records source byte hashes and Git-normalized ported hashes. Git normalizes text to LF;
VBA and Windows scripts are checked out with CRLF under .gitattributes.
The original ZIP is the authoritative record of original bytes.

Layout was checked against K-SACCR at
`f831561caba40b1b686a20035f0a76d91eea2d48`: core/modules/workbook,
`src/workbook/SACCR_Template.xlsx`, tests/derivations and tools. Its layout is
a design reference only. K-CVA owns its API, architecture and methodology.

## Ownership and placement

| Destination | Responsibility |
| --- | --- |
| `src/core/CORE_BACVA.bas` | Pure prototype calculation and input checks; unchanged formulas |
| `src/modules/CVA_Functions.bas` | Three facade functions recorded in PUBLIC_API.txt |
| `src/workbook/M_Main.bas`, `ThisWorkbook.cls` | Excel mapping, buttons and events |
| `src/workbook/CVA_Template.xlsx` | Byte-identical macro-free source template; sole workbook ignore exception |
| `tools/Build-CVA.cmd`, `Build-CVA.ps1` | Windows COM builder; imported source remains authoritative |
| `tests/modules/TEST_Prototype.bas` | Original prototype suite, separate from the setup harness |
| `tests/fixtures/prototype/cases.json` | Original synthetic intake cases |
| `tests/expected/prototype/expected.json` | Original unvalidated intake expectations |
| `tests/derivations/prototype_reference.py` | Original Decimal reference; independence not certified by porting |
| `docs/contracts/PROTOTYPE.md`, `docs/methodology/PROTOTYPE.md` | Intake contract and methodology claims retained for review |
| `docs/prototype/` | Original ZIP, provenance, hashes, instructions and validation limitations |

The nested `prototype/` fixture folders deliberately distinguish the intake
schema from the registered fixture schema enforced by `check_test_cases.py`.
These cases have not been registered as regulatory validation evidence. The
original assertions, constants and expected values are retained without repair.

## Mechanical changes

- Builder resolves the repository root as the parent of tools, reads the named
  template under src/workbook, and writes workbook and evidence to ignored
  build/. Existing output is still refused. Import membership is unchanged:
  src .bas files and TEST_Prototype, with ThisWorkbook code injected into the
  document module. The setup TEST_Harness/TEST_Examples are not imported.
- The reference script resolves the root two parents above tests/derivations
  and writes to tests/expected/prototype/expected.json. No arithmetic changed.
- VBA comments point to the relocated contract/methodology. Executable VBA
  statements and signatures are unchanged; the core and ThisWorkbook bytes
  are preserved before Git line-ending normalization.
- Start instructions use repository paths and build/ output. Validation notes
  point to the relocated evidence path. Intake documentation is explicitly
  marked unvalidated; original versions remain inside the ZIP.
- The source checker allows only the exact template path, with regression cases
  rejecting other names, locations and extensions. The API regression now checks
  the real facade source rather than assuming an empty source directory.
- API inventory lists CVA_Calculate, CVA_Discount and CVA_RiskWeight with their
  exact declarations. Module names, error ownership and dependency direction
  are unchanged. The architectural obligations still apply; the port does not
  certify the completeness of intake contracts or regulatory claims.
- Root and directory guides distinguish the earlier setup baseline from the
  prototype port. Changelog, provenance and the narrow .gitignore exception
  are included for review.

## Running and acceptance limits

On Windows desktop Excel follow [START-HERE.txt](START-HERE.txt) and run
`tools\Build-CVA.cmd` from the checkout. Output is
`build/K-CVA_Prototype.xlsm` and `build/Excel-build-evidence.txt`.
The builder retains the original numerical smoke assertions. A successful
operational build would not constitute numerical acceptance for v0.2.0.
The macro-free template still contains its original package instructions;
use the repository instructions linked here for relocated paths.

Native Excel, VBA compilation/execution, COM execution and UI/event behavior
were not run in this Linux environment. The earlier setup harness evidence
does not cover these newly ported modules. See [validation notes](VALIDATION.md)
for the original pending host checks. Final check results belong in the task PR.
