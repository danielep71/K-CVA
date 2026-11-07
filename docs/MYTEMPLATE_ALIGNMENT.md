# MyTemplate finding reconciliation

Issue #162, reviewed 2026-11-07. Baselines: K-CVA release/0.1.0
`c3366a073e34f13a94dd78077fa16cfc72684429` (same tree as main after #160),
and MyTemplate `f1d0d17ecede525941cfedf07f0cf737bf1346ef`.
The supplied report used older K-CVA `7ffc3631`; it is not current evidence.

## Already resolved

These nine findings are implemented in #159 and integrated by #160/#161.

| Finding | Current evidence |
| --- | --- |
| F05 | Work issue forms require `target_end_date`. |
| F08 | Bug evidence/workaround/recovery and enhancement alternatives are optional fields. |
| L04 | Label reconcile requires the default branch, including manual dispatch; negative fixtures cover it. |
| L05 | `assertSafeDeletions` checks associations before mutation, including closed items and comma names. |
| L10 | Reconcile declares `pull-requests: read`. |
| T02 | Issue triage handles milestone events. |
| T04 | `check_issues.py` requires an open milestone for open issues. |
| T05 | Calendar dates and strict target-before-due comparison are enforced, with planning-line precedence. |
| P06 | PR milestone clearing paginates, reads back after PATCH and declares `issues: read`. |

## Corrections in this change

| Finding | Resolution |
| --- | --- |
| G10 | Add a local code of conduct with prohibited behavior and the established private maintainer contact. |
| C04 | Enable C90/max15 for tooling; one documented exemption for the test-only fake API dispatcher. |
| D03 | Add manual CodeQL dispatch and a separate read-only PR job, no result/database upload, SARIF retained 30 days. |
| S03 | Manifest requires security updates enabled; read the dedicated endpoint, distinguish paused and unread, verify after apply. |
| A05 | Check App client ID and key-presence boolean before minting; never pass the raw key to the preflight. |
| A12 | Track last observation per daily metric, migrate seven-column CSVs, cover A@t1/A@t3/B@t2 replay. |
| C14 | Cancel superseded PR integrity runs only; unique run-ID groups preserve push/manual evidence. |
| D10 | Add conditional good-faith safe harbor limited to maintainer-controlled claims. |
| G13 | Ignore keystores and private SSH filenames, explicitly retain public keys. |
| S14 | Report includes exact manifest SHA256, desired values and mode alongside timestamp/live/drift. |
| S18 | Declare/read/compare all-external-contributor approval; never automatically write this setting. |
| S19 | Declare/read/compare retention 90 days; never automatically write this setting. |
| S26 | Defer automatic branch deletion until security/protection operations succeed; test failure ordering. |

## Evidence limits

The regression suite uses synthetic traffic and a fake GitHub settings API.
It does not apply live settings or rewrite the traffic-history branch.
The UI confirmed enabled security updates and all-external-contributor approval
on 2026-11-07, and retention 90 days. No API verification of the paused flag
is claimed. Historical settings evidence files remain unchanged.
No Excel execution, calculation certification, release publication or main
integration is implied. Hosted CI and final-head review are recorded on the PR.
