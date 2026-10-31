# Repository governance

This document defines how changes to K-CVA are proposed, reviewed and
integrated. Policy and verified GitHub controls are recorded separately.

## Ownership and scope

Daniele Penza (@danielep71) owns scope, priorities, integration and publication.
Contributors and automation act within the maintainer's authorization and retain
truthful authorship. Bot authorship does not permit bypassing review or rules.

The milestone **v0.1.0 - Repo setup** covers repository infrastructure.
Architecture and the initial CVA product scope are recorded in
[DECISIONS.md](DECISIONS.md); production calculations, numerical certification
and production workbook packaging are outside this milestone. The repository
is public.

## Branches

| Branch | Role |
| --- | --- |
| `main` | Integrated source; receives release integration PRs using merge commits. |
| `release/0.1.0` | Active setup integration branch. |
| Other `release/X.Y.Z` | Created only by maintainer decision, without a v prefix. |
| `docs/<issue>-<slug>`, `fix/<issue>-<slug>`, `chore/<issue>-<slug>`, `test/<issue>-<slug>` | Task branches cut from the active release branch, deleted after merge. |
| `traffic-history` | Data-only branch written by the Traffic history workflow ([TRAFFIC.md](TRAFFIC.md)), created once as an orphan commit. Never a task base or merged into source branches. |

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
to obtain a review. If required review is unavailable, keep the PR open and
record the blocker rather than treating absent review as success.

A sync PR with a verified empty file diff needs only applicable CI, with that
evidence recorded in the PR. A sync PR changing files needs normal final-head
review. `Repository integrity` must pass on the sync head as on other
protected-branch PRs.

## Protection policy and verified controls

Policy for main and release/**: require PRs, resolved conversations, zero
mandatory approvals, no deletion, no force pushes and no bypass. Main accepts
merge commits only; release/** accepts squash or merge. Both require the exact
`Repository integrity` check from GitHub Actions on an up-to-date branch; only
the creation of a release branch is exempt. Tags `v*` cannot be updated,
deleted or force-pushed. `traffic-history` cannot be deleted or force-pushed
and needs no PR. Path-filtered label workflows must not serve as the universal
required check ([CI.md](CI.md#workflow-rules) checks that the required one has
no filter).

These controls, the general and Actions settings and the security features
are declared in [.github/repository-settings.json](../.github/repository-settings.json)
and described in [REPOSITORY_SETTINGS.md](REPOSITORY_SETTINGS.md), which also
says how to check them.

- Change a control by changing that file in a reviewed PR, then apply it with
  `python tools/repository_settings.py --apply` and confirm with `--check`.
- Run `--check` before closing a milestone. Never describe a desired control
  as configured until `--check` has read it back.
- Record applicable checks and explicit gaps in each PR. Absence of a check is
  not a passing check.
- Before closing a setup issue, reconcile affected status tables, decision
  records and dependent issue progress with its delivered evidence and
  remaining work.

<a id="demonstrated-enforcement"></a>

### Demonstrated enforcement

Dated evidence, not a rule: a read-back shows that a rule is configured; this
shows that GitHub enforces it. Recorded on **2026-10-24** for
[#13](https://github.com/danielep71/K-CVA/issues/13).
Each row is a merge GitHub refused on a real pull request into release/0.1.0.
The refusal text is quoted from the API response.

| Rule | Evidence |
| --- | --- |
| A failing required check blocks the merge | Controlled [PR #68](https://github.com/danielep71/K-CVA/pull/68). Head `e05d06e` added `tests/modules/TEST_DefectProbe.bas`, whose `GoTo Missing` names no label. Run [40116817400](https://github.com/danielep71/K-CVA/actions/runs/40116817400) checked test merge `379b3dc`; only `vba-jumps` failed, with `tests/modules/TEST_DefectProbe.bas:8: GoTo target 'Missing' is not a label of procedure Probe`. A squash merge pinned to `e05d06e` was refused: *405 Repository rule violations found. Required status check "Repository integrity" is failing.* Correction `2f56108` removed the probe; run [40116946233](https://github.com/danielep71/K-CVA/actions/runs/40116946233) passed on test merge `46b9ecb`. The probe never reached an integration branch: #68 was squash-merged after the correction, so only the corrected tree landed. |
| A passing check on an old base is not enough | After [#69](https://github.com/danielep71/K-CVA/pull/69) moved release/0.1.0 to `d6014c8`, a squash merge of #68 pinned to `2f56108`, whose passing run predated that base, was refused: *405 Repository rule violations found. Required status check "Repository integrity" is expected.* |
| Rebase merges are refused | A rebase merge of #69 pinned to `19d6308`, with its check passing, was refused: *405 Rebase merges are not allowed on this repository.* The message does not say whether the repository setting or the release ruleset refused it; the #12 read-back records rebase as allowed by the repository and excluded by the ruleset. #69 was then squash-merged. |

**What a pull request run checks.** A `pull_request` run checks out GitHub's
test merge of the head into the current base, not the head alone. Its evidence
artifact is named after that test-merge SHA, and its report records both the
checked commit and the PR head SHA (`PR_HEAD_SHA`). Every gate reads every
tracked file and the workflow has no path filter, so the whole change range is
checked; the up-to-date rule makes the checked tree the tree that merges.
Intermediate commits are not checked one by one; a squash merge lands only the
checked tree.

**Not demonstrated, verified by read-back only:** the resolved-conversation
rule (no unresolved thread was open during the exercise); merge-commit-only on
main; deletion, force-push and tag protections; and the release creation
exemption. A refusal can only be shown by attempting the merge; an untriggered
rule is recorded as verified, not enforced. Workflow logs and the 30-day
artifacts expire, so the decisive lines are copied here and into #13.

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
  milestone; link them to relevant issues and preceding PRs. The *Pull request
  milestones* workflow clears a milestone set on a pull request, at once and
  in a daily sweep ([CI](CI.md#pull-request-milestones)).

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
Versions, the changelog and the release procedure are defined in
[RELEASING.md](../RELEASING.md) and [CHANGELOG.md](../CHANGELOG.md);
preparing a version and publishing it are separate explicit maintainer
decisions. The milestone closeout follows [CLOSEOUT.md](CLOSEOUT.md).

Do not commit credentials or confidential client data. Security reporting,
licensing and provenance are documented in [SECURITY.md](../SECURITY.md) and
[NOTICE.md](../NOTICE.md), which also records this document's provenance.
The project is licensed under MPL-2.0 ([LICENSE](../LICENSE)); security
features are recorded with their verification limits.
