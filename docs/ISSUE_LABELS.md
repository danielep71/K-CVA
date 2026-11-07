# 🏷️ Issue labels & automation

![Labels](https://img.shields.io/badge/labels-20-1D76DB)

This repository defines 20 issue labels, each with a name, description, and colour. `.github/labels.json` is authoritative; edit it through a pull request. Its catalogue has a `core` list and optional `overlays`: named label sets that `selected_overlays` enables. Synchronization and drift detection resolve the core plus the selected overlays; every name is unique across the core and every overlay, and an unknown or duplicated selection is a validation error. In this repository the overlays are empty and none is selected, so the resolved catalogue is the core. `prune: true` deletes live labels outside the catalogue, but only unused ones. Before it changes anything, synchronization checks every label it would delete against all issues and pull requests, open and closed. It stops if one still carries the label. A name that contains a comma cannot be passed to the API's label filter, so for that name it reads the labels of every issue and pull request, up to 10,000, and stops if a response is malformed or the limit is reached. Remove a label that is still used from its issues and pull requests, or add it to the catalogue, then rerun. A dry run, `node .github/scripts/labels-sync.mjs --mode reconcile --dry-run`, changes nothing and makes no such check: it previews the plan, including the deletion of a label still in use. `tools/test_labels_sync.py` runs both against a local fake API.

## ⚙️ Automation

| Workflow | Purpose |
| --- | --- |
| Sync issue labels | Validates pull requests; reconciles labels after a catalogue change lands on the default branch or a manual run on the default branch. Refuses to delete a label in use. Verifies the exact live result. |
| Detect issue-label drift | Checks daily at 05:17 UTC and manually; PR runs use offline fixtures. Reports drift without modifying labels. Each report is cross-checked against the reconciler's plan on the same snapshot: the script writes the live labels it read to a temporary file, runs `labels-sync.mjs --mode plan` on it, and fails (status `fail`) if the two plans differ; the evidence then carries both plans under `cross_check`. |
| Issue triage | Audits open issues on issue and milestone events or manual runs. Reports a missing assignee, open milestone, target end date or dependency section; not exactly one priority, or `P1` without `bug`; a target end date not before the milestone's due date; a dependency naming an issue that does not exist; invalid labels; and inconsistent blocked status. |
| Pull request milestones | Removes any milestone set on a pull request when the pull request is opened, reopened, edited, or given a milestone, and in a daily and manual scan of every pull request. It reads each pull request again after the change and fails if the milestone is still set; its job summary lists each pull request and the milestone removed. If GitHub gives a pull-request run a read-only token, the run warns instead of failing, and the next daily or manual scan removes the milestone. It never checks out pull-request code. |
| Dependabot (`.github/dependabot.yml`) | Opens weekly pull requests (CodeQL actions are grouped) for the SHA-pinned GitHub Actions, the hash-locked Python tooling, labelled `ci` and `P3` and assigned to me. Nothing merges automatically. |

PR validation and triage are read-only. The reconciler has `issues: write` and
`pull-requests: read`, so pruning sees labels carried only by PRs. The milestone
workflow has `pull-requests: write` and `issues: read`. The workflow write-scope
allowlist is checked by `tools/check_workflows.py`; all actions are pinned.

## Configuration

The four issue forms and Dependabot assign `danielep71`. Triage reads the
required assignee from `bug.yml` and checks that the other forms agree.
The resolved catalogue is the core plus `selected_overlays`; the former
separate profile policy is no longer used. Keep names, descriptions and colours
in this guide consistent with `.github/labels.json`.

## 🧭 Using the labels

Every issue has exactly one priority and the type labels that fit the work. Pull requests carry the labels of the work they deliver; milestones belong to issues only, and *Pull request milestones* removes any milestone set on a pull request.

Pull requests opened by Dependabot or another bot carry the labels of the work and no milestone. During triage, link each one to an existing issue or a new tracking issue, and give that issue the milestone. Before merging one, record my review of its final diff as [GOVERNANCE.md](GOVERNANCE.md#review-of-the-final-head) describes.

### Priorities

| Label | Use |
| --- | --- |
| `P1` | Reserved for a confirmed calculation bug: wrong results for valid inputs. Only together with `bug`; never for setup, documentation, or tooling work. |
| `P2` | Material correctness, robustness, or maintainability defect. Default of the bug and private security contact forms. |
| `P3` | Non-blocking quality, testing, documentation, setup, or technical-debt work. Default of the enhancement and documentation forms and of Dependabot pull requests. |

A form sets the default priority; the maintainer confirms or changes it during triage. Raise a bug to `P1` only once the calculation defect is confirmed.

Every open issue also needs a target end date: an ISO `YYYY-MM-DD` calendar date (Europe/Rome) earlier than the due date of its milestone. The bug, enhancement, and documentation forms ask for it in the *Target end date* field. On other issues, including private security contacts, add it during triage as a line in the issue body:

```text
- Target end date: YYYY-MM-DD (Europe/Rome)
```

When both are present, that line takes precedence over the form field, so edit the line to reschedule. Triage reports a missing or invalid date (`target-date`), and a milestone without a due date or a target end date on or after it (`milestone-due`).

### Start dates and historical records

Record `- Start date: YYYY-MM-DD (Europe/Rome)` at triage, alongside the target
end date. For remaining work, distinguish the planned window from earlier work
already delivered. Keep prerequisites explicit; a date does not clear `blocked`.
The current checker validates target end dates, not start dates or the temporal
ordering of dependencies.

Preserve an original target when it is known. For closed issues without a
historical plan, record the creation date as a tracking proxy and completion
separately; label a reconstructed target explicitly as retrospective. Do not
use that reconstruction to claim on-time delivery. Closed issues are excluded
from automated triage and need evidence-based maintenance review.

### Types

| Label | Use |
| --- | --- |
| `bug` | A confirmed defect. The bug form sets it. |
| `enhancement` | New capability or improvement. The enhancement form sets it. |
| `documentation` | Documentation work. The documentation form sets it. |
| `behavior-change` | Add to work that changes externally observable behavior, such as computed results or input and output layouts. |
| `refactor` | Restructuring that preserves supported behavior. If supported behavior changes, use `behavior-change` instead. |
| `tests` | Regression coverage, test harnesses, fixtures, or manual validation. |
| `ci` | Workflows, automated checks, and dependency updates, including every Dependabot pull request. Release certification belongs to `release`. |
| `repository` | Repository structure, governance, metadata, or tooling. |
| `release` | Release preparation, certification, evidence, packaging, or publication. |
| `security` | Hardening and supply-chain work, and private security contact requests, which never contain vulnerability details. Never for an undisclosed vulnerability: report it as `SECURITY.md` describes. |

### Status and triage

| Label | Use |
| --- | --- |
| `blocked` | A prerequisite named in the [dependency section](#dependency-section), as an issue link or an `External condition:` line, is unresolved. Remove it once all are resolved; ready issues carry no status label. In the same edit, delete the `External condition:` line of each resolved condition, or replace the section with "None" if nothing else is named: **Issue triage** treats every such line as unresolved. |
| `question` | I need information or a decision before the work can proceed. |
| `help wanted` | I welcome outside investigation, implementation, validation, or review. |
| `good first issue` | Well-scoped task suitable for a first contribution. |
| `duplicate` | Close the issue and link the issue or pull request that already covers the work. |
| `invalid` | Close the issue: it is incomplete, unsupported, or not actionable as submitted. |
| `wontfix` | Close the issue: I have decided not to do this work. |

### Dependency section

**Issue triage** reads the section under the first level-2 or level-3 heading whose text contains "Dependencies", up to the next level-2 or level-3 heading. In it:

- name a prerequisite issue as `#12` or by its URL in this repository; it blocks the work while it is open;
- write an external blocker on a line that starts with `External condition:`, in any letter case, optionally after a `-` or `*` list bullet, followed by what you are waiting for; it counts as unresolved until you delete the line;
- a pull request named there is a known reference, never a prerequisite: to wait for one, name the issue it resolves;
- write `None` when nothing blocks the work.

A blocked issue, for example:

```markdown
## Dependencies and blocking status

- #12, which defines the input layout
- External condition: waiting for access to an Excel host
- Related: #34, the pull request that started this work
```

## ✅ Closing issues

Close an issue as completed only when linked evidence meets its acceptance criteria, and check an acceptance box only when that evidence demonstrates it. When the issue is closed, add a **Resolution** section to its body with:

- links to the change (pull request and commit);
- the checks actually run, with their results;
- what was not validated, and any accepted limitation.

Close for another reason (duplicate, not planned, or superseded) only with an explicit explanation; the `duplicate`, `invalid`, and `wontfix` rows above say which label applies. Record material scope or policy decisions in the issue, pull request, or commit description.

## 🎨 Catalogue

The table below lists the descriptions defined in `.github/labels.json`, which synchronization uses as its source of truth: the `core` list plus every selected overlay.

| Label | Colour | Description |
| --- | --- | --- |
| `behavior-change` | `#C24E00` | Intentional externally observable behavior change |
| `blocked` | `#B60205` | Cannot proceed until a named dependency is complete |
| `bug` | `#D73A4A` | Confirmed defect in behavior, correctness, error handling, or a documented contract |
| `ci` | `#24292F` | Automated quality checks, workflow maintenance, or dependency updates |
| `documentation` | `#0075CA` | Documentation for users or for my repository maintenance |
| `duplicate` | `#CFD3D7` | An existing issue or pull request already covers this work |
| `enhancement` | `#A2EEEF` | New capability or meaningful improvement to supported behavior |
| `good first issue` | `#7057FF` | Well-scoped task suitable for a first contribution |
| `help wanted` | `#008672` | I welcome external investigation, implementation, validation, or review |
| `invalid` | `#E4E669` | Report is incomplete, unsupported, or not actionable as submitted |
| `P1` | `#B60205` | Confirmed calculation bug: wrong results for valid inputs (reserved for this case) |
| `P2` | `#D93F0B` | Material correctness, robustness, or maintainability defect |
| `P3` | `#FBCA04` | Non-blocking quality, testing, documentation, setup or technical-debt work |
| `question` | `#D876E3` | I need further information or need to make a decision |
| `refactor` | `#6F42C1` | Internal restructuring intended to preserve supported behavior |
| `release` | `#B60276` | Release preparation, certification, evidence, packaging, or publication |
| `repository` | `#1D76DB` | Repository structure, governance, metadata, tooling, or maintenance |
| `security` | `#8B0000` | Security boundary, vulnerability handling, supply chain, or hardening |
| `tests` | `#006B75` | Regression coverage, test harnesses, fixtures, or manual validation |
| `wontfix` | `#6E7781` | I have decided not to implement or continue this work |

## Local issue audit

The audit needs Python 3.11+ and Node.js, because it validates the catalogue with the synchronization script. To audit the live issues with your GitHub CLI login:

```sh
GITHUB_TOKEN="$(gh auth token)" python tools/check_issues.py --repository OWNER/REPOSITORY
```

To audit an export instead, pass a JSON array of issues and pull requests, open and closed, in GitHub REST format, and name the repository explicitly so dependency URLs resolve:

```sh
python tools/check_issues.py --input issues.json --repo-name OWNER/REPOSITORY
```

Triage accepts only the labels that `.github/labels.json` resolves: the core plus the selected overlays.
