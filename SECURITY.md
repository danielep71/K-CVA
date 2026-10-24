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

| Current workflow | Permissions and behavior |
| --- | --- |
| Label synchronization | PR validation reads contents. Reconciliation on relevant main pushes or manual dispatch has contents:read and issues:write. Review the selected ref before dispatching a write-capable run. |
| Label drift | PR fixtures read contents; live checks read contents/issues. No label mutation. |
| Issue triage | Reads contents, issues and pull requests; reports metadata violations without editing issues. |

The workflow files pin actions to full SHAs and disable persisted checkout
credentials. No traffic token or traffic workflow is established by this issue.
Traffic collection belongs to #14. Universal repository CI belongs to #6;
required-check enforcement to #12. A green metadata check is not a security scan.

## Feature status and limitations

Snapshot: **2026-10-24**. Private visibility was read back through the repository
API. Settings evidence recorded in
[issue #12](https://github.com/danielep71/MKT-K-CVA/issues/12)
verified dependency graph and Dependabot alerts enabled, full-SHA pinning
required and default workflow-token read permissions.

Dependabot update configuration is pending #6. Code scanning, secret scanning,
push protection and GitHub private vulnerability reporting have **not been
verified as enabled for this repository**. The connector did not expose their
security_and_analysis status; absence of that field is not proof of availability
or absence. Do not claim these features are active or copy SFTs availability
claims. Use the confirmed email route regardless.

Repository automation and human review do not certify the security of Excel,
operating systems, dependencies or future calculation code.
