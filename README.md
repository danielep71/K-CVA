# K-CVA

Regulatory capital for credit valuation adjustment (CVA) risk. K-CVA is
intended to become an Excel/VBA application that calculates the own funds
requirements for CVA risk under the EU Capital Requirements Regulation, from
supplied exposures and hedges.

The repository was named MKT-K-CVA until 2026-10-24; GitHub redirects the
old links.

> [!IMPORTANT]
> **Status: repository setup only.** There is no calculation engine, public
> API, workbook or validated method yet. Nothing here should be used to
> compute capital. The regulatory basis is the EU CRR as amended by CRR3; the
> basic approach (BA-CVA) comes first and the standardised approach (SA-CVA)
> after it, with exposure values and effective maturities supplied by the
> caller ([decisions](docs/DECISIONS.md)). Economic or accounting CVA, an
> exposure simulation engine and a parallel Python product are out of scope.

## What exists today

- **Repository checks** (`python tools/check_repository.py`, also run by CI
  on every pull request): tooling tests, label and issue-form configuration,
  the format of the numerical test-case files, static rules on the exported
  VBA source, and the workflows. They read files only: they compile no VBA
  and check no calculation.
- **A VBA regression harness** with a neutral example suite in
  `tests/modules/`. It exercises the harness itself and contains no CVA
  calculation. It has not yet been compiled or run in Excel (#11).
- **Methodology and test-case documents**: the regulatory basis, a copy of the
  CRR provisions relied on, the BA-CVA inputs, and the format of future test
  cases.

Not available: a CVA calculation, a public API, a workbook or a release. No
figure produced from this repository should be relied on.

## Getting started

1. Clone the repository and switch to the active release branch
   ([obtain the source](INSTALLATION.md#obtain-an-exact-source-revision)).
2. Install Git, Python and Node.js and run `python tools/check_repository.py`
   ([developer setup](INSTALLATION.md#developer-setup)).
3. To try the harness, build a development workbook on the intended Excel host
   and run `TEST_Examples.RunExampleTests`
   ([importing VBA into Excel](INSTALLATION.md#importing-vba-into-excel),
   [running the harness](INSTALLATION.md#running-the-harness)).
4. Before proposing a change, read [CONTRIBUTING.md](CONTRIBUTING.md).

## Documents

| Document | Purpose |
| --- | --- |
| [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md) | Layout, dependency direction, public API boundary, contracts |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Scope, architecture and methodology decisions, open and closed |
| [docs/methodology/README.md](docs/methodology/README.md) | Regulatory basis, approaches, BA-CVA inputs, version applicability, source register, traceability |
| [docs/methodology/sources/README.md](docs/methodology/sources/README.md) | The copy of the CRR provisions relied on, with hashes and terms of use |
| [docs/methodology/TEST_CASES.md](docs/methodology/TEST_CASES.md) | Test-case files, tolerances, reference classes, completeness |
| [docs/VBA_HOUSE_STYLE.md](docs/VBA_HOUSE_STYLE.md) | VBA naming, contracts, errors, cleanup, encoding |
| [INSTALLATION.md](INSTALLATION.md) | Excel host, developer setup and evidence locations, importing and exporting the VBA source, running the harness |
| [tests/README.md](tests/README.md) | Test layout, the VBA harness and its log format |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Reporting a problem with synthetic data; the development workflow; validation rules |
| [docs/GOVERNANCE.md](docs/GOVERNANCE.md) | Branches, integration, review, protection, issues |
| [docs/ISSUE_LABELS.md](docs/ISSUE_LABELS.md) | Issue labels, priorities and triage |
| [docs/CI.md](docs/CI.md), [tools/README.md](tools/README.md) | Repository checks, CI coverage and dependency updates |
| [SECURITY.md](SECURITY.md) | Reporting vulnerabilities privately; synthetic data only |
| [NOTICE.md](NOTICE.md), [LICENSE](LICENSE) | Copyright, provenance and the MPL-2.0 licence |
| [CHANGELOG.md](CHANGELOG.md), [RELEASING.md](RELEASING.md) | What changed, versions and the release procedure |
| [docs/CLOSEOUT.md](docs/CLOSEOUT.md) | The v0.1.0 closeout checklist and evidence index |

Task branches start from `release/0.1.0`, and task pull requests target it.
Nothing has been released: no version, tag or workbook. Changes are recorded
under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md), and a version is
prepared and published only by maintainer decision, as in
[RELEASING.md](RELEASING.md).
