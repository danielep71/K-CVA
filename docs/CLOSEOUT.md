# v0.1.0 closeout

The checklist and evidence index for closing the milestone
[v0.1.0 - Repo setup](https://github.com/danielep71/MKT-K-CVA/milestone/1).
Prepared by #17 before the file audits; filled in by #18, #19 and #20.
Nothing in this document is complete until its row links the evidence.

> [!IMPORTANT]
> **Infrastructure readiness is not calculation certification.** Closing
> v0.1.0 certifies that the repository's governance, checks, conventions,
> documents and VBA scaffold are in place and reproduce from a fresh
> checkout. It certifies no CVA calculation, regulatory interpretation,
> numerical result or workbook: none exists at v0.1.0. Closing the milestone
> publishes nothing ([RELEASING.md](../RELEASING.md)).

<a id="sequence"></a>

## Sequence

| Step | Issue | Needs | Produces |
| ---: | --- | --- | --- |
| 1 | The remaining setup issues: #11, #14, #15 and #17 | Each issue's own prerequisites | Their deliverables, merged and integrated into `main` |
| 2 | #18, file audit | Step 1 | The [file audit record](#file-audit-record), with relevance, provenance and owner references for every tracked file |
| 3 | #19, comment audit | #18 | The comment columns of the same record |
| 4 | #20, certification | #19 | The [candidate record](#candidate-record), this checklist and the [evidence index](#evidence-index) completed, the [scope statement](#scope-statement) |
| 5 | Release preparation, if the maintainer decides it | #20 | [RELEASING.md](../RELEASING.md) steps 1 to 4; publication is a further decision |

A file changed after an audit row was recorded is audited again before
certification: the record names the blob it reviewed.

<a id="checklist"></a>

## Checklist

The criteria of #20. Each row is ticked only with a link to its evidence.

| # | Criterion | Evidence | Done |
| ---: | --- | --- | :---: |
| 1 | Every milestone issue and acceptance box verified against retained evidence; no source-repository completion counted as local completion | [Evidence index](#evidence-index) | ☐ |
| 2 | Documented setup reproduced from a fresh checkout with the declared prerequisites, and the accepted commit recorded | [Candidate record](#candidate-record) | ☐ |
| 3 | Hosted `Repository integrity` green on the candidate | Run link | ☐ |
| 4 | Live labels agree with the catalogue; issue metadata and dependencies pass triage | *Live label drift* and *Issue triage* run links | ☐ |
| 5 | Protection behaviour as recorded in [GOVERNANCE.md](GOVERNANCE.md#protection-policy-and-verified-controls), re-read on the certification date | Ruleset read-back | ☐ |
| 6 | Genuine scaffold execution in Excel on the intended host, at the candidate or with the reason a later change does not affect it | #11 evidence | ☐ |
| 7 | File and comment audits cover every tracked file at the candidate, including changes made after the audits | [File audit record](#file-audit-record) | ☐ |
| 8 | Evidence index and explicit limitations assembled; scope statement recorded | This document | ☐ |
| 9 | Milestone closed only after every prerequisite is complete or a scope change is explicitly agreed; no tag, release or workbook published automatically | Maintainer decision | ☐ |

<a id="candidate-record"></a>

## Candidate record

Recorded by #20 from the runs themselves:

| Item | Value |
| --- | --- |
| Accepted commit | Full 40-character SHA on `main` |
| Integration pull request | The release-to-main PR whose merge commit it is, and its sync PR |
| Fresh checkout | `git clone`, `git switch --detach <SHA>`, `git status --short` (empty) |
| Static checks | `python tools/check_repository.py`: exit code and one line per check; `report.json` with the SHA and `"dirty": false` |
| Tool versions | Git, Python and Node.js actually used, against the [CI baseline](../INSTALLATION.md#developer-setup) |
| Hosted CI | `Repository integrity` run ID and result on the SHA |
| Excel run | Host, Excel build and bitness, harness `RESULT` line, from #11 |
| Deviations | `none`, or each criterion not met and the decision accepting it |

<a id="evidence-index"></a>

## Evidence index

One row per issue of the milestone. *Evidence* links the issue's Resolution
section, which links its pull requests, integration and checks. *Verified at
candidate* is ticked by #20 once the evidence still holds for the accepted
commit.

| Issue | Subject | Evidence | Verified at candidate |
| --- | --- | --- | :---: |
| #2 | Branch governance and review | Resolution of #2 | ☐ |
| #3 | Project boundary and architecture | Resolution of #3 | ☐ |
| #4 | Licensing, provenance and security | Resolution of #4 | ☐ |
| #5 | Source-control hygiene and conventions | Resolution of #5 | ☐ |
| #6 | Repository CI and dependency updates | Resolution of #6 | ☐ |
| #7 | Pull request template and issue tracking | Resolution of #7 | ☐ |
| #8 | Methodology provenance and test-case contract | Resolution of #8 | ☐ |
| #9 | Static checks and regression fixtures | Resolution of #9 | ☐ |
| #10 | Regression scaffold | Resolution of #10 | ☐ |
| #11 | Candidate-bound evidence and host smoke test | Open | ☐ |
| #12 | Repository settings and protections | Resolution of #12 | ☐ |
| #13 | Failing and passing checks and merge enforcement | Resolution of #13 | ☐ |
| #14 | Traffic history | Open | ☐ |
| #15 | Repository About metadata | Open | ☐ |
| #16 | Onboarding | Resolution of #16 | ☐ |
| #17 | Versioning and closeout documents | Open | ☐ |
| #18 | File audit | Open | ☐ |
| #19 | Comment audit | Open | ☐ |
| #20 | Certification | Open | ☐ |
| #35, #37, #41, #47 | Documentation and CI corrections | Their Resolutions | ☐ |
| #56, #58, #60, #62, #64, #65 | Static-check defects | Their Resolutions | ☐ |

An issue added to the milestone later gets a row here.

<a id="file-audit-record"></a>

## File audit record

#18 creates `docs/evidence/v0.1.0-file-audit.md` at the commit it reviews;
#19 adds its columns there. One row per tracked file, binary files included:

| Column | Content |
| --- | --- |
| Path | As `git ls-files` prints it |
| Blob | The blob SHA reviewed (`git ls-files -s`) |
| Relevance (#18) | Needed for this repository, or removed |
| Provenance (#18) | Written here, or adapted, with its [NOTICE.md](../NOTICE.md) entry |
| Owner and foreign references (#18) | Names, paths and project references found, and whether each is legitimate |
| Comments and prose (#19) | `reviewed`, `not applicable` (no prose or comments) or `limitation` with the reason |
| Findings | Each problem found, or `none` |
| Fix | The pull request that corrected it, or the issue tracking an implementation defect |

The record states the commit it covers and lists the files changed since,
with their re-audit.

<a id="scope-statement"></a>

## Scope statement

Recorded by #20 with the candidate, in these terms unless the evidence
supports less:

> v0.1.0 *Repo setup* is certified at commit `<SHA>` as repository
> infrastructure only: governance and protections, repository checks and CI,
> source conventions, licensing and provenance, the methodology register and
> test-case contract, the VBA regression scaffold and the onboarding
> documents. The scaffold was run in Excel on `<host>`. No CVA calculation,
> regulatory interpretation, numerical result, public API or workbook is
> certified, released or implied. Limitations: `<list>`.
