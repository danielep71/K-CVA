"""Compare the repository's live settings with the reviewed desired state.

The desired state is ``.github/repository-settings.json``: the general
settings, the security features, the Actions permissions and the rulesets
(docs/REPOSITORY_SETTINGS.md). Modes:

- preview (default): read the live settings and print every difference;
- ``--check``: the same, exiting 1 on any difference and 2 if a setting could
  not be read (an unread setting is never taken as matching);
- ``--apply --approve-plan SHA256 --journal PATH``: apply an approved plan, then read settings
  again and verify; needs a token with admin rights on the repository;
- ``--report PATH``: also write a dated JSON evidence report of what was read.

The visibility is checked but never applied, and rulesets present live but
absent from the desired state are reported, never deleted. Uses only the
standard library; the token comes from ``GH_TOKEN`` or ``GITHUB_TOKEN``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
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
    # GitHub omits bypass_actors when the token cannot write the ruleset: that
    # is not the same as an empty list, so it is unread, never "no bypass".
    if "bypass_actors" in ruleset:
        data["bypass_actors"] = sorted(data["bypass_actors"] or [], key=json.dumps)
    else:
        data["bypass_actors"] = UNREAD
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
    try:
        _, fixes = get(client, "/automated-security-fixes")
        if not isinstance(fixes, dict):
            raise Unreadable("automated-security-fixes: expected object")
        enabled, paused = fixes.get("enabled"), fixes.get("paused")
        if not isinstance(enabled, bool) or not isinstance(paused, bool):
            raise Unreadable("automated-security-fixes: missing boolean enabled/paused")
        security["dependabot_security_updates"] = (
            "enabled(paused)" if enabled and paused else "enabled" if enabled else "disabled")
    except Unreadable:
        security["dependabot_security_updates"] = UNREAD
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
    # Administrative read-back only: these settings require a separate decision
    # in GitHub's UI, not an implicit write by --apply.
    for key, path, field in (
        ("fork_pr_approval_policy", "/actions/permissions/fork-pr-contributor-approval", "approval_policy"),
        ("retention_days", "/actions/permissions/artifact-and-log-retention", "days"),
    ):
        try:
            _, data = get(client, path)
            value = data.get(field, UNREAD) if isinstance(data, dict) else UNREAD
            valid = (isinstance(value, str) and value in {
                         "first_time_contributors_new_to_github", "first_time_contributors",
                               "all_external_contributors"} if key == "fork_pr_approval_policy"
                     else isinstance(value, int) and not isinstance(value, bool) and value > 0)
            actions[key] = value if valid else UNREAD
        except Unreadable:
            actions[key] = UNREAD
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



def stronger_rule(want: Mapping[str, Any], have: Mapping[str, Any]) -> bool:
    """Conservative partial order; unknown parameters require exact equality."""
    if want["type"] != have["type"]:
        return False
    w, h = want.get("parameters") or {}, have.get("parameters") or {}
    for key in set(w) | set(h):
        a, b = w.get(key), h.get(key)
        if key == "required_approving_review_count" and want["type"] == "pull_request":
            if not isinstance(b, int) or b < (a or 0):
                return False
        elif key == "allowed_merge_methods" and want["type"] == "pull_request":
            if not b or not set(b) <= set(a or ["merge", "squash", "rebase"]):
                return False
        elif key == "required_status_checks" and want["type"] == "required_status_checks":
            required = {(x.get("context"), x.get("integration_id")) for x in a or []}
            actual = {(x.get("context"), x.get("integration_id")) for x in b or []}
            if not required <= actual:
                return False
        elif key == "do_not_enforce_on_create" and want["type"] == "required_status_checks":
            if b not in (False, a):
                return False
        elif isinstance(a, bool) and key in {
                "dismiss_stale_reviews_on_push", "require_code_owner_review",
                "require_last_push_approval", "required_review_thread_resolution",
                "strict_required_status_checks_policy"}:
            if b not in (True, a):
                return False
        elif a != b:
            return False
    return True


def covers(want: Mapping[str, Any], candidates: list[dict[str, Any]], default: str) -> bool:
    """Only active, fully visible rulesets without bypass/exclusions count.

    Ref matching is deliberately conservative: exact patterns, the default
    branch alias and ~ALL; arbitrary glob containment is not inferred.
    """
    if want.get("enforcement") != "active" or want.get("bypass_actors") != []:
        return False
    eligible = []
    for have in candidates:
        if (have.get("enforcement") != "active" or have.get("target") != want["target"]
                or have.get("bypass_actors") != []):
            continue
        conditions = have.get("conditions") or {}
        refs = conditions.get("ref_name") or {}
        if set(conditions) != {"ref_name"} or refs.get("exclude"):
            continue
        required = (want.get("conditions") or {}).get("ref_name") or {}
        if set(want.get("conditions") or {}) != {"ref_name"} or required.get("exclude"):
            continue
        def expand(values: list[str]) -> set[str]:
            return {f"refs/heads/{default}" if v == "~DEFAULT_BRANCH" and default else v for v in values}
        actual = expand(refs.get("include") or [])
        if "~ALL" in actual or expand(required.get("include") or []) <= actual:
            eligible.append(have)
    return all(any(stronger_rule(rule, other) for have in eligible for other in have.get("rules", []))
               for rule in want["rules"]) and bool(eligible)



def replacement(want: dict[str, Any], have: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve additional rules and individually stronger known parameters."""
    result = copy.deepcopy(want)
    rules = {rule["type"]: copy.deepcopy(rule) for rule in have.get("rules", [])}
    for rule in want["rules"]:
        previous = rules.get(rule["type"], {})
        combined = copy.deepcopy(rule)
        parameters = combined.setdefault("parameters", {})
        for key, value in (previous.get("parameters") or {}).items():
            old = {"type": rule["type"], "parameters": {key: value}}
            new = {"type": rule["type"], "parameters": {key: parameters.get(key)}}
            if stronger_rule(new, old):
                parameters[key] = value
        if not parameters:
            combined.pop("parameters")
        rules[rule["type"]] = combined
    result["rules"] = sorted(rules.values(), key=lambda r: str(r["type"]))
    return result


def ruleset_plan(desired: Mapping[str, Any], live: Mapping[str, Any]) -> list[tuple[str, str, Any]]:
    """Replace differing named rulesets first in the projected coverage state."""
    if live["rulesets"] == UNREAD:
        return []
    projected = copy.deepcopy(live["rulesets"])
    default = str(live.get("general", {}).get("default_branch") or "")
    steps = []
    missing = []
    for rule in desired["rulesets"]:
        want = normalize_ruleset(rule)
        have = projected.get(want["name"])
        if have is None:
            missing.append(want)
        elif not covers(want, [have], default) and any(have[k] != want[k] for k in RULESET_KEYS):
            updated = replacement(want, have)
            steps.append(("PUT", f"/rulesets/{have['id']}", updated))
            projected[want["name"]] = updated
    for want in missing:
        if not covers(want, list(projected.values()), default):
            steps.append(("POST", "/rulesets", want))
            projected[want["name"]] = want
    return steps

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
            if covers(want, list(live["rulesets"].values()), str(live["general"].get("default_branch") or "")):
                continue
            drift.append(f"rulesets.{name}: missing")
            continue
        if covers(want, [have], str(live["general"].get("default_branch") or "")):
            continue
        for key in RULESET_KEYS:
            if have[key] == UNREAD:
                unread.append(f"rulesets.{name}.{key}")
            elif have[key] != want[key]:
                drift.append(f"rulesets.{name}.{key}: live {json.dumps(have[key])}, desired {json.dumps(want[key])}")
    default = str(live["general"].get("default_branch") or "")
    drift += [f"rulesets.{name}: not in the desired state (not deleted by --apply)"
              for name in sorted(set(live["rulesets"]) - set(wanted))
              if not any(covers(want, list(live["rulesets"].values()), default)
                         and any(covers(dict(want, rules=[rule]), [live["rulesets"][name]], default)
                                 for rule in want["rules"])
                         for want in wanted.values())]
    return drift, unread


def build_plan(desired: Mapping[str, Any], live: Mapping[str, Any]) -> list[tuple[str, str, Any]]:
    """Compute exact requests without mutation; retain local write policy and order."""
    done: list[tuple[str, str, Any]] = []

    def send(method: str, path: str, body: Any = None) -> None:
        done.append((method, path, copy.deepcopy(body)))

    general = {key: want for key, want in desired["general"].items()
               if live["general"].get(key) != want and f"general.{key}" not in NEVER_APPLIED}
    auto_delete = general.pop("delete_branch_on_merge", None)
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
    done.extend(ruleset_plan(desired, live))
    # Only enable automatic deletion after every protection/security operation
    # succeeds. A failed ruleset write exits before this final PATCH.
    if auto_delete is not None:
        send("PATCH", "", {"delete_branch_on_merge": auto_delete})
    return done



def plan_digest(desired: Mapping[str, Any], live: Mapping[str, Any], manifest: bytes) -> str:
    """Bind approval to destination, manifest, observed state and exact writes."""
    record = {"repository": desired["repository"], "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
              "live": live, "writes": build_plan(desired, live)}
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_journal(path: Path, record: Mapping[str, Any]) -> None:
    """Atomically replace the record; a write failure stops further mutations."""
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply(client: Client, desired: Mapping[str, Any], live: Mapping[str, Any], *,
          manifest: bytes, approved: str, journal: Path) -> dict[str, Any]:
    """Execute the approved snapshot, stopping on any error; never roll back.

    Re-read immediately before planning. This is not a GitHub transaction:
    concurrent external edits during the sequence still require read-back.
    """
    current = read_live(client)
    digest = plan_digest(desired, current, manifest)
    if digest != approved or digest != plan_digest(desired, live, manifest):
        raise ValueError("Refusing to apply: plan changed; review a new preview")
    if differences(desired, current)[1]:
        raise ValueError("Refusing to apply: unread settings")
    steps = build_plan(desired, current)
    record: dict[str, Any] = {"repository": desired["repository"], "plan_sha256": digest,
        "started_at": datetime.now(UTC).isoformat(), "writes": [
            {"method": m, "path": p, "payload": body, "status": "pending"} for m, p, body in steps],
        "readback": None}
    # Exclusive reservation refuses existing paths and symlinks, including races.
    with journal.open("x", encoding="utf-8"):
        pass
    write_journal(journal, record)
    for entry, (method, path, body) in zip(record["writes"], steps, strict=True):
        entry["status"] = "in_progress"
        write_journal(journal, record)
        try:
            status, _ = client.request(method, path, copy.deepcopy(body))
            entry["http_status"] = status
            if not 200 <= status < 300:
                raise RuntimeError(f"{method} {path}: HTTP {status}")
        except Exception:
            entry["status"] = "failed_or_unknown"
            write_journal(journal, record)
            raise
        entry["status"] = "done"
        write_journal(journal, record)
        print(f"applied: {method} {path}")
    try:
        after = read_live(client)
        drift, unread = differences(desired, after)
        record["readback"] = {"live": after, "drift": drift, "unread": unread}
    except Exception:
        record["readback"] = {"error": "read-back failed; inspect live state before retrying"}
        write_journal(journal, record)
        raise
    write_journal(journal, record)
    return after


def report(repository: str, desired_path: Path, live: Mapping[str, Any], drift: list[str],
           unread: list[str], *, mode: str = "preview", manifest: bytes | None = None) -> dict[str, Any]:
    manifest = desired_path.read_bytes() if manifest is None else manifest
    return {
        "repository": repository,
        "mode": mode,
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "desired": json.loads(manifest),
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
    parser.add_argument("--approve-plan", help="SHA256 printed by preview")
    parser.add_argument("--journal", type=Path, help="new JSON journal path in an existing directory")
    args = parser.parse_args(argv)
    if args.apply and (not args.approve_plan or args.journal is None):
        print("Refusing to apply: --approve-plan and --journal are required", file=sys.stderr)
        return 2
    if not args.apply and (args.approve_plan or args.journal):
        parser.error("--approve-plan and --journal require --apply")
    if args.journal and args.report and args.journal.resolve() == args.report.resolve():
        print("Journal and report must use different paths", file=sys.stderr)
        return 2
    manifest = args.desired.read_bytes()
    desired = json.loads(manifest)
    repository = desired["repository"]
    client = client or GitHub(repository, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    live = read_live(client)
    drift, unread = differences(desired, live)
    digest = plan_digest(desired, live, manifest)
    print(f"PLAN SHA-256: {digest}")
    for method, path, body in build_plan(desired, live):
        print(f"plan: {method} {path} {json.dumps(body, sort_keys=True)}")
    if args.apply:
        try:
            live = apply(client, desired, live, manifest=manifest, approved=args.approve_plan, journal=args.journal)
        except (OSError, ValueError, RuntimeError) as error:
            print(str(error), file=sys.stderr)
            return 2
        drift, unread = differences(desired, live)
    for line in drift:
        print("drift: " + line)
    for line in unread:
        print("unread: " + line)
    print(f"{repository}: {len(drift)} differences, {len(unread)} unread settings")
    if args.report:
        evidence = report(repository, args.desired, live, drift, unread, manifest=manifest,
                          mode="apply" if args.apply else "check" if args.check else "preview")
        evidence["plan_sha256"] = digest
        args.report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    if drift and (args.check or args.apply):
        return 1
    return 2 if unread and (args.check or args.apply) else 0


if __name__ == "__main__":
    sys.exit(main())
