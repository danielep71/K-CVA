# Security policy

## Reporting privately

Email **danielep71@gmail.com** with subject **Private security report — MKT-K-CVA**.
The maintainer confirmed this route on 2026-10-24 for issue #4. No test email
was sent. Do not put vulnerability details, credentials or confidential data
in issues, PRs, commits, logs or screenshots, even while the repository is private.

Include the full commit SHA, affected paths, impact, minimal synthetic
reproduction, environment/tool versions and any tested workaround.
Reports are handled on a best-effort basis; no response-time guarantee is made.

## Supported scope

No product version is released or certified. Reports about main and the active
release/0.1.0 branch are accepted. Relevant current components are repository
scripts, issue forms and Actions workflows. Future VBA/workbook components
enter scope when added. Identify modifications and reproduce against an
unmodified repository revision where possible.

Ordinary calculation defects without security impact belong in issues;
P1 is reserved for confirmed calculation defects. Vulnerabilities in third-party
platforms should be reported to their vendors.

## Data and credentials

Use synthetic transactions, counterparties and market data in fixtures and
examples. Never commit client portfolios, personal data, passwords, tokens or
private workbooks. Redact logs and evidence before retaining or sharing them.
Keep secrets in authorized secret storage, with narrowly scoped permissions;
never embed them in source or print them.

If credentials are exposed, revoke/rotate them promptly and contact the owner
privately. Deleting a file does not remove it from Git history or logs.
Coordinate any history rewrite separately; do not force-push protected branches.
Do not weaken organization macro or endpoint policy to run a workbook.

## Automation boundary

| Automation | Permissions and behavior |
| --- | --- |
| Label synchronization | PR validation reads contents. Reconciliation on relevant main pushes or manual dispatch has contents:read and issues:write. Review the selected ref before dispatching a write-capable run. |
| Label drift | PR fixtures read contents; live checks read contents/issues. No label mutation. |
| Issue triage | Reads contents, issues and pull requests; reports metadata violations without editing issues. |
| Repository integrity | Reads contents; runs unfiltered PR/push checks for main and release/**, plus manual dispatch. Uploads diagnostic evidence retained for 30 days. No source or issue mutation; see [CI coverage](docs/CI.md). |
| Dependabot version updates | Weekly GitHub Actions dependency-update PRs targeting release/0.1.0, assigned to the maintainer. No automatic approval or merge; maintainer final-head review is required. |

The workflow files pin actions to full SHAs and disable persisted checkout
credentials. No traffic token or traffic workflow is established by this issue.
Traffic collection belongs to #14. Universal repository CI was delivered by #6
through PR #30 and integrated into main by PR #32; required-check enforcement
remains #12 work. A green metadata check is not a security scan.

## Feature status and limitations

Snapshot: **2026-10-24**, verified in this repository's signed-in
[Advanced Security settings](https://github.com/danielep71/MKT-K-CVA/settings/security_analysis)
and [security overview](https://github.com/danielep71/MKT-K-CVA/security).
The repository API confirmed private visibility, personal ownership and main as
the default branch. No visibility, ownership, subscription or security setting
was changed during this verification.

| Feature | Observed status and limitation |
| --- | --- |
| Dependency graph | Enabled. |
| Dependabot alerts | Enabled. |
| Automatic dependency submission | Disabled. |
| Malware alerts | Disabled. |
| Dependabot security updates / grouped security updates | Both disabled. |
| Dependabot version updates | Configured in [.github/dependabot.yml](.github/dependabot.yml) by #6 and integrated into main by PR #32. Weekly GitHub Actions updates target release/0.1.0; PR #34 demonstrates operation. This is distinct from the disabled security-update features above. |
| Code scanning | Overview explicitly shows disabled and states that Advanced Security is only available for organizations. Unavailable in this repository's current configuration. |
| Secret scanning / repository push protection | Neither control is offered in Advanced Security settings. They are unavailable in the current personal-private configuration under the documented eligibility below; no scan or push-blocking coverage is claimed. |
| GitHub private vulnerability reporting | No control or advisory reporting entry is offered. GitHub documents this feature for public repositories; it is unavailable while this repository remains private. Use the confirmed email route above. |
| Security policy discovery | [SECURITY.md is on main](https://github.com/danielep71/MKT-K-CVA/blob/main/SECURITY.md), integrated by PR #28. The issue chooser security link targets main following #7/PR #32. The private email reporting route remains unchanged. |

Eligibility references checked on the same date:
[secret scanning](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enable-secret-scanning),
[push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection),
and [private vulnerability reporting](https://docs.github.com/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
Secret scanning eligibility includes organization-owned private repositories
with Secret Protection and specified enterprise-managed user repositories;
this repository exposes neither configuration. Repository push protection
requires Secret Protection. User-level push protection for public repositories
does not establish coverage for this private repository.

The missing controls and documented eligibility together establish the current
availability limitation; an omitted API security_and_analysis field alone does
not. Reassess after any ownership, plan or visibility change. Retain private
visibility. Manual review and the data/credential rules above remain necessary.

Existing [issue #12](https://github.com/danielep71/MKT-K-CVA/issues/12) evidence
also records required full-SHA action pinning and default workflow-token read
permissions. Dependency-update configuration was completed by #6. These settings
and repository integrity checks do not constitute code or secret scanning.

Repository automation and human review do not certify the security of Excel,
operating systems, dependencies or future calculation code.
