# Repository settings verification

Verified on 2026-10-24 for #12. This records configured controls. The controlled
failing/passing enforcement exercise of #13 is recorded in
[GOVERNANCE.md](GOVERNANCE.md#demonstrated-enforcement).

## Comparison with CCR-K-SFTs

Live REST readback compared repository general settings and all five rulesets.
Signed-in Actions and Advanced Security settings were inspected for both repos.
[Retained ruleset readback](evidence/repository-rulesets-2026-10-24.json) records
conditions, rules and bypass lists; it contains no credentials.

| Area | Verified result |
| --- | --- |
| General | Both private, main default, Projects off, update-branch suggestions and merged-head deletion on. Repository merge/squash/rebase allowed; auto-merge off. Branch rules narrow merge methods. |
| Main | PR required, zero mandatory approvals, resolved threads, merge commits only, no deletion/force pushes. Repository integrity from GitHub Actions (15368), strict up-to-date true, creation exemption false. |
| Release | Same checks and PR safeguards for release/**; squash and merge allowed, no linear-history rule. Creation exemption true permits starting a release branch; subsequent updates require checks. Separate deletion guard retained. |
| Tags | v* updates, deletion and force pushes blocked. |
| Traffic | traffic-history deletion and force pushes blocked; no PR requirement. Local branch/workflow/credentials remain #14 work. |
| Bypasses | Both repositories' five rulesets active, with no bypass actors or excluded refs. |
| Actions | All actions allowed with full-length SHA pinning required; default token reads contents/packages; Actions-created/approved PRs off. Private-fork workflows and cross-repository access off; retention 90 days. |
| Dependency security | Dependency graph and Dependabot alerts on; automatic dependency submission, malware alerts, security/grouped updates off; zero auto-triage rules. Version-update configuration present; standard GitHub runner. |

The controls above are aligned. Local release/0.1.0 and setup-only workflow scope
are intentional project differences. Source credentials, collaborators,
integrations and access grants were not copied. Traffic implementation in the
reference does not establish local completion. Private-repository scanning and
reporting availability remains documented in [SECURITY.md](../SECURITY.md);
no additional scanner coverage is claimed by this settings change.

## Saved target rulesets

- [Protect main](https://github.com/danielep71/MKT-K-CVA/rules/25781886)
- [Protect release branches](https://github.com/danielep71/MKT-K-CVA/rules/25781928)
- [Release deletion guard](https://github.com/danielep71/MKT-K-CVA/rules/25781993)
- [Release tags](https://github.com/danielep71/MKT-K-CVA/rules/25781957)
- [Traffic history](https://github.com/danielep71/MKT-K-CVA/rules/25782014)

The UI confirmed both source-branch rulesets saved; independent REST readback
confirmed the exact check name, GitHub Actions source, strict policy and creation
settings. No visibility, credential, collaborator, integration or publication
change was made. Future changes must update this snapshot and governance.
