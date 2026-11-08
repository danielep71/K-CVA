# v0.1.0 closeout

The checklist and evidence index for closing the milestone
[v0.1.0 - Repo setup](https://github.com/danielep71/K-CVA/milestone/1).
Prepared by #17; audits by #18/#19; verification record assembled by #20
on 2026-11-08. Final closeout is pending the certification PR gates.
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
| 1 | Completed setup prerequisites, including #11 | Each issue's own prerequisites | Their deliverables, merged and integrated into `main` |
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
| 1 | Every milestone issue and acceptance box verified against retained evidence; no source-repository completion counted as local completion | [Evidence index](#evidence-index) | ☑ |
| 2 | Documented setup reproduced from a fresh checkout with the declared prerequisites, and the accepted commit recorded | [Candidate record](#candidate-record) | ☑ |
| 3 | Hosted `Repository integrity` green on the candidate | [Main CI](evidence/certification-2026-11-08.md#candidate-and-reproducibility) | ☑ |
| 4 | Live labels agree with the catalogue; issue metadata and dependencies pass triage | [Live snapshot and hosted triage](evidence/certification-2026-11-08.md#current-controls) | ☑ |
| 5 | Protection behaviour as recorded in [GOVERNANCE.md](GOVERNANCE.md#protection-policy-and-verified-controls), re-read on the certification date | [Authenticated report](evidence/repository-settings-2026-11-08.json) | ☑ |
| 6 | Genuine scaffold execution in Excel on the intended host, at the candidate or with the reason a later change does not affect it | [Host evidence and delta](evidence/certification-2026-11-08.md#excel-evidence-and-subsequent-source-delta) | ☑ |
| 7 | File and comment audits cover every tracked file at the candidate, including changes made after the audits | [File audit record](#file-audit-record) | ☑ |
| 8 | Evidence index and explicit limitations assembled; scope statement recorded | This document | ☑ |
| 9 | Milestone closed only after every prerequisite is complete or a scope change is explicitly agreed; no tag, release or workbook published automatically | Maintainer decision | ☐ |

<a id="candidate-record"></a>

## Candidate record

Original reviewed main candidate: `3d75855e5cbe6cda2f7fd519b6c363710ba9b935`
(integration #178; identical-tree sync #179).

The [verification record](evidence/certification-2026-11-08.md#candidate-and-reproducibility)
records the clean checkout, exact tools, all 24 static gates, hosted candidate
checks, cached actionlint limitation and operator-supplied Excel evidence.
The [static report](evidence/integrity-3d75855.json) retains candidate/file hashes
and `dirty: false`. Final certification is pending the closeout PR's checks,
final-head review, merge and final main integration/SHA record; this is not a publication decision.

<a id="evidence-index"></a>

## Evidence index

The [43-row issue reconciliation](evidence/certification-2026-11-08.md#acceptance-reconciliation)
links every setup-milestone issue and its local evidence. The original 41 prerequisites
are closed; #186 is the subsequent reviewed download-resilience follow-up. Qualifications for #116 and #120, later VBA comment changes, live
settings provenance and unsupported claims remain explicit in that record.
Issue #20 and milestone closure remain pending the final PR gates.

<a id="file-audit-record"></a>

## File audit record

#18 records the [per-file audit](evidence/v0.1.0-file-audit.md) at the commit it reviews;
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

Proposed acceptance, effective only after the certification PR passes its
required CI and final-head review and merges, and the later tooling change
is integrated into main with its final accepted SHA recorded:

> v0.1.0 *Repo setup* is verified at commit
> `3d75855e5cbe6cda2f7fd519b6c363710ba9b935` as repository infrastructure
> only. The retained genuine Excel scaffold run is bound to `194e9cd`, with
> the later comment-only delta explicitly assessed. No CVA calculation,
> regulatory interpretation, numerical result, public API or workbook is
> certified, released or implied. The [attributed evidence and limitations](evidence/certification-2026-11-08.md#scope-and-limitations)
> are part of this statement.

The issue/milestone decision records when the PR gates are satisfied. Closing
this milestone does not authorize tags, releases or workbook publication.
