# Repository settings

The repository's settings are declared in
[.github/repository-settings.json](../.github/repository-settings.json) and
compared with the live repository by `tools/repository_settings.py`. This page
describes that desired state and how to check and change it. The policy behind
it is in [GOVERNANCE.md](GOVERNANCE.md#protection-policy-and-verified-controls).

## Checking and changing the settings

From the repository root, with a token in `GH_TOKEN` (or `GITHUB_TOKEN`) that
has admin rights on the repository, for example `GH_TOKEN=$(gh auth token)`:

| Command | Effect | Exit code |
| --- | --- | --- |
| `python tools/repository_settings.py` | Reads the live settings and prints every difference (preview) | 0 |
| `python tools/repository_settings.py --check` | The same, as a check | 0 if all match, 1 on any difference, 2 if a setting could not be read |
| `python tools/repository_settings.py --apply` | Changes the live settings to the desired state, then reads them again and verifies | as `--check`, after the change |
| add `--report docs/evidence/repository-settings-YYYY-MM-DD.json` | Also writes a dated JSON report of everything read | unchanged |

- **Unread settings:** a setting the token may not read is reported as
  *unread*, never as matching, and `--apply` refuses to run while any setting
  is unread.
- **Never applied:** the visibility is checked but never applied, and a
  ruleset present live but absent from the file is reported, never deleted.
- **Changing a control:** edit the file in a reviewed pull request, run
  `--apply` once it is merged, and keep a `--check` report as evidence.

The script uses only the standard library; its tests (`tools/test_repository_settings.py`,
in the repository checks) run against a fake API, without network access.

## Desired state

**General.** Public; default branch `main`. Issues and the wiki on; Projects
and Discussions off. The repository allows merge commits, squash and rebase
merges, which the rulesets below narrow per branch. Auto-merge off,
update-branch suggestions on, head branches deleted after merge, and no
web-commit sign-off requirement.

**Security.**

| Feature | Desired |
| --- | --- |
| Private vulnerability reporting | On |
| Secret scanning (Secret Protection) and push protection | On |
| Secret scanning: non-provider patterns, validity checks | Off |
| Dependabot alerts | On |
| Dependabot security updates | Off |
| Code scanning default setup | Not configured; code scanning runs in advanced setup ([CI.md](CI.md#code-scanning)), which default setup would break |

**Actions.** Actions enabled and all actions allowed, with full-length
commit-SHA pinning required. The default workflow token is read-only, and
workflows may not create or approve pull requests.

**Rulesets.** All five are active, with no bypass actors and no excluded refs.

| Ruleset (id) | Applies to | Rules |
| --- | --- | --- |
| Protect main (25781886) | The default branch | No deletion or force push. A pull request with resolved conversations and zero required approvals; merge commits only. `Repository integrity` from GitHub Actions (integration 15368) on an up-to-date branch, also when the branch is created. |
| Protect release branches (25781928) | `release/**` | As main, but squash or merge commits allowed, and the check is not required when a release branch is created. |
| Prevent release branch deletion (25781993) | `release/**` | No deletion. |
| Protect release tags (25781957) | `v*` tags | No update, deletion or force push. |
| Protect traffic history (25782014) | `traffic-history` | No deletion or force push; no pull request required, so the Traffic history workflow can push ([TRAFFIC.md](TRAFFIC.md)). |

## Evidence

- [repository-settings-2026-10-31.json](evidence/repository-settings-2026-10-31.json)
  is the first `--check` report. Every setting it could read matched. It
  could not read the Dependabot-alert switch or the Actions permissions,
  which the environment it ran in may not query; those six settings are
  recorded as unread and await a check with the maintainer's token.
- [repository-rulesets-2026-10-24.json](evidence/repository-rulesets-2026-10-24.json)
  is the earlier, hand-made ruleset read-back, kept as history. It names the
  repository by its former name, MKT-K-CVA.

Scanning and reporting availability is described in
[SECURITY.md](../SECURITY.md#current-visibility).
