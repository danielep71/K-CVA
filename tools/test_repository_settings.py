"""Offline tests for tools/repository_settings.py, against a fake GitHub API."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import repository_settings as rs

RULESET: dict[str, Any] = {"name": "Protect main", "target": "branch", "enforcement": "active",
           "conditions": {"ref_name": {"exclude": [], "include": ["~DEFAULT_BRANCH"]}},
           "rules": [{"type": "non_fast_forward"}, {"type": "deletion"}], "bypass_actors": []}
DESIRED: dict[str, Any] = {
    "repository": "owner/repo",
    "general": {"visibility": "public", "allow_rebase_merge": True, "delete_branch_on_merge": True},
    "security": {"dependabot_security_updates": "disabled", "secret_scanning": "enabled",
                 "secret_scanning_push_protection": "enabled", "private_vulnerability_reporting": True,
                 "vulnerability_alerts": True, "code_scanning_default_setup": "not-configured"},
    "actions": {"enabled": True, "allowed_actions": "all", "sha_pinning_required": True,
                "default_workflow_permissions": "read", "can_approve_pull_request_reviews": False},
    "rulesets": [RULESET],
}


class FakeGitHub:
    """Holds a repository's settings; answers and applies REST requests to them."""

    def __init__(self) -> None:
        self.repo: dict[str, Any] = {
            "visibility": "public", "allow_rebase_merge": True, "delete_branch_on_merge": True,
            "security_and_analysis": {"dependabot_security_updates": {"status": "disabled"},
                                      "secret_scanning": {"status": "enabled"},
                                      "secret_scanning_push_protection": {"status": "enabled"}}}
        self.pvr = True
        self.alerts = True
        self.default_setup = "not-configured"
        self.actions = {"enabled": True, "allowed_actions": "all", "sha_pinning_required": True}
        self.workflow = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
        self.rulesets: dict[int, dict[str, Any]] = {1: copy.deepcopy(RULESET) | {"id": 1}}
        self.refused: set[str] = set()
        self.writes: list[str] = []

    def request(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        if path.split("?")[0] in self.refused:
            return 403, {"message": "refused"}
        if method != "GET":
            self.writes.append(f"{method} {path}")
        if path == "":
            if method == "PATCH":
                analysis = body.pop("security_and_analysis", {})
                if "dependabot_security_updates" in analysis:
                    return 422, {"message": "dependabot_security_updates is not a PATCH parameter"}
                self.repo.update(body)
                for key, value in analysis.items():
                    self.repo["security_and_analysis"][key] = value
            return 200, copy.deepcopy(self.repo)
        if path == "/automated-security-fixes" and method in ("PUT", "DELETE"):
            status = "enabled" if method == "PUT" else "disabled"
            self.repo["security_and_analysis"]["dependabot_security_updates"] = {"status": status}
            return 204, None
        if path == "/private-vulnerability-reporting":
            if method != "GET":
                self.pvr = method == "PUT"
            return (200, {"enabled": self.pvr}) if method == "GET" else (204, None)
        if path == "/vulnerability-alerts":
            if method != "GET":
                self.alerts = method == "PUT"
                return 204, None
            return (204, None) if self.alerts else (404, None)
        if path == "/code-scanning/default-setup":
            if method == "PATCH":
                self.default_setup = body["state"]
            return 200, {"state": self.default_setup}
        if path == "/actions/permissions":
            if method == "PUT":
                self.actions = dict(body)
            return 200, dict(self.actions)
        if path == "/actions/permissions/workflow":
            if method == "PUT":
                self.workflow = dict(body)
            return 200, dict(self.workflow)
        if path.startswith("/rulesets?"):
            return 200, [{"id": key} for key in self.rulesets]
        if path == "/rulesets" and method == "POST":
            new_id = max(self.rulesets) + 1
            self.rulesets[new_id] = dict(body) | {"id": new_id}
            return 201, self.rulesets[new_id]
        if path.startswith("/rulesets/"):
            key = int(path.rsplit("/", 1)[1])
            if method == "PUT":
                self.rulesets[key] = dict(body) | {"id": key}
            return 200, copy.deepcopy(self.rulesets[key])
        return 404, None


def run(github: FakeGitHub, *args: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as directory:
        desired = Path(directory) / "desired.json"
        desired.write_text(json.dumps(DESIRED), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = rs.main(["--desired", str(desired), *args], client=github)
    return code, output.getvalue()


class CheckTests(unittest.TestCase):
    def test_matching_settings_pass(self) -> None:
        for args in ((), ("--check",)):
            with self.subTest(args=args):
                self.assertEqual(run(FakeGitHub(), *args), (0, "owner/repo: 0 differences, 0 unread settings\n"))

    def test_drift_is_listed_and_fails_check(self) -> None:
        github = FakeGitHub()
        github.repo["allow_rebase_merge"] = False
        github.pvr = False
        github.rulesets[1]["enforcement"] = "disabled"
        github.rulesets[2] = copy.deepcopy(RULESET) | {"id": 2, "name": "Extra"}
        code, output = run(github, "--check")
        self.assertEqual(code, 1)
        for line in ('drift: general.allow_rebase_merge: live false, desired true',
                     'drift: security.private_vulnerability_reporting: live false, desired true',
                     'drift: rulesets.Protect main.enforcement: live "disabled", desired "active"',
                     "drift: rulesets.Extra: not in the desired state (not deleted by --apply)"):
            self.assertIn(line, output)
        self.assertEqual(run(github)[0], 0)  # preview reports but does not fail

    def test_unread_settings_are_never_a_match(self) -> None:
        github = FakeGitHub()
        github.refused = {"/actions/permissions", "/vulnerability-alerts"}
        code, output = run(github, "--check")
        self.assertEqual(code, 2)
        self.assertIn("unread: security.vulnerability_alerts", output)
        self.assertIn("unread: actions.sha_pinning_required", output)

    def test_ruleset_order_does_not_matter(self) -> None:
        github = FakeGitHub()
        github.rulesets[1]["rules"].reverse()
        self.assertEqual(run(github, "--check")[0], 0)

    def test_normalizing_does_not_change_the_input(self) -> None:
        ruleset = copy.deepcopy(RULESET)
        ruleset["conditions"]["ref_name"]["include"] = ["b", "a"]
        before = copy.deepcopy(ruleset)
        rs.normalize_ruleset(ruleset)
        self.assertEqual(ruleset, before)


class ApplyTests(unittest.TestCase):
    def test_apply_fixes_drift_and_verifies(self) -> None:
        github = FakeGitHub()
        github.repo["allow_rebase_merge"] = False
        github.repo["security_and_analysis"]["secret_scanning_push_protection"] = {"status": "disabled"}
        github.alerts = False
        github.default_setup = "configured"
        github.workflow["default_workflow_permissions"] = "write"
        github.rulesets[1]["enforcement"] = "evaluate"
        code, output = run(github, "--apply")
        self.assertEqual(code, 0, output)
        self.assertEqual(github.writes, ["PATCH ", "PUT /vulnerability-alerts", "PATCH /code-scanning/default-setup",
                                         "PUT /actions/permissions/workflow", "PUT /rulesets/1"])
        self.assertEqual(run(github, "--check")[0], 0)

    def test_dependabot_security_updates_use_their_own_endpoint(self) -> None:
        github = FakeGitHub()
        github.repo["security_and_analysis"]["dependabot_security_updates"] = {"status": "enabled"}
        self.assertEqual(run(github, "--check")[0], 1)
        code, output = run(github, "--apply")
        self.assertEqual(code, 0, output)
        self.assertEqual(github.writes, ["DELETE /automated-security-fixes"])
        self.assertEqual(run(github, "--check")[0], 0)

    def test_missing_ruleset_is_created_extra_is_kept(self) -> None:
        github = FakeGitHub()
        github.rulesets = {7: copy.deepcopy(RULESET) | {"id": 7, "name": "Extra"}}
        code, _ = run(github, "--apply")
        self.assertEqual(code, 1)  # the extra ruleset remains drift
        self.assertEqual(github.writes, ["POST /rulesets"])
        self.assertIn(7, github.rulesets)

    def test_visibility_is_never_applied(self) -> None:
        github = FakeGitHub()
        github.repo["visibility"] = "private"
        code, output = run(github, "--apply")
        self.assertEqual(code, 1)
        self.assertEqual(github.writes, [])
        self.assertIn('general.visibility: live "private", desired "public"', output)

    def test_apply_refuses_when_a_setting_is_unread(self) -> None:
        github = FakeGitHub()
        github.repo["allow_rebase_merge"] = False
        github.refused = {"/actions/permissions"}
        code, output = run(github, "--apply")
        self.assertEqual((code, github.writes), (2, []))
        self.assertIn("Refusing to apply", output)


class ReportTests(unittest.TestCase):
    def test_report_records_the_reading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            self.assertEqual(run(FakeGitHub(), "--check", "--report", str(path))[0], 0)
            data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((data["repository"], data["result"], data["drift"], data["unread"]),
                         ("owner/repo", "match", [], []))
        self.assertTrue(data["read_at"].endswith("Z"))
        self.assertEqual(data["live"]["rulesets"]["Protect main"]["enforcement"], "active")


if __name__ == "__main__":
    unittest.main()
