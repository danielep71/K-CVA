# Contributing to K-CVA

K-CVA has one maintainer, who decides scope, priorities and what is
integrated ([docs/GOVERNANCE.md](docs/GOVERNANCE.md#ownership-and-scope)).
The repository is public (verified on 2026-10-28). Every change starts from
an issue and arrives through a pull request.

The repository is in **setup**: there is no calculation engine, workbook or
validated method yet ([README.md](README.md)). Contributions today are to the
setup itself: tooling, tests, documentation and governance.

Never disclose a suspected vulnerability in an issue or pull request; follow
[SECURITY.md](SECURITY.md).

<a id="reporting-a-problem"></a>

## Reporting a problem

Open an issue with one of the forms; blank issues are disabled.

| Form | Use it for |
| --- | --- |
| **Bug report** | Something that behaves differently from its documentation. Give the full commit SHA, the environment (for Excel: build, bitness, Windows version), the steps, and the expected and observed behaviour. |
| **Enhancement** | New or changed behaviour. Define the observable contract, the non-goals and how it will be validated; a calculation change cites the CRR provision it implements ([methodology](docs/methodology/README.md)). |
| **Documentation** | A wrong, stale or missing statement. Name the document that is authoritative for it. |

**Synthetic data only.** Never attach or paste real counterparties,
portfolios, exposures, ratings, market data or client data, and never
credentials, tokens or internal paths. Reproduce the problem with invented
values; a minimal example is better than a real file. A workbook can hold
data outside its visible cells, so attach none: describe the steps or the
exported source instead. If confidential data has been posted, tell the
maintainer at once rather than editing it out quietly; the
[data rules](SECURITY.md#data-and-credentials) apply.

Each issue gets the assignee, exactly one priority and a milestone at triage
([docs/GOVERNANCE.md](docs/GOVERNANCE.md#issues-dependencies-and-closure),
[docs/ISSUE_LABELS.md](docs/ISSUE_LABELS.md)).

<a id="development-workflow"></a>

## Development workflow

1. **Set up** once, as in [developer setup](INSTALLATION.md#developer-setup).
2. **Branch** from the active release branch, `release/0.1.0`
   ([branches](docs/GOVERNANCE.md#branches)), never from `main`. Name the
   branch `fix/<issue>-<slug>`, `docs/<issue>-<slug>`, `test/<issue>-<slug>`
   or `chore/<issue>-<slug>`.
3. **Change** as little as the issue needs: no unrelated formatting, generated
   output or opportunistic refactoring. Update the documentation the change
   affects in the same pull request, add a material change under
   `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md#maintenance-policy), and
   record anything adapted from another repository in
   [NOTICE.md](NOTICE.md).
4. **Check** with `python tools/check_repository.py` before every push; every
   check must pass. Stage new files first, so that they are checked
   ([CI](docs/CI.md)).
5. **Open a pull request** against `release/0.1.0` with the
   [template](.github/pull_request_template.md). Reference the issue with
   `Refs #<issue>`; give the pull request no milestone.
6. **Review.** Codex reviews the pull request when it opens; after a later
   push, request `@codex review` again. Every finding is fixed or answered,
   and the review covers the final head commit
   ([review](docs/GOVERNANCE.md#review-of-the-final-head)).
7. **Merge.** The pull request is squash-merged once `Repository integrity`
   passes on its current head and the branch is up to date. Integration into
   `main` and the sync back are separate steps, taken with the maintainer's
   approval ([integration](docs/GOVERNANCE.md#integration-and-synchronization)).

Never rebase, amend or force-push a commit that has been pushed; correct it
with a new commit.

### Commit messages

A subject line in the conventional form (`docs: ...`, `fix: ...`,
`test: ...`, `chore: ...`), then a body that states:

- **what** changed and **why**;
- **what was validated** at that commit, with the commands run and their
  results; and
- **what was not validated**, separating static checks from Excel runs.

Reference the issue. Do not put credentials, private links or claims that
were not checked in a commit message.

<a id="source-and-validation"></a>

## Source and validation

- **Exported VBA is the source.** The `.bas`, `.cls` and `.frm` files are the
  reviewable record; a workbook never is, and none is committed. Import and
  export as in [INSTALLATION.md](INSTALLATION.md#importing-vba-into-excel);
  write as in [docs/VBA_HOUSE_STYLE.md](docs/VBA_HOUSE_STYLE.md); place
  components as in [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md).
- **A static pass is not Excel evidence.** `tools/check_repository.py` and CI
  read files; they do not compile VBA or run Excel
  ([three different checks](docs/CI.md#vba-static-checks)). A pull request
  that changes VBA states whether it was compiled and run in Excel, on which
  host and at which commit, and never implies it was when it was not. No VBA
  has been compiled or run yet (#11).
- **A skipped or incomplete run is not a pass**, whether a check fails to run
  or the harness reports `completeness=INCOMPLETE`
  ([tests/README.md](tests/README.md#vba-harness)).
- **Expected values never come from the code under test.** They come from a
  published example, a registered external implementation, or a separate
  derivation, as the
  [reference classes](docs/methodology/TEST_CASES.md#reference-classes)
  define.
- **Every calculation rule cites its source.** A rule cites a registered CRR
  article and paragraph before code depends on it
  ([traceability](docs/methodology/README.md#traceability)).

<a id="where-rules-live"></a>

## Where the rules live

| Need | Document |
| --- | --- |
| Scope, layout, dependency direction, public API | [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md), [docs/DECISIONS.md](docs/DECISIONS.md) |
| Regulatory basis, sources and test cases | [docs/methodology/README.md](docs/methodology/README.md), [docs/methodology/TEST_CASES.md](docs/methodology/TEST_CASES.md) |
| VBA naming, contracts, errors, cleanup, encoding | [docs/VBA_HOUSE_STYLE.md](docs/VBA_HOUSE_STYLE.md) |
| Setup, Excel host, import and export, the harness | [INSTALLATION.md](INSTALLATION.md) |
| Test layout and the harness log | [tests/README.md](tests/README.md) |
| Checks and CI | [docs/CI.md](docs/CI.md), [tools/README.md](tools/README.md) |
| Branches, review, protection, issues | [docs/GOVERNANCE.md](docs/GOVERNANCE.md), [docs/ISSUE_LABELS.md](docs/ISSUE_LABELS.md) |
| Pull request checklist | [.github/pull_request_template.md](.github/pull_request_template.md) |
| Vulnerabilities and data | [SECURITY.md](SECURITY.md) |
| Versions, changelog and releases | [CHANGELOG.md](CHANGELOG.md), [RELEASING.md](RELEASING.md); nothing is published |
| The v0.1.0 closeout | [docs/CLOSEOUT.md](docs/CLOSEOUT.md) |

## Licensing

The repository is covered by the [Mozilla Public License 2.0](LICENSE)
([NOTICE.md](NOTICE.md)). Contributions are accepted under the same licence.
Submit only what you have the right to submit: code, tests, data, text and
generated material alike. A file adapted from another repository, and a copy
of a regulatory text, is recorded in [NOTICE.md](NOTICE.md) in the same
change.
