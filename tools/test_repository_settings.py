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
from unittest.mock import patch

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
        self.paused = False
        self.pvr = True
        self.alerts = True
        self.default_setup = "not-configured"
        self.actions = {"enabled": True, "allowed_actions": "all", "sha_pinning_required": True}
        self.workflow = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
        self.rulesets: dict[int, dict[str, Any]] = {1: copy.deepcopy(RULESET) | {"id": 1}}
        self.refused: set[str] = set()
        self.writes: list[str] = []

    # Declarative endpoint dispatch in this fake mirrors independent API routes;
    # splitting it obscures the request/response fixture. Production code has no exemption.
    def request(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:  # noqa: C901
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
        if path == "/automated-security-fixes" and method == "GET":
            status = self.repo["security_and_analysis"]["dependabot_security_updates"]["status"]
            return 200, {"enabled": status == "enabled", "paused": self.paused}
        if path == "/actions/permissions/fork-pr-contributor-approval":
            return 200, {"approval_policy": "all_external_contributors"}
        if path == "/actions/permissions/artifact-and-log-retention":
            return 200, {"days": 90}
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
        if "--apply" in args:
            live = rs.read_live(github)
            args = (*args, "--approve-plan", rs.plan_digest(DESIRED, live, desired.read_bytes()),
                    "--journal", str(Path(directory) / "journal.json"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = rs.main(["--desired", str(desired), *args], client=github)
    return code, output.getvalue()


def apply_test(github: FakeGitHub, desired: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    manifest = json.dumps(desired).encode()
    with tempfile.TemporaryDirectory() as directory:
        return rs.apply(github, desired, live, manifest=manifest,
                        approved=rs.plan_digest(desired, live, manifest), journal=Path(directory) / "journal.json")


class CheckTests(unittest.TestCase):
    def test_matching_settings_pass(self) -> None:
        for args in ((), ("--check",)):
            with self.subTest(args=args):
                self.assertEqual(run(FakeGitHub(), *args)[0], 0)

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
                     'drift: rulesets.Protect main.enforcement: live "disabled", desired "active"'):
            self.assertIn(line, output)
        self.assertEqual(run(github)[0], 0)  # preview reports but does not fail

    def test_unread_settings_are_never_a_match(self) -> None:
        github = FakeGitHub()
        github.refused = {"/actions/permissions", "/vulnerability-alerts"}
        code, output = run(github, "--check")
        self.assertEqual(code, 2)
        self.assertIn("unread: security.vulnerability_alerts", output)
        self.assertIn("unread: actions.sha_pinning_required", output)

    def test_omitted_bypass_actors_are_unread_not_empty(self) -> None:
        # GitHub omits bypass_actors for a token without write access to the ruleset.
        github = FakeGitHub()
        del github.rulesets[1]["bypass_actors"]
        code, output = run(github, "--check")
        self.assertEqual(code, 2, output)
        self.assertIn("unread: rulesets.Protect main.bypass_actors", output)
        code, output = run(github, "--apply")
        self.assertEqual(code, 2, output)
        self.assertEqual(github.writes, [])

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
        self.assertEqual(code, 0)  # equivalent protection under another name
        self.assertEqual(github.writes, [])
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


class AlignmentTests(unittest.TestCase):
    def test_paused_updates_remain_drift_after_apply(self) -> None:
        github = FakeGitHub()
        github.paused = True
        desired = copy.deepcopy(DESIRED)
        desired["security"]["dependabot_security_updates"] = "enabled"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "desired.json"
            path.write_text(json.dumps(desired), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rs.main(["--desired", str(path), "--apply", "--approve-plan",
                    rs.plan_digest(desired, rs.read_live(github), path.read_bytes()),
                    "--journal", str(Path(directory) / "journal.json")], github), 1)
        drift, _ = rs.differences(desired, rs.read_live(github))
        self.assertTrue(any("enabled(paused)" in line for line in drift))

    def test_missing_admin_endpoints_are_unread(self) -> None:
        github = FakeGitHub()
        github.refused = {"/automated-security-fixes", "/actions/permissions/fork-pr-contributor-approval",
                          "/actions/permissions/artifact-and-log-retention"}
        live = rs.read_live(github)
        self.assertEqual(live["security"]["dependabot_security_updates"], rs.UNREAD)
        self.assertEqual(live["actions"]["fork_pr_approval_policy"], rs.UNREAD)
        self.assertEqual(live["actions"]["retention_days"], rs.UNREAD)

    def test_admin_values_are_read_only(self) -> None:
        github = FakeGitHub()
        desired = copy.deepcopy(DESIRED)
        desired["actions"].update(fork_pr_approval_policy="first_time_contributors", retention_days=60)
        live = rs.read_live(github)
        self.assertEqual(live["actions"]["retention_days"], 90)
        self.assertEqual(live["actions"]["fork_pr_approval_policy"], "all_external_contributors")
        self.assertEqual(len(rs.differences(desired, live)[0]), 2)
        self.assertEqual(rs.build_plan(desired, live), [])

    def test_auto_delete_is_last_and_failure_prevents_it(self) -> None:
        for fail in (False, True):
            with self.subTest(fail=fail):
                github = FakeGitHub()
                github.repo["delete_branch_on_merge"] = False
                github.repo["allow_rebase_merge"] = False
                github.rulesets[1]["enforcement"] = "disabled"
                live = rs.read_live(github)
                if fail:
                    github.refused.add("/rulesets/1")
                    with self.assertRaises(ValueError):
                        apply_test(github, DESIRED, live)
                    self.assertFalse(github.repo["delete_branch_on_merge"])
                else:
                    apply_test(github, DESIRED, live)
                    self.assertEqual(github.writes, ["PATCH ", "PUT /rulesets/1", "PATCH "])
                    self.assertTrue(github.repo["delete_branch_on_merge"])


class PlanSafetyTests(unittest.TestCase):
    def test_digest_binds_manifest_destination_observation_and_plan(self) -> None:
        github = FakeGitHub()
        live = rs.read_live(github)
        manifest = json.dumps(DESIRED).encode()
        digest = rs.plan_digest(DESIRED, live, manifest)
        self.assertEqual(digest, rs.plan_digest(DESIRED, copy.deepcopy(live), manifest))
        self.assertNotEqual(digest, rs.plan_digest(DESIRED, live, manifest + b" "))
        for area, key, value in (("general", "visibility", "private"),
                                  ("general", "allow_rebase_merge", False)):
            changed = copy.deepcopy(live)
            changed[area][key] = value
            self.assertNotEqual(digest, rs.plan_digest(DESIRED, changed, manifest))
        changed_desired = dict(DESIRED, repository="another/repo")
        self.assertNotEqual(digest, rs.plan_digest(changed_desired, live, manifest))

    def test_stale_approval_and_existing_journal_never_write(self) -> None:
        github = FakeGitHub()
        live = rs.read_live(github)
        manifest = json.dumps(DESIRED).encode()
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.json"
            digest = rs.plan_digest(DESIRED, live, manifest)
            github.pvr = False
            with self.assertRaises(ValueError):
                rs.apply(github, DESIRED, live, manifest=manifest, approved=digest, journal=journal)
            self.assertFalse(journal.exists())
            live = rs.read_live(github)
            journal.write_text("existing")
            with self.assertRaises(FileExistsError):
                rs.apply(github, DESIRED, live, manifest=manifest,
                         approved=rs.plan_digest(DESIRED, live, manifest), journal=journal)
            self.assertEqual(journal.read_text(), "existing")
            self.assertEqual(github.writes, [])

    def test_journal_precedes_mutations_and_retains_partial_failure(self) -> None:
        github = FakeGitHub()
        github.repo["allow_rebase_merge"] = False
        github.pvr = False
        github.alerts = False
        live = rs.read_live(github)
        manifest = json.dumps(DESIRED).encode()
        original = github.request
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.json"
            def request(method: str, path: str, body: Any = None) -> tuple[int, Any]:
                if method != "GET":
                    record = json.loads(journal.read_text())
                    self.assertTrue(any(e["status"] == "in_progress" for e in record["writes"]))
                if method == "PUT" and path == "/private-vulnerability-reporting":
                    return 500, None
                return original(method, path, body)
            with patch.object(github, "request", side_effect=request), self.assertRaises(RuntimeError):
                rs.apply(github, DESIRED, live, manifest=manifest,
                         approved=rs.plan_digest(DESIRED, live, manifest), journal=journal)
            record = json.loads(journal.read_text())
            self.assertEqual([e["status"] for e in record["writes"]], ["done", "failed_or_unknown", "pending"])
            self.assertTrue(github.repo["allow_rebase_merge"])
            self.assertFalse(github.alerts)

    def test_journal_failure_prevents_first_mutation(self) -> None:
        github = FakeGitHub()
        github.pvr = False
        with patch.object(rs, "write_journal", side_effect=OSError("disk full")), self.assertRaises(OSError):
            apply_test(github, DESIRED, rs.read_live(github))
        self.assertEqual(github.writes, [])

    def test_successful_journal_contains_readback(self) -> None:
        github = FakeGitHub()
        github.pvr = False
        live = rs.read_live(github)
        manifest = json.dumps(DESIRED).encode()
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.json"
            rs.apply(github, DESIRED, live, manifest=manifest,
                     approved=rs.plan_digest(DESIRED, live, manifest), journal=journal)
            record = json.loads(journal.read_text())
            self.assertEqual(record["readback"]["drift"], [])
            self.assertEqual(record["writes"][0]["status"], "done")

    def test_equivalence_refuses_bypass_exclusions_and_inactive_rules(self) -> None:
        for key, value in (("bypass_actors", [{"actor_id": 1}]), ("enforcement", "evaluate"),
                           ("conditions", {"ref_name": {"include": ["~ALL"], "exclude": ["refs/heads/x"]}})):
            candidate = copy.deepcopy(RULESET)
            candidate[key] = value
            self.assertFalse(rs.covers(RULESET, [candidate], "main"))
        candidate = copy.deepcopy(RULESET)
        del candidate["bypass_actors"]
        self.assertFalse(rs.covers(RULESET, [candidate], "main"))

    def test_stronger_rules_are_retained(self) -> None:
        want: dict[str, Any] = {"type": "pull_request", "parameters": {
            "required_approving_review_count": 0, "allowed_merge_methods": ["merge", "squash"]}}
        have = copy.deepcopy(want)
        have["parameters"].update(required_approving_review_count=2, allowed_merge_methods=["merge"])
        self.assertTrue(rs.stronger_rule(want, have))
        self.assertFalse(rs.stronger_rule(have, want))
        desired = copy.deepcopy(DESIRED)
        desired["rulesets"][0]["rules"].append(want)
        github = FakeGitHub()
        github.rulesets[1]["rules"].append(have)
        live = rs.read_live(github)
        self.assertEqual(rs.ruleset_plan(desired, live), [])
        self.assertEqual(rs.differences(desired, live), ([], []))

    def test_missing_rule_does_not_reduce_existing_stronger_parameter(self) -> None:
        desired = copy.deepcopy(DESIRED)
        desired["rulesets"][0]["rules"].append({"type": "pull_request", "parameters": {
            "required_approving_review_count": 0, "required_review_thread_resolution": True}})
        github = FakeGitHub()
        github.rulesets[1]["rules"] = [{"type": "pull_request", "parameters": {
            "required_approving_review_count": 2, "required_review_thread_resolution": False}}]
        live = rs.read_live(github)
        plan = rs.ruleset_plan(desired, live)
        rule = next(r for r in plan[0][2]["rules"] if r["type"] == "pull_request")
        self.assertEqual(rule["parameters"], {"required_approving_review_count": 2,
                                             "required_review_thread_resolution": True})

    def test_combined_equivalent_rulesets_are_not_drift(self) -> None:
        github = FakeGitHub()
        github.rulesets = {
            2: dict(copy.deepcopy(RULESET), id=2, name="First", rules=[{"type": "deletion"}]),
            3: dict(copy.deepcopy(RULESET), id=3, name="Second", rules=[{"type": "non_fast_forward"}])}
        live = rs.read_live(github)
        self.assertEqual(rs.ruleset_plan(DESIRED, live), [])
        self.assertEqual(rs.differences(DESIRED, live), ([], []))

    def test_coverage_uses_projected_default_branch(self) -> None:
        github = FakeGitHub()
        github.repo["default_branch"] = "old-main"
        github.rulesets[1]["conditions"]["ref_name"]["include"] = ["refs/heads/old-main"]
        desired = copy.deepcopy(DESIRED)
        desired["general"]["default_branch"] = "main"
        live = rs.read_live(github)
        plan = rs.build_plan(desired, live)
        self.assertEqual([step[0] for step in plan], ["PATCH", "PUT"])
        self.assertEqual(plan[1][2]["conditions"]["ref_name"]["include"], ["~DEFAULT_BRANCH"])
        after = apply_test(github, desired, live)
        self.assertEqual(rs.differences(desired, after), ([], []))
        # A differently named old-default rule also cannot cover a missing rule.
        github = FakeGitHub()
        github.repo["default_branch"] = "old-main"
        github.rulesets[1].update(name="Other")
        github.rulesets[1]["conditions"]["ref_name"]["include"] = ["refs/heads/old-main"]
        self.assertEqual([step[0] for step in rs.build_plan(desired, rs.read_live(github))], ["PATCH", "POST"])

    def test_coverage_is_evaluated_after_replacement(self) -> None:
        github = FakeGitHub()
        github.rulesets[1]["conditions"]["ref_name"]["include"] = ["~ALL"]
        github.rulesets[1]["rules"] = [{"type": "deletion"}]
        desired = copy.deepcopy(DESIRED)
        other = copy.deepcopy(RULESET)
        other.update(name="Other", conditions={"ref_name": {"include": ["refs/heads/other"], "exclude": []}})
        other["rules"] = [{"type": "deletion"}]
        desired["rulesets"].append(other)
        self.assertTrue(rs.covers(other, list(github.rulesets.values()), "main"))
        plan = rs.ruleset_plan(desired, rs.read_live(github))
        self.assertEqual([step[0] for step in plan], ["PUT", "POST"])


class ReportTests(unittest.TestCase):
    def test_report_records_the_reading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            self.assertEqual(run(FakeGitHub(), "--check", "--report", str(path))[0], 0)
            data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((data["repository"], data["result"], data["drift"], data["unread"]),
                         ("owner/repo", "match", [], []))
        self.assertTrue(data["read_at"].endswith("Z"))
        self.assertEqual(data["mode"], "check")
        self.assertEqual(data["desired"], DESIRED)
        self.assertEqual(len(data["manifest_sha256"]), 64)
        self.assertEqual(data["live"]["rulesets"]["Protect main"]["enforcement"], "active")


if __name__ == "__main__":
    unittest.main()
