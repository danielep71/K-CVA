<!-- Keep this focused. Link evidence instead of pasting confidential data. -->

## Problem and change

Describe the trigger, previous behavior and resulting behavior. State what is
in scope for regulatory CVA capital and what remains unsupported.

## Linked issues and tracking

Refs #<!-- issue number -->

- [ ] Linked issues are assigned to @danielep71, have exactly one priority and an issue milestone.
- [ ] P1 is used only for confirmed calculation defects, with the bug label.
- [ ] Named unresolved prerequisites are listed in each issue's dependency section; blocked matches their current state.
- [ ] This PR has **no milestone**. Milestones belong to issues only.

## Validation and limitations

Commands and results:
- <!-- Command; PASS/FAIL; evidence link. Distinguish local from hosted checks. -->

Tested checkout / full commit SHA:
- <!-- Record the SHA in evidence or a final review comment after the last push. -->

For calculation changes: cite the selected methodology/version, synthetic
fixtures, independent expected values and tolerances. For VBA changes: record
Excel build/bitness, import/compile/runtime evidence and operation/cleanup
outcomes. State untested hosts, missing checks and unresolved limitations.
Repository setup checks do not certify CVA calculations or Excel execution.

## Review and integration

- [ ] Final diff and full head SHA reviewed; later pushes require fresh review.
- [ ] Applicable checks passed, findings answered and conversations resolved; link any maintainer-authorized exception.
- [ ] Correct route and merge method selected below.

Route: <!-- Task -> release/0.1.0 (squash); release -> main (merge, owner approval); main -> release (merge, record empty/non-empty file diff). -->
Review/evidence links: <!-- Final-head review, checks and artifact links. -->

Follow [repository governance](https://github.com/danielep71/K-CVA/blob/main/docs/GOVERNANCE.md)
and [issue rules](https://github.com/danielep71/K-CVA/blob/main/docs/ISSUE_LABELS.md).
Report security vulnerabilities through the
[private reporting route](https://github.com/danielep71/K-CVA/blob/main/SECURITY.md),
not in this PR.
