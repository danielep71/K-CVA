# MKT-K-CVA

Regulatory credit valuation adjustment (CVA) capital — repository setup.

**Status:** no calculation engine, supported public API, workbook or validated
CVA method is available. Milestone **v0.1.0 - Repo setup** establishes governance,
architecture, tooling and validation conventions. It does not deliver production
calculations or numerical certification.

The intended product is an Excel/VBA application with a calculation core that
does not access Excel. Python is used for repository tooling and independent
reference testing, not as a runtime calculation dependency.

The initial scope is regulatory CVA capital. Economic/accounting CVA valuation,
a general exposure simulation engine and a parallel Python product are outside
the initial scope. The regulatory basis is the EU CRR as amended by CRR3; the
basic approach (BA-CVA) comes first and the standardised approach (SA-CVA)
after it. See the [methodology](docs/methodology/README.md); nothing is
implemented yet.

## Project guides

- [Developer setup and import/export](INSTALLATION.md)
- [VBA house style](docs/VBA_HOUSE_STYLE.md)
- [Repository structure and contracts](docs/REPOSITORY_STRUCTURE.md)
- [Scope and architecture decisions](docs/DECISIONS.md)
- [Methodology work](docs/methodology/README.md)
- [Governance and review](docs/GOVERNANCE.md)
- [Issue labels and triage](docs/ISSUE_LABELS.md)

Task branches start from `release/0.1.0`; task PRs target that branch.
Milestones belong to issues only. See [LICENSE](LICENSE), [licensing and provenance](NOTICE.md) and
[private security reporting](SECURITY.md).

Portable infrastructure validation: `python tools/check_repository.py`.
See [CI and dependency updates](docs/CI.md) for prerequisites, coverage and evidence.
