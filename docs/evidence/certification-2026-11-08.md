# v0.1.0 certification verification record

Issue #20; reviewed 2026-11-08. This records the infrastructure checks for
[milestone v0.1.0 - Repo setup](https://github.com/danielep71/K-CVA/milestone/1).
**Certification is pending the closeout PR's required CI, final-head review
and merge. The issue and milestone remain open until those gates pass.**
Nothing here publishes a tag, release or workbook.

## Candidate and reproducibility

- Main candidate: `3d75855e5cbe6cda2f7fd519b6c363710ba9b935`, integration
  [#178](https://github.com/danielep71/K-CVA/pull/178); sync
  [#179](https://github.com/danielep71/K-CVA/pull/179) at
  `f673dfd78f63403e8635c52f21c8cd3060957478` has the identical source tree.
- Fresh independent local clone (`git clone --no-hardlinks` from the available
  repository), detached at the candidate; clean before and after checks.
  This is a fresh checkout, not a new network clone/authentication exercise.
- Python 3.12.14, Node 24.22.1, Git 2.51.1, Linux x64. The declared Python
  packages were available in the environment. `python tools/check_repository.py`
  passed all 24 gates; [unaltered report](integrity-3d75855.json) identifies
  the candidate and `dirty: false`, with file SHA-256 values.
- The repeat cold-cache actionlint download returned HTTP 504. The successful
  local run used the previously downloaded locked archive, whose SHA-256 is
  checked by the tool before extraction. This does not establish current
  cold-network installation availability or excuse a failing hosted gate.
- Main [integrity 42458019525](https://github.com/danielep71/K-CVA/actions/runs/42458019525)
  and [CodeQL 42458019427](https://github.com/danielep71/K-CVA/actions/runs/42458019427)
  are green. Closeout PR checks are separate, mandatory evidence.

## Current controls

[Machine-readable check results](certification-checks-2026-11-08.json) retain
all 20 live label definitions, zero-drift comparison/reconciler agreement,
triage result and current lock's published-wheel hash coverage. Labels were
read from the public REST endpoint; the complete issue export was obtained
through the connected GitHub API (100, 85 and 0 items, including PRs).
All seven open issues pass; all 41 other setup-milestone issues are closed.
Hosted [triage 42470606166, attempt 2](https://github.com/danielep71/K-CVA/actions/runs/42470606166/attempts/2)
also passed after an initial runtime-download failure. These are dated snapshots.

The [authenticated settings report](repository-settings-2026-11-08.json)
was supplied by the maintainer, read at 10:09:13 UTC: no drift and no unread
settings. Manifest SHA-256
`f87de47b180d9726c36f98181313fd29ccfe9b71ff83d9d2aab9226044611020`
matches the candidate; replaying its comparator also returns empty findings.
The report does not record the operator's script commit, so this linkage rests
on manifest identity and independent replay, not an asserted tool SHA.
Five active rulesets have no bypass/exclusion; private reporting, secret
scanning, push protection and Dependabot security updates are enabled.
The complete snapshot, rather than this abbreviated description, is authoritative.

The real enforcement demonstrations remain those of #13, linked in
[GOVERNANCE](../GOVERNANCE.md#protection-policy-and-verified-controls).
Today's read-back corroborates configuration; it is not a repeated destructive
probe of every control. No settings were applied during certification review.

## Acceptance reconciliation

Read every setup issue body and its retained resolution/comments. Each row
below links local evidence, not completion in SFTs or MyTemplate. All 41
prerequisites are closed. Two historical unchecked qualifications are carried
forward explicitly: #116's operator-confirmed secret retirement and #120's
cross-platform wheel coverage without host execution. Neither is silently
promoted to independently observed administrative/host behaviour.

| Issue | Deliverable | Retained evidence and assessment |
| --- | --- | --- |
| [#2](https://github.com/danielep71/K-CVA/issues/2) | Branch governance and review | Task #21, integration #22; later public-policy changes in #108. Current settings snapshot confirms the configured rules. |
| [#3](https://github.com/danielep71/K-CVA/issues/3) | Project boundary and architecture | Task #24, integration #28; decisions A3/A4 and the #8 methodology contract are recorded locally. |
| [#4](https://github.com/danielep71/K-CVA/issues/4) | Licensing and security | Tasks #25/#27, integration #28; MPL imports and source-specific terms remain distinguished in NOTICE. Public settings supersede the historical private snapshot. |
| [#5](https://github.com/danielep71/K-CVA/issues/5) | Source-control conventions | Task #26, integration #28; ignore/trackable probes and current committed-whitespace gate. Host execution is supplied by #11, not inferred from static checks. |
| [#6](https://github.com/danielep71/K-CVA/issues/6) | Universal CI and dependency updates | Task #30, integration #32; current candidate passes all 24 gates. Dependabot configuration exists and authenticated security-update setting is enabled. |
| [#7](https://github.com/danielep71/K-CVA/issues/7) | PR template and issue forms | Task #31, integration #32; current forms/templates pass configuration checks. Historical task-review exception remains historical. |
| [#8](https://github.com/danielep71/K-CVA/issues/8) | Methodology and test-case contract | Tasks #72/#73, integration #74; local decisions and registered source identity retained. This is a contract/provenance deliverable, not formula validation. |
| [#9](https://github.com/danielep71/K-CVA/issues/9) | Static VBA checks | Task #54, integration #55; regression corrections #56/#58/#60/#62/#64/#65 and current fixtures pass. |
| [#10](https://github.com/danielep71/K-CVA/issues/10) | Regression scaffold | Task #76, integration #77; normal, injected and skipped-case contracts, plus the subsequent #11 host evidence. |
| [#11](https://github.com/danielep71/K-CVA/issues/11) | Genuine host evidence | [Retained operator report](excel-run-194e9cd.md), documentation #166, integration #167. See the explicit later-source delta below. |
| [#12](https://github.com/danielep71/K-CVA/issues/12) | Repository protections | Task #51, integration #52; complete authenticated report dated 2026-11-08 supersedes earlier incomplete read-back. |
| [#13](https://github.com/danielep71/K-CVA/issues/13) | Protection enforcement | Tasks #68/#69, integration #70; real failing-check, stale-base and rebase-merge refusals. Other controls are configuration read-back only, as documented in GOVERNANCE. |
| [#14](https://github.com/danielep71/K-CVA/issues/14) | Traffic history | Initial implementation and integrations #103/#106/#111; counts-only scope and App migration #116 supersede the original PAT design. |
| [#15](https://github.com/danielep71/K-CVA/issues/15) | Repository About metadata | Retained metadata read-back; current description identifies regulatory CVA, BA-CVA before SA-CVA, and setup-only status. |
| [#16](https://github.com/danielep71/K-CVA/issues/16) | Onboarding | Task #78, integration #80; current documented prerequisites used for the clean-checkout run below. |
| [#17](https://github.com/danielep71/K-CVA/issues/17) | Versioning and closeout process | Task #82, integration #83; no VERSION/tag/release publication follows from closing setup. |
| [#18](https://github.com/danielep71/K-CVA/issues/18) | File audit | Task #169, integration #170; [per-file audit](v0.1.0-file-audit.md) and final blob reconciliation below. |
| [#19](https://github.com/danielep71/K-CVA/issues/19) | Comment and prose audit | Task #173, integration #174; [prose review](v0.1.0-file-audit.md#prose-and-comment-review-19), with comment-only VBA delta explicitly accepted as supporting evidence. |
| [#35](https://github.com/danielep71/K-CVA/issues/35) | Stale documentation | Task #36, integration #39; obsolete pending statuses reconciled. |
| [#37](https://github.com/danielep71/K-CVA/issues/37) | Whitespace and runtime pins | Task #38, integration #39; committed-tree whitespace checks and consistent runtimes in current workflows. |
| [#41](https://github.com/danielep71/K-CVA/issues/41) | Rendering and chooser wording | Task #42, integration #43; corrected tables/lists and issue chooser. |
| [#47](https://github.com/danielep71/K-CVA/issues/47) | NOTICE source pins | Task #48, integration #49; imported provenance is pinned. |
| [#56](https://github.com/danielep71/K-CVA/issues/56) | Conditional Declare parsing | Regression fixtures for colon-separated conditional declarations; integrated through #55; current tests pass. |
| [#58](https://github.com/danielep71/K-CVA/issues/58) | Unparenthesized object creation | CreateObject/GetObject detection regression fixtures; integrated through #55; current tests pass. |
| [#60](https://github.com/danielep71/K-CVA/issues/60) | Conditional scope isolation | Conditional-block parser regression fixtures; integrated through #55; current tests pass. |
| [#62](https://github.com/danielep71/K-CVA/issues/62) | Dotted jump syntax | Dotted GoTo regression fixtures; integrated through #55; current tests pass. |
| [#64](https://github.com/danielep71/K-CVA/issues/64) | Type/Enum members | Member-scope regression fixtures; integrated through #55; current tests pass. |
| [#65](https://github.com/danielep71/K-CVA/issues/65) | Standalone New dependencies | Filesystem-object construction regression fixtures; integrated through #55; current tests pass. |
| [#85](https://github.com/danielep71/K-CVA/issues/85) | Project rename | Task #86, integration #87; active K-CVA identity, historical upstream names retained where relevant. |
| [#108](https://github.com/danielep71/K-CVA/issues/108) | Public visibility and source terms | Task #109, integrations #111/#113; public visibility, private reporting and secret protection confirmed in supplied settings report. Source terms remain in NOTICE. |
| [#116](https://github.com/danielep71/K-CVA/issues/116) | GitHub App traffic token | Task #140, integration #141; run 41703028266. PAT retirement/TRAFFIC_TOKEN deletion rests on maintainer confirmation dated 2026-11-03 in [the retained resolution](https://github.com/danielep71/K-CVA/issues/116#issuecomment-6613506942), not independent secret enumeration. Shared App installation scope remains an explicit limitation. |
| [#117](https://github.com/danielep71/K-CVA/issues/117) | CodeQL | Task #127, integrations #130/#138; pins #135, alert correction #137. Intentional summary-file access alert disposition retained; VBA/numerical scanning is not claimed. |
| [#118](https://github.com/danielep71/K-CVA/issues/118) | Markdown and external links | Task #126, integration #130; current anchor fixtures pass. Historical external report has two unverified URLs; ongoing availability is not certified. |
| [#119](https://github.com/danielep71/K-CVA/issues/119) | Workflow rules and timeouts | Integrations #130/#144/#147 include the reopened job-permission correction and closeout. Current workflow gates pass. |
| [#120](https://github.com/danielep71/K-CVA/issues/120) | Ruff, mypy and dependency lock | Integration #130 and subsequent reviewed updates. All 338 published wheels for the 11 current pinned packages have hashes in the lock (PyPI metadata checked today). Linux execution only; no Windows/macOS installation claim. |
| [#121](https://github.com/danielep71/K-CVA/issues/121) | Settings as code | Task #129, integration #130; supplied full authenticated check and independently replayed comparator. No live apply exercised. |
| [#122](https://github.com/danielep71/K-CVA/issues/122) | PR milestone guard | Task #128, integration #130; actual clearing exercise run 41243238829, with subsequent pagination/read-back safeguards. |
| [#123](https://github.com/danielep71/K-CVA/issues/123) | Timeless policy wording | Task #129, integration #130; this closeout removes the later procedural heading suffix (#176), retaining issue references in dated evidence. |
| [#158](https://github.com/danielep71/K-CVA/issues/158) | Issue and label management | Task #159, integration #160; schema 3/pruning safeguards and triage contracts. Current live labels and all seven open issues pass. |
| [#162](https://github.com/danielep71/K-CVA/issues/162) | Remaining template baseline | Task #163, integration #164; local tests, metadata/date policy, integrity tooling and pinned dependencies retained. |
| [#176](https://github.com/danielep71/K-CVA/issues/176) | Settings plan/journal/equivalence | Task #177, integration #178, sync #179; 27 settings tests and final-head review. Approved digest, atomic journal and stronger-equivalent coverage verified offline; no live mutation/rollback exercise. |
| [#20](https://github.com/danielep71/K-CVA/issues/20) | Certification | This record and CLOSEOUT; final PR gates and milestone closure remain pending. |

## Excel evidence and subsequent source delta

The [maintainer's genuine Excel run](excel-run-194e9cd.md) is bound to
`194e9cd322b5a86a58bf54e025d931b17cc13276`: Excel 16.0 build 20430,
Office 64-bit, VBA7, Windows 11 Enterprise 25H2 build 26200.9711.
It reports import, compile PASS, normal/injected/skipped logs, export and
validator PASS. The report does not quote each raw RESULT line; none is invented.

Compared both modules through the certification candidate: their executable
statements are unchanged; #19 changed comments/contracts only. Later #176
changes settings tooling, not the scaffold or host recorder's executable
behaviour. This is the reason the earlier run supports infrastructure acceptance
at the later candidate. It is **not** a new import/compile/run or a new export
identity. Original blobs remain those in the operator report. Raw host logs,
exports and host metadata are operator-held, not independently revalidated here;
registry restoration, other builds, 32-bit Office and other hosts are unproven.

## Final file coverage

Enumerated all 93 candidate paths and blobs. The 92 non-report blobs exactly
match the #19 reviewed-blob column with the seven #176 overrides. The audit
report's own externally identified blob is
`cf1b6b6ead4bc5ed36ddc489a13f326c419f2c04`; its prose and coverage were re-read.
No unmatched source file remains. The closeout PR adds evidence and edits
related documentation only; its supplemental rows in the
[file audit](v0.1.0-file-audit.md) identify those reviewed blobs, with self hashes
recorded in the PR. Checks on that PR do not retrospectively alter the candidate.

## Scope and limitations

The proposed acceptance covers repository infrastructure: governance and
configured protections, checks/CI, source conventions, licensing/provenance,
methodology register and test-case contract, the VBA scaffold and onboarding.
It certifies **no CVA formula, regulatory interpretation, numerical result,
public API or workbook**. No runtime engine or production workbook exists here.

Operator-supplied Excel/settings evidence and PAT-retirement confirmation retain
the attribution above. Offline settings tests do not prove live apply/rollback.
Published wheel hashes do not prove Windows/macOS execution. External link
availability, all shared-App installations and every historical code path were
not independently revalidated. Historical review exceptions are not erased by
this record. HTTP download failures must not be treated as passing CI.
