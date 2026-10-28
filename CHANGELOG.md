# Changelog

All notable changes to K-CVA are recorded here, from the user's point of
view. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). It is not a commit
log or a substitute for release evidence. **No version has been released**:
everything below is under `[Unreleased]`.

## Maintenance policy

- Add a material change under `[Unreleased]` in the same pull request as the
  change it describes. A change with nothing for a user to notice (a typo, a
  refactor with no effect) needs no entry.
- Describe the observable result: what exists, what a user or contributor
  can now do, what changed in a contract, and what to do about it.
- Link the issue or pull request that holds the detail.
- Record only evidence that was produced. A static check is not an Excel run:
  say what was and was not run in Excel.
- Until a version is released, edit an existing entry rather than adding one
  that describes a change to an unreleased state: an entry describes what the
  release contains.
- Entries move into a dated section only when a release is prepared
  ([RELEASING.md](RELEASING.md)). A published section is not rewritten; a
  demonstrable error is corrected with a note.

<a id="date-and-version-rules"></a>

### Date and version rules

`python tools/check_repository.py` (gate `changelog`) checks the headings,
dates, order, link references and `VERSION`. What a version number means
(`0.y.z`, patch, minor, major) is checked in review.

| Rule | Standard |
| --- | --- |
| Version | `MAJOR.MINOR.PATCH`, without a leading `v` in headings |
| Release heading | `## [X.Y.Z] - YYYY-MM-DD`, a real calendar date |
| Ordering | `[Unreleased]` first; releases newest to oldest, by version and date |
| Link references | `[Unreleased]` and every release; a release's points to `.../releases/tag/vX.Y.Z` |
| `0.y.z` | Initial development: no compatibility is promised between versions |
| Patch, minor, major | From `1.0.0`: a compatible correction, a compatible capability, an incompatible change to the public contract |

| Category | Use for |
| --- | --- |
| **Added** | New capabilities, files, checks or tests |
| **Changed** | Changes to existing behaviour, contracts, tooling or documentation |
| **Fixed** | Corrected defects |
| **Security** | Safely disclosed security corrections |
| **Validation** | Evidence actually produced |
| **Known limitations** | Deliberate, unresolved boundaries |

Use only the categories an entry needs.

<a id="unreleased"></a>

## [Unreleased]

Planned as 0.1.0, *Repo setup*: repository infrastructure only. It contains no
CVA calculation, public API or workbook.

### Added

- Governance: the branch model, task, integration and sync pull requests,
  review of the final head, rulesets on `main`, `release/**` and `v*` tags
  with the required `Repository integrity` check, and the issue rules
  ([docs/GOVERNANCE.md](docs/GOVERNANCE.md),
  [docs/REPOSITORY_SETTINGS.md](docs/REPOSITORY_SETTINGS.md); #2, #12).
- The project boundary, layout, dependency direction, public API boundary and
  the decision register
  ([docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md),
  [docs/DECISIONS.md](docs/DECISIONS.md); #3).
- Licensing under MPL 2.0, the provenance register and the security policy
  ([NOTICE.md](NOTICE.md), [SECURITY.md](SECURITY.md); #4).
- Source conventions: exported VBA as the source, the VBA house style, the
  intended Windows 64-bit Excel host and the import and export steps
  ([docs/VBA_HOUSE_STYLE.md](docs/VBA_HOUSE_STYLE.md),
  [INSTALLATION.md](INSTALLATION.md); #5).
- `python tools/check_repository.py`, run locally and by the
  `Repository integrity` workflow on every pull request: tooling tests, label
  and issue-form configuration, the test-case format, the changelog, static
  checks of the exported VBA source, the workflows and whitespace; and
  reviewed Dependabot updates of the pinned actions
  ([docs/CI.md](docs/CI.md); #6, #9).
- The issue forms, labels and issue-triage check, and the pull request
  template (PR #1, #7).
- The regulatory basis (the EU CRR as amended by CRR3, BA-CVA first, then
  SA-CVA), a registered copy of the CRR provisions relied on, and the
  test-case file format with its tolerances and reference classes
  ([docs/methodology/](docs/methodology/README.md); #8).
- A VBA regression harness with a neutral example suite in `tests/modules/`,
  the reference cleanup pattern, and a procedure and checker for recording an
  Excel run against its commit
  ([tests/README.md](tests/README.md#vba-harness),
  [INSTALLATION.md](INSTALLATION.md#recording-an-excel-run); #10, #11).
- Onboarding: README, developer setup and contributing guide
  ([CONTRIBUTING.md](CONTRIBUTING.md); #16).
- Repository traffic history (views and clones) kept beyond GitHub's 14
  days, on the data-only `traffic-history` branch
  ([docs/TRAFFIC.md](docs/TRAFFIC.md); #14).
- This changelog, the release procedure and the closeout checklist
  ([RELEASING.md](RELEASING.md), [docs/CLOSEOUT.md](docs/CLOSEOUT.md); #17).

### Validation

- Enforcement of the required check was exercised on `release/**`: a failing
  check and an out-of-date base blocked the merge, and a rebase merge was
  refused ([demonstrated enforcement](docs/GOVERNANCE.md#demonstrated-enforcement);
  #13).

### Known limitations

- No VBA has been imported, compiled or run in Excel; no host is tested
  (#11).
- There is no calculation, public API, workbook or numerical test case other
  than an illustrative format example. Methodology decisions M4 and M6 are
  open, and M5 and M7 in part ([docs/DECISIONS.md](docs/DECISIONS.md)).
- The repository is public. Code scanning is not configured; secret scanning
  and push protection cover GitHub's supported secret patterns only
  ([SECURITY.md](SECURITY.md#current-visibility); #108).

[Unreleased]: https://github.com/danielep71/K-CVA/commits/main
