# Repository governance

This document defines how changes to MKT-K-CVA are proposed, reviewed and
integrated. Policy and verified GitHub controls are recorded separately.

## Ownership and scope

Daniele Penza (@danielep71) owns scope, priorities, integration and publication.
Contributors and automation act within the maintainer's authorization and retain
truthful authorship. Bot authorship does not permit bypassing review or rules.

The milestone **v0.1.0 - Repo setup** covers repository infrastructure.
Architecture and CVA scope are decided in [#3](https://github.com/danielep71/MKT-K-CVA/issues/3);
production calculations, numerical certification and production workbook packaging
are outside this milestone. Keep the repository private.

## Branches

| Branch | Role |
| --- | --- |
| `main` | Integrated source; receives release integration PRs using merge commits. |
| `release/0.1.0` | Active setup integration branch; created on 2026-10-24 from main at `f738d54e61535d63cf3f625303dae7611f434cf0`, by maintainer decision in #2. |
| Other `release/X.Y.Z` | Created only by maintainer decision, without a v prefix. |
| `docs/<issue>-<slug>`, `fix/<issue>-<slug>`, `chore/<issue>-<slug>`, `test/<issue>-<slug>` | Task branches cut from the active release branch, deleted after merge. |
| `traffic-history` | Reserved for data-only automation under #14; not yet created. Never a task base or merged into source branches. |

A release branch does not imply publication.

## Integration and synchronization

1. Create task branches from the active release branch. Task PRs target that
   branch, link their issue and describe validation and limitations.
2. Review the final head and resolve findings. Squash-merge task PRs after their
   applicable checks pass. End the squash subject with the PR number and include
   the issue reference in its body.
3. Integrate release into main through a PR using a merge commit, after
   maintainer approval. Task PRs do not target main.
4. Once checks on the integration commit pass, open a main-to-release sync PR
   and merge it using a merge commit. Record whether its file diff is empty.
5. Do not merge task PRs into release between integration and sync. If a task
   accidentally enters this window, cut a recovery branch from release, merge
   main into it and use a merge PR back into release. Verify its diff is empty
   before applying the sync review exception. Do not relax protection.
6. If main receives unrelated commits while release has unique commits, stop
   integration and record the maintainer's recovery decision.

Protected branches change through PRs, never direct pushes or GitHub's Update
branch action against main or release. Do not rebase, amend or force-push shared
history. Correct it with new commits.

## Review of the final head

Zero required GitHub approvals accommodates the sole owner, who cannot approve
their own PR. It does not waive review. Record maintainer review of the final
diff and full head SHA, plus the checks that actually ran.

For human-authored PRs, use Codex review when available. After any later push,
wait for any earlier review to finish, request `@codex review` in a new top-level
comment and verify completion for the new head. Fix or explicitly answer every
finding and resolve applicable conversations. Older reviews do not cover a new
head. Do not claim Codex coverage when it was skipped.

Bot-authored PRs require maintainer final-head review; do not change authorship
to obtain a review. Codex review availability in this repository is not yet
verified. If required review is unavailable, keep the PR open and record the
blocker rather than treating absent review as success.

A sync PR with a verified empty file diff needs only applicable CI, with that
evidence recorded in the PR. A sync PR changing files needs normal final-head
review. Once #6 and #12 enable it, `Repository integrity` must pass on the sync
head as on other protected-branch PRs.

## Protection policy and verified controls

Intended policy for main and release/**: require PRs, resolved conversations,
zero mandatory approvals, no deletion, no force pushes and no bypass.
Require the exact `Repository integrity` check and up-to-date branches after
#6 supplies an unfiltered workflow and #12 configures enforcement. Path-filtered
label workflows must not serve as the universal required check.

Snapshot verified on **2026-10-24** through GitHub API reads and the settings
evidence recorded in [#12](https://github.com/danielep71/MKT-K-CVA/issues/12):

| Control | Configured or pending |
| --- | --- |
| Visibility and default branch | Private; main. |
| Main ruleset 25781886 | Active; PR required, 0 approvals, resolved conversations, deletion and force pushes blocked; merge commits only; no bypass. |
| Release ruleset 25781928 | Active for release/**; same protections, squash or merge allowed, no linear-history rule and no bypass. |
| Release deletion ruleset 25781993 | Active for release/**; deletion blocked, no bypass. |
| Tag ruleset 25781957 | Active for v*; updates, deletion and force pushes blocked, no bypass. |
| Traffic ruleset 25782014 | Active for traffic-history; deletion and force pushes blocked; regular automation updates allowed, no PR requirement or bypass. Branch and workflow pending #14. |
| Required check and strict up-to-date rule | **Pending #6 and #12**. Neither main nor release currently requires status checks. Preserve the release-branch creation exception when configuring the check. |
| Enforcement demonstration | Pending controlled failing/passing PR exercise #13. Configured controls alone do not prove enforcement. |
| General settings | Projects off; update-branch suggestion and automatic head-branch deletion on. Repository supports merge, squash and rebase, restricted by the branch rules above. |
| Actions | Full-SHA action pinning required; default token reads contents/packages; workflow PR creation/approval off. |
| Security | Dependency graph and Dependabot alerts enabled. Licensing, provenance and security policy pending #4; dependency-update configuration pending #6. |
| Label automation and forms | Installed by #1. Label validation/drift fixtures are path-filtered; live reconciliation is on main. Issue triage is read-only. PR template pending #7. |
| Codex review | Availability not yet verified here; SFTs review results are not evidence for this repository. |

Until the universal check exists, record applicable checks and explicit gaps in
each PR. Absence of a check is not a passing check. Update this dated snapshot
when a control changes; do not describe desired controls as configured.

## Issues, dependencies and closure

[ISSUE_LABELS.md](ISSUE_LABELS.md) defines the canonical catalogue, priority
criteria, dependency syntax and audit commands. These rules apply to every issue:

- Assign to `danielep71`, choose a milestone and exactly one priority.
- Reserve P1 for confirmed calculation defects producing wrong results for
  valid inputs, together with `bug`. Setup work is P3.
- Use `blocked` only for named unresolved prerequisites. Ready issues have no
  status label. After closing a prerequisite, review its dependants and remove
  `blocked` only when all prerequisites are resolved.
- Give milestones to issues only. Task, integration, sync and bot PRs have no
  milestone; link them to relevant issues and preceding PRs.

Issue forms cannot enforce all metadata. The read-only Issue triage workflow
reports violations; the maintainer corrects them and verifies the next run.

Close as completed only after acceptance criteria are supported by linked
evidence. Add a Resolution section linking PRs and commits, actual check results,
unvalidated aspects and accepted limitations. A task merged into the active
release branch may close once its criteria are met; record that main integration
is still pending. Keep any dependent issue blocked if its own prerequisite needs
the change on main. Explain duplicate/not-planned closures explicitly.

## Publication, security and provenance

Milestone closure or integration into main does not publish a release.
Versioning and release preparation belong to #17; tags and releases require an
explicit maintainer decision.

Do not commit credentials or confidential client data. Security reporting,
licensing and the provenance register are decisions for #4; no SFTs license,
security feature or technical stack is implicitly adopted.

This policy was written for MKT-K-CVA using the process in
[CCR-K-SFTs governance](https://github.com/danielep71/CCR-K-SFTs/blob/c13e1167e779ab1816db9d8c81e140abddbf6c66/docs/GOVERNANCE.md)
as a design reference (source blob `bab2ca28c0e48cda98a58698003bbad65de1c9e4`).
Its configured controls and domain-specific decisions were not copied as facts.
