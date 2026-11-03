# Issue labels and triage

The label catalogue and automation are aligned with `danielep71/CCR-K-SFTs` (source commit `3b7aaf09ae16d9ca60ad7b4dedd6ee9461c451af`). `.github/labels.json` is the canonical catalogue of 20 labels; `.github/label-policy.json` selects the application profile without domain overlays.

For branch roles, final-head review, integration and evidence-based closure, see
[GOVERNANCE.md](GOVERNANCE.md). This page owns label and triage semantics.

## Issues

- Assign issues to `danielep71` and select a milestone during triage.
- Assign exactly one priority: P1 only for confirmed calculation bugs producing wrong results for valid inputs; P2 for material correctness, robustness or maintainability defects; P3 for non-blocking improvements.
- P1 also requires `bug`. The automated check verifies that pairing; maintainers verify the calculation evidence.
- Include a `Dependencies and blocking status` section. Write `None` when there are no prerequisites, reference prerequisite issues with `#number`, or use a line beginning `External condition:`.
- When a prerequisite closes, review dependent issues and remove `blocked` once all prerequisites are resolved.
- Apply `blocked` exactly while a named prerequisite issue is open or an external condition remains unresolved. Pull requests are references, not prerequisite issues.
- Use only catalogue labels. Close issues when acceptance criteria and validation evidence are complete.
- Assign milestones to issues only; link pull requests to the issues they implement. A milestone set on a pull request is cleared automatically ([CI](CI.md#pull-request-milestones)).

## Automation

- **Sync issue labels** validates pull requests and reconciles live names, colours, descriptions and count on relevant pushes to main or manual dispatch. Labels outside the catalogue are pruned. It verifies an exact match after reconciliation.
- **Detect issue-label drift** checks daily at 05:17 UTC or on manual dispatch, using read-only permissions. Pull requests run deterministic fixtures. Reports are retained for 30 days.
- **Issue triage** audits open issues on issue changes or manual dispatch. It reports findings without editing issues.

## Local verification

```sh
node .github/scripts/labels-sync.mjs --policy .github/label-policy.json --self-test
node .github/scripts/labels-sync.mjs --policy .github/label-policy.json --mode validate
node .github/scripts/labels-drift.mjs --policy .github/label-policy.json --self-test
python tools/check_issues.py --check-config
python -m unittest discover -s tools -p 'test_check_issues.py'
```
