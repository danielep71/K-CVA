"""Compare the repository's live settings with the reviewed desired state.

The desired state is ``.github/repository-settings.json``: the general
settings, the security features, the Actions permissions and the rulesets
(docs/REPOSITORY_SETTINGS.md). Modes:

- preview (default): read the live settings and print every difference;
- ``--check``: the same, exiting 1 on any difference and 2 if a setting could
  not be read (an unread setting is never taken as matching);
- ``--apply``: change the live settings to the desired state, then read them
  again and verify; needs a token with admin rights on the repository;
- ``--report PATH``: also write a dated JSON evidence report of what was read.

The visibility is checked but never applied, and rulesets present live but
absent from the desired state are reported, never deleted. Uses only the
standard library; the token comes from ``GH_TOKEN`` or ``GITHUB_TOKEN``.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[1]
DESIRED = ROOT / ".github" / "repository-settings.json"
API = "https://api.github.com"
GENERAL = ("visibility", "default_branch", "has_issues", "has_projects", "has_wiki", "has_discussions",
           "allow_merge_commit", "allow_squash_merge", "allow_rebase_merge", "allow_auto_merge",
           "allow_update_branch", "delete_branch_on_merge", "web_commit_signoff_required")
NEVER_APPLIED = {"general.visibility"}
RULESET_KEYS = ("name", "target", "enforcement", "conditions", "rules", "bypass_actors")
UNREAD = "<unread>"


class Unreadable(Exception):
    """The API refused to show a setting (missing permission or a blocked path)."""


class Client(Protocol):
    def request(self, method: str, path: str, body: Any = None) -> tuple[int, Any]: ...


class GitHub:
    """A minimal REST client; ``path`` is relative to the repository."""

    def __init__(self, repository: str, token: str | None) -> None:
        self.base = f"{API}/repos/{repository}"
        self.token = token

    def request(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(  # noqa: S310 - the HTTPS GitHub API only
            self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - as above
                raw = response.read()
                return int(response.status), json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            raw = error.read()
            try:
                return error.code, json.loads(raw) if raw else None
            except ValueError:
                return error.code, None


def get(client: Client, path: str, absent: tuple[int, ...] = ()) -> tuple[int, Any]:
    status, data = client.request("GET", path)
    if status in absent or 200 <= status < 300:
        return status, data
    raise Unreadable(f"GET {path}: HTTP {status}")


def normalize_ruleset(ruleset: Mapping[str, Any]) -> dict[str, Any]:
    """The reviewed fields of a ruleset, in a stable order for comparison."""
    data: dict[str, Any] = {key: copy.deepcopy(ruleset.get(key)) for key in RULESET_KEYS}
    data["rules"] = sorted(data["rules"] or [], key=lambda rule: str(rule.get("type")))
    for rule in data["rules"]:
        checks = (rule.get("parameters") or {}).get("required_status_checks")
        if isinstance(checks, list):
            checks.sort(key=lambda check: str(check.get("context")))
    for side in ("include", "exclude"):
        names = ((data.get("conditions") or {}).get("ref_name") or {}).get(side)
        if isinstance(names, list):
            names.sort()
    data["bypass_actors"] = sorted(data["bypass_actors"] or [], key=json.dumps)
    return data


def read_live(client: Client) -> dict[str, Any]:
    """The live settings in the shape of the desired-state file; UNREAD where refused."""
    live: dict[str, Any] = {}
    try:
        _, repository = get(client, "")
        live["general"] = {key: repository.get(key) for key in GENERAL}
        analysis = repository.get("security_and_analysis")
        if not isinstance(analysis, dict):
            raise Unreadable("security_and_analysis is only shown to admins")
        security: dict[str, Any] = {key: value.get("status") for key, value in sorted(analysis.items())}
    except Unreadable:
        live.setdefault("general", {key: UNREAD for key in GENERAL})
        security = {}
    for key, path, reader in (
        ("private_vulnerability_reporting", "/private-vulnerability-reporting",
         lambda status, data: bool(data.get("enabled"))),
        ("vulnerability_alerts", "/vulnerability-alerts", lambda status, data: status == 204),
        ("code_scanning_default_setup", "/code-scanning/default-setup", lambda status, data: data.get("state")),
    ):
        try:
            status, data = get(client, path, absent=(404,) if key == "vulnerability_alerts" else ())
            security[key] = reader(status, data)
        except Unreadable:
            security[key] = UNREAD
    live["security"] = security
    actions: dict[str, Any] = {}
    for path, keys in (("/actions/permissions", ("enabled", "allowed_actions", "sha_pinning_required")),
                       ("/actions/permissions/workflow",
                        ("default_workflow_permissions", "can_approve_pull_request_reviews"))):
        try:
            _, data = get(client, path)
            actions.update({key: data.get(key) for key in keys})
        except Unreadable:
            actions.update(dict.fromkeys(keys, UNREAD))
    live["actions"] = actions
    try:
        _, summaries = get(client, "/rulesets?includes_parents=false&per_page=100")
        rulesets = {}
        for summary in summaries:
            _, detail = get(client, f"/rulesets/{summary['id']}")
            rulesets[detail["name"]] = normalize_ruleset(detail) | {"id": detail["id"]}
        live["rulesets"] = rulesets
    except Unreadable:
        live["rulesets"] = UNREAD
    return live


def differences(desired: Mapping[str, Any], live: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """Return (drift, unread): one line per differing or unreadable setting."""
    drift: list[str] = []
    unread: list[str] = []
    for area in ("general", "security", "actions"):
        for key, want in desired[area].items():
            have = live.get(area, {}).get(key, UNREAD)
            if have == UNREAD:
                unread.append(f"{area}.{key}")
            elif have != want:
                drift.append(f"{area}.{key}: live {json.dumps(have)}, desired {json.dumps(want)}")
    if live["rulesets"] == UNREAD:
        unread.append("rulesets")
        return drift, unread
    wanted = {ruleset["name"]: normalize_ruleset(ruleset) for ruleset in desired["rulesets"]}
    for name, want in wanted.items():
        have = live["rulesets"].get(name)
        if have is None:
            drift.append(f"rulesets.{name}: missing")
            continue
        for key in RULESET_KEYS:
            if have[key] != want[key]:
                drift.append(f"rulesets.{name}.{key}: live {json.dumps(have[key])}, desired {json.dumps(want[key])}")
    drift += [f"rulesets.{name}: not in the desired state (not deleted by --apply)"
              for name in sorted(set(live["rulesets"]) - set(wanted))]
    return drift, unread


def apply(client: Client, desired: Mapping[str, Any], live: Mapping[str, Any]) -> list[str]:
    """Change what differs; return one line per request made."""
    done: list[str] = []

    def send(method: str, path: str, body: Any = None) -> None:
        status, data = client.request(method, path, body)
        if not 200 <= status < 300:
            raise RuntimeError(f"{method} {path}: HTTP {status} {data}")
        done.append(f"{method} {path}")

    general = {key: want for key, want in desired["general"].items()
               if live["general"].get(key) != want and f"general.{key}" not in NEVER_APPLIED}
    # The repository PATCH takes only the secret-scanning switches; Dependabot
    # security updates have their own endpoint, below.
    analysis = {key: {"status": want} for key, want in desired["security"].items()
                if key.startswith("secret_scanning") and live["security"].get(key) != want}
    if general or analysis:
        send("PATCH", "", general | ({"security_and_analysis": analysis} if analysis else {}))
    security = desired["security"]
    updates = security.get("dependabot_security_updates")
    if updates is not None and live["security"].get("dependabot_security_updates") != updates:
        send("PUT" if updates == "enabled" else "DELETE", "/automated-security-fixes")
    if live["security"].get("private_vulnerability_reporting") != security["private_vulnerability_reporting"]:
        send("PUT" if security["private_vulnerability_reporting"] else "DELETE", "/private-vulnerability-reporting")
    if live["security"].get("vulnerability_alerts") != security["vulnerability_alerts"]:
        send("PUT" if security["vulnerability_alerts"] else "DELETE", "/vulnerability-alerts")
    if live["security"].get("code_scanning_default_setup") != security["code_scanning_default_setup"]:
        send("PATCH", "/code-scanning/default-setup", {"state": security["code_scanning_default_setup"]})
    actions = desired["actions"]
    for path, keys in (("/actions/permissions", ("enabled", "allowed_actions", "sha_pinning_required")),
                       ("/actions/permissions/workflow",
                        ("default_workflow_permissions", "can_approve_pull_request_reviews"))):
        if any(live["actions"].get(key) != actions[key] for key in keys):
            send("PUT", path, {key: actions[key] for key in keys})
    for ruleset in desired["rulesets"]:
        want = normalize_ruleset(ruleset)
        have = live["rulesets"].get(want["name"])
        if have is None:
            send("POST", "/rulesets", want)
        elif any(have[key] != want[key] for key in RULESET_KEYS):
            send("PUT", f"/rulesets/{have['id']}", want)
    return done


def report(repository: str, desired_path: Path, live: Mapping[str, Any], drift: list[str],
           unread: list[str]) -> dict[str, Any]:
    return {
        "repository": repository,
        "read_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "desired_state": desired_path.relative_to(ROOT).as_posix() if desired_path.is_relative_to(ROOT)
        else str(desired_path),
        "result": "drift" if drift else "unread" if unread else "match",
        "drift": drift,
        "unread": unread,
        "live": live,
    }


def main(argv: list[str] | None = None, client: Client | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 on drift, 2 on unread settings")
    mode.add_argument("--apply", action="store_true", help="change the live settings to the desired state")
    parser.add_argument("--desired", type=Path, default=DESIRED)
    parser.add_argument("--report", type=Path, help="write a JSON evidence report here")
    args = parser.parse_args(argv)
    desired = json.loads(args.desired.read_text(encoding="utf-8"))
    repository = desired["repository"]
    client = client or GitHub(repository, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    live = read_live(client)
    drift, unread = differences(desired, live)
    if args.apply and drift:
        if unread:
            print("Refusing to apply: unread settings: " + ", ".join(unread), file=sys.stderr)
            return 2
        for line in apply(client, desired, live):
            print("applied: " + line)
        live = read_live(client)
        drift, unread = differences(desired, live)
    for line in drift:
        print("drift: " + line)
    for line in unread:
        print("unread: " + line)
    print(f"{repository}: {len(drift)} differences, {len(unread)} unread settings")
    if args.report:
        args.report.write_text(json.dumps(report(repository, args.desired, live, drift, unread), indent=2) + "\n",
                               encoding="utf-8")
    if drift and (args.check or args.apply):
        return 1
    return 2 if unread and (args.check or args.apply) else 0


if __name__ == "__main__":
    sys.exit(main())
