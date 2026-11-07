"""Regression tests for PR milestone reconciliation, adapted from MyTemplate."""

from __future__ import annotations

import io
import re
import unittest
import unittest.mock
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

import yaml

ROOT = Path(__file__).resolve().parents[1]


def milestone_script() -> Any:
    run = yaml.safe_load((ROOT / ".github/workflows/pr-milestones.yml").read_text())["jobs"]["clear"]["steps"][0]["run"]
    return run.split("<<'PY'\n", 1)[1].rsplit("PY", 1)[0]


class FakeGitHub:
    def __init__(
        self, pulls: Any, issues: Any = (), *, read_only: Any = False, sticky: Any = False, unpersisted: Any = False
    ) -> None:
        self.items = {pull["number"]: dict(pull, pull_request={}) for pull in pulls}
        self.items.update({issue["number"]: dict(issue) for issue in issues})
        self.patches: list[int] = []
        self.requests: list[tuple[str, str]] = []
        self.read_only = read_only
        self.sticky = sticky
        self.unpersisted = unpersisted

    def __call__(self, method: Any, path: Any, data: Any = None) -> Any:
        self.requests.append((method, path))
        if path.startswith("/repos/o/r/pulls?"):
            match = re.search("[?&]page=(\\d+)", path)
            assert match, path
            page = int(match.group(1))
            pulls = [item for item in self.items.values() if "pull_request" in item]
            return pulls[(page - 1) * 100 : page * 100]
        number = int(path.rsplit("/", 1)[1])
        if method == "PATCH":
            if self.read_only:
                raise HTTPError(path, 403, "Resource not accessible by integration", Message(), None)
            self.patches.append(number)
            if self.unpersisted:
                return dict(self.items[number], milestone=data["milestone"])
            if not self.sticky:
                self.items[number]["milestone"] = data["milestone"]
        return dict(self.items[number])


class MilestoneScriptTests(unittest.TestCase):
    def script(self) -> Any:
        namespace = {"__name__": "milestones"}
        exec(milestone_script(), namespace)  # noqa: S102 - trusted repository workflow under test
        return namespace

    def reconcile(self) -> Any:
        return self.script()["reconcile"]

    def run_job(self, api: Any, event: Any) -> Any:
        """Run the job's logic; return the job summary and what it printed."""
        published: list[str] = []
        with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.script()["run"](api, "o/r", event, published.append)
        return ("".join(published), out.getvalue())

    def test_pull_request_event_clears_only_that_pull_request(self) -> None:
        api = FakeGitHub([{"number": 1, "milestone": {"title": "v1"}}, {"number": 2, "milestone": {"title": "v1"}}])
        self.reconcile()(api, "o/r", {"number": 1, "pull_request": {}})
        self.assertEqual(api.patches, [1])
        self.assertIsNotNone(api.items[2]["milestone"])

    def test_scan_clears_every_pull_request_and_never_touches_issues(self) -> None:
        pulls = [{"number": n, "milestone": {"title": "v1"} if n % 2 else None} for n in range(1, 151)]
        api = FakeGitHub(pulls, issues=[{"number": 500, "milestone": {"title": "v1"}}])
        self.reconcile()(api, "o/r", {"schedule": "17 3 * * *"})
        self.assertEqual(api.patches, list(range(1, 151, 2)))
        self.assertIsNotNone(api.items[500]["milestone"])

    def test_an_issue_number_is_refused(self) -> None:
        api = FakeGitHub([], issues=[{"number": 7, "milestone": {"title": "v1"}}])
        with self.assertRaisesRegex(ValueError, "Refusing to change an issue"):
            self.reconcile()(api, "o/r", {"number": 7, "pull_request": {}})
        self.assertEqual(api.patches, [])

    def test_a_pull_request_without_a_milestone_is_left_alone(self) -> None:
        api = FakeGitHub([{"number": 3, "milestone": None}])
        self.assertEqual(self.reconcile()(api, "o/r", {"number": 3, "pull_request": {}}), [])
        self.assertEqual(api.patches, [])

    def test_a_milestone_that_survives_the_change_fails(self) -> None:
        api = FakeGitHub([{"number": 4, "milestone": {"title": "v1"}}], sticky=True)
        with self.assertRaisesRegex(ValueError, "PR #4 still has a milestone"):
            self.reconcile()(api, "o/r", {"number": 4, "pull_request": {}})

    def test_a_removal_is_read_back_after_the_change(self) -> None:
        api = FakeGitHub([{"number": 8, "milestone": {"title": "v1"}}])
        self.assertEqual(self.reconcile()(api, "o/r", {"number": 8, "pull_request": {}}), [(8, "v1")])
        self.assertEqual(
            api.requests,
            [("GET", "/repos/o/r/issues/8"), ("PATCH", "/repos/o/r/issues/8"), ("GET", "/repos/o/r/issues/8")],
        )

    def test_a_change_the_response_reports_but_github_does_not_keep_fails(self) -> None:
        api = FakeGitHub([{"number": 9, "milestone": {"title": "v1"}}], unpersisted=True)
        published: list[str] = []
        with self.assertRaisesRegex(ValueError, "PR #9 still has a milestone after the change"):
            self.script()["run"](api, "o/r", {"number": 9, "pull_request": {}}, published.append)
        self.assertEqual(published, [], "no removal may be recorded")

    def test_the_summary_lists_each_removal_with_its_scope(self) -> None:
        api = FakeGitHub(
            [
                {"number": 1, "milestone": {"title": "v1 | first\nrelease"}},
                {"number": 2, "milestone": None},
                {"number": 3, "milestone": {"title": "v2"}},
            ]
        )
        summary, printed = self.run_job(api, {"schedule": "17 3 * * *"})
        self.assertEqual(api.patches, [1, 3])
        self.assertIn("Scope: every pull request.", summary)
        self.assertIn("| #1 | v1 \\| first release |", summary)
        self.assertIn("| #3 | v2 |", summary)
        self.assertIn("Removed 2 pull request milestone(s); scope: every pull request", printed)

    def test_a_run_with_nothing_to_remove_says_so(self) -> None:
        summary, _ = self.run_job(FakeGitHub([{"number": 5, "milestone": None}]), {"number": 5, "pull_request": {}})
        self.assertIn("Scope: pull request #5.", summary)
        self.assertIn("nothing was removed", summary)

    def test_a_read_only_token_on_a_pull_request_event_warns(self) -> None:
        api = FakeGitHub([{"number": 6, "milestone": {"title": "v1"}}], read_only=True)
        summary, printed = self.run_job(api, {"number": 6, "pull_request": {}})
        self.assertIn("::warning title=Milestone not removed::", printed)
        self.assertIn("HTTP 403", summary)
        self.assertIn("daily scan or a manual run", summary)
        self.assertIsNotNone(api.items[6]["milestone"])

    def test_a_read_only_token_fails_a_scan(self) -> None:
        api = FakeGitHub([{"number": 6, "milestone": {"title": "v1"}}], read_only=True)
        with self.assertRaises(HTTPError):
            self.run_job(api, {"schedule": "17 3 * * *"})
