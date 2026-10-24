# Repository structure

This document owns artifact placement, dependency direction and API conventions.
[DECISIONS.md](DECISIONS.md) owns scope choices and unresolved questions.
[GOVERNANCE.md](GOVERNANCE.md) owns branch and review rules.

## Product boundary

The intended application computes regulatory CVA capital under a selected,
documented regime. It does not initially price economic/accounting CVA or provide
a general exposure simulation engine. Inputs needed by the selected approach
must be defined explicitly; the application must never equate a valuation
adjustment with a regulatory capital requirement.

No engine or workbook exists yet. Architecture is a design for subsequent work,
not evidence of implemented or validated functionality.

## Locations

| Location | Responsibility | Current status |
| --- | --- | --- |
| `.github/` | Workflow configuration, issue forms and canonical labels | Present, including Repository integrity CI, Dependabot version updates (#6) and PR template (#7). Required-check enforcement configured under #12 and demonstrated under #13. |
| `docs/` | Governance, architecture, decisions and API inventory | Present. |
| `docs/methodology/` | Dated source register, approach decisions and fixture contract | Methodology skeleton, source register with a copy of the controlling text, and test-case contract (#8); no formula transcribed. |
| `docs/contracts/` | Versioned public input/output contracts | Reserved until the first real contract. |
| `src/` | Production source and source placement guide | Guide only. |
| `src/core/` | VBA calculations and pure validation | Reserved. |
| `src/modules/` | Public facade and supported entry points | Reserved. |
| `src/classes/` | Host-independent record/model classes if required | Reserved. |
| `src/workbook/`, `src/forms/` | Excel adapters, document modules and optional forms | Reserved. |
| `tests/` | Verification guide, harness, synthetic fixtures and expected values | Guide, VBA harness and neutral example suite in `tests/modules/` (#10); not yet run in Excel (#11). |
| `tests/fixtures/`, `tests/expected/` | Inputs and independently justified expected results | One illustrative format example ([TEST_CASES.md](methodology/TEST_CASES.md)); no regulatory case. |
| `tests/derivations/` | Independent Python reference calculations | Reserved. |
| `tests/evidence/` | Deliberately retained, reviewed evidence tied to a source commit | Reserved; evidence contract pending #11. |
| `tools/` | Repository checks, build and evidence tooling | Issue-policy checker and tests, [check_repository.py](../tools/check_repository.py), [actionlint-lock.json](../tools/actionlint-lock.json) and the static VBA checks (`check_vba_*.py`, `vba_lexer.py`) present; see [CI.md](CI.md). |
| `examples/modules/` | Synthetic VBA examples using supported API only | Reserved. |
| `test-results/` | Disposable run output | Ignored by .gitignore. Do not commit disposable run output. |

Create reserved directories with their first useful file, not empty placeholders.
Existing checker unit tests stay beside the checker in tools; numerical and
host verification belong in tests. Keep generated workbooks out of source
control unless a reviewed source template has an explicit path exception under
the [Git hygiene policy](../INSTALLATION.md#git-hygiene-verification) established by #5. Exported source is authoritative; workbook changes must be exported and
reviewed. Form resources, when used, stay beside their form definitions.

## Dependencies

The Excel adapter calls the public facade, which validates the public contract
and delegates calculations to the core. The core may use host-independent
classes. Classes must not call the facade or host, avoiding dependency cycles.

- Core and model classes have no Excel object-model, worksheet, range, UI,
  file/network access or ambient mutable run state.
- Facade procedures contain orchestration and contract validation, not duplicate
  formulas. They return structured results/errors to callers.
- Workbook and form code maps cells/events to facade inputs and renders results;
  it contains no regulatory formulas.
- Tests may exercise core directly; examples use only the supported facade.
- Python is never called by the workbook. Reference derivations must be justified
  from methodology rather than mechanically translating VBA.
- Repository tooling is not a second calculation implementation.

The `vba-dependencies` check enforces these boundaries by name and review
covers what it cannot resolve ([VBA static checks](CI.md#vba-static-checks)).
Host policy and conventions are in [INSTALLATION.md](../INSTALLATION.md) and
[VBA_HOUSE_STYLE.md](VBA_HOUSE_STYLE.md); host validation remains pending #11.

## Public API inventory

[PUBLIC_API.txt](PUBLIC_API.txt) is currently empty of declarations.
A VBA Public declaration is supported only if explicitly inventoried.
Core standard modules use `Option Private Module`; this limits external
visibility and is not a security boundary. Test/example modules are never part
of the production import set.

Each supported declaration is recorded as two tab-separated lines:

```text
<component>	<kind>	<name>
# SIG	<component>	<kind>	<name>	<normalized declaration>
```

Kinds: Function, Sub, Property Get, Property Let, Property Set, Const, Enum or
Type. Normalize signature whitespace to single spaces. Blank lines and ordinary
# comments are ignored; # SIG lines are signature records. Public class members
follow the same inventory convention when classes become supported API.
The `vba-public-api` check verifies the inventory against src/modules/.

A supported API change needs an issue, updated contract and inventory, tests and
a [changelog](../CHANGELOG.md) entry. There are no supported entry points
until these records and implementation are reviewed together.

## Input/output contract conventions

Before the first facade entry point, add its contract under docs/contracts.
Define schema/version identifiers and, for every field: type, unit, currency,
date basis, allowed domain, null/missing treatment and sign convention.
Specify stable record identifiers and relationships for the chosen approach;
do not predeclare a universal netting-set model.

A contract must identify the selected approach and rule-version identifier,
input provenance, valuation/calculation dates, validation failures, result
status, output units and intermediate audit values. Distinguish invalid input,
unsupported scope and numerical failure. Never silently substitute defaults,
coerce missing values to zero, or present partial results as successful capital.

Fixture contracts must trace every expected value to a source or independent
derivation and define absolute/relative tolerances and rounding explicitly.
No numeric tolerance or regulatory parameter is chosen here; #8 owns those
decisions. Evidence must identify source commit, host/tool versions, inputs,
expected and actual outputs, commands and pass/fail status (#11).

## Design reference

The separation of core, facade, host, tests and tooling was informed by
CCR-K-SFTs architecture (source blob
`7f0efeb4295330a7061c661fbada828950fae220`).
Its SFT formulas, collateral rules, regulatory decisions and tested-host claims
are not evidence for this project.
