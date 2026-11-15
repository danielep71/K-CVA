"""Fixtures for the workflow rules in tools/check_workflows.py."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import check_workflows
from check_workflows import check, check_all, check_required, load

SHA = "a" * 40
CHECKOUT = f"actions/checkout@{SHA}"


def workflow(jobs: str, top: str = "permissions:\n  contents: read\n",
             on: str = "on:\n  push:\n") -> dict[str, object]:
    return load(textwrap.dedent(on) + textwrap.dedent(top) + "jobs:\n"
                + textwrap.indent(textwrap.dedent(jobs), "  "))


JOB_PERMISSIONS = "  permissions:\n    contents: read\n"
GOOD_JOB = f"""\
build:
  runs-on: ubuntu-24.04
  timeout-minutes: 5
{JOB_PERMISSIONS}  steps:
    - uses: {CHECKOUT}
      with:
        persist-credentials: false
"""

PUSH_BRANCHES = "  push:\n    branches: [main, 'release/**']\n"
REQUIRED = f"""\
on:
  pull_request:
{PUSH_BRANCHES}permissions:
  contents: read
jobs:
  integrity:
    name: Repository integrity
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
"""


class RuleTests(unittest.TestCase):
    def test_valid_workflow_passes(self) -> None:
        self.assertEqual(check("x.yml", workflow(GOOD_JOB)), [])

    def test_top_level_permissions_must_be_explicit_and_read_only(self) -> None:
        cases = {"": "explicit read-only", "permissions: write-all\n": "explicit read-only",
                 "permissions:\n  contents: write\n": "grant write: contents"}
        for top, message in cases.items():
            with self.subTest(top=top):
                found = check("x.yml", workflow(GOOD_JOB, top=top))
                self.assertTrue(any(message in line for line in found), found)
        for top in ("permissions: {}\n", "permissions: read-all\n"):
            with self.subTest(top=top):
                self.assertEqual(check("x.yml", workflow(GOOD_JOB, top=top)), [])

    def test_job_write_scope_needs_the_allowlist(self) -> None:
        job = GOOD_JOB.replace(JOB_PERMISSIONS, "  permissions:\n    contents: read\n    issues: write\n")
        found = check("x.yml", workflow(job))
        self.assertEqual(found, ["x.yml: job build: write scope not allowed: issues"])
        allowed = {("x.yml", "build"): frozenset({"issues"})}
        original = check_workflows.WRITE_ALLOWED
        check_workflows.WRITE_ALLOWED = allowed
        try:
            self.assertEqual(check("x.yml", workflow(job)), [])
            # The allowlist names a job, not a workflow: another job may not write.
            self.assertTrue(check("x.yml", workflow(job.replace("build:", "other:", 1))))
        finally:
            check_workflows.WRITE_ALLOWED = original
        found = check("x.yml", workflow(GOOD_JOB.replace(JOB_PERMISSIONS, "  permissions: write-all\n")))
        self.assertIn("x.yml: job build: permissions must be an explicit mapping", found)

    def test_every_job_sets_its_own_permissions(self) -> None:
        # Inheriting the top-level block is not explicit, even when it is read-only.
        found = check("x.yml", workflow(GOOD_JOB.replace(JOB_PERMISSIONS, "")))
        self.assertEqual(found, ["x.yml: job build: permissions must be set on the job"])
        for block in ("  permissions: {}\n", "  permissions:\n    contents: read\n"):
            with self.subTest(block=block):
                self.assertEqual(check("x.yml", workflow(GOOD_JOB.replace(JOB_PERMISSIONS, block))), [])
        reusable = f"call:\n  uses: owner/repo/.github/workflows/w.yml@{SHA}\n"
        self.assertEqual(check("x.yml", workflow(reusable)),
                         ["x.yml: job call: permissions must be set on the job"])

    def test_every_job_needs_a_bounded_timeout(self) -> None:
        for value in ("", "  timeout-minutes: 0\n", "  timeout-minutes: 61\n",
                      "  timeout-minutes: '5'\n", "  timeout-minutes: true\n"):
            with self.subTest(value=value):
                job = GOOD_JOB.replace("  timeout-minutes: 5\n", value)
                self.assertIn("x.yml: job build: timeout-minutes must be 1 to 60",
                              check("x.yml", workflow(job)))

    def test_actions_must_be_pinned_to_a_full_sha(self) -> None:
        for use in ("actions/checkout@v4", f"actions/checkout@{SHA[:39]}",
                    "docker://alpine:3", "./local-action"):
            with self.subTest(use=use):
                job = GOOD_JOB.replace(CHECKOUT, use)
                self.assertTrue(any("not pinned" in line
                                    for line in check("x.yml", workflow(job))))
        reusable = f"call:\n  uses: owner/repo/.github/workflows/w.yml@{SHA}\n  permissions: {{}}\n"
        self.assertEqual(check("x.yml", workflow(reusable)), [])
        self.assertTrue(check("x.yml", workflow(reusable.replace(SHA, "main"))))

    def test_checkout_must_not_persist_credentials(self) -> None:
        for change in ("persist-credentials: true", "persist-credentials: 'true'",
                       "fetch-depth: 1"):
            with self.subTest(change=change):
                job = GOOD_JOB.replace("persist-credentials: false", change)
                self.assertIn("x.yml: job build: checkout must set persist-credentials: false",
                              check("x.yml", workflow(job)))
        job = GOOD_JOB.replace("persist-credentials: false", "persist-credentials: 'false'")
        self.assertEqual(check("x.yml", workflow(job)), [])

    def test_duplicate_keys_are_refused(self) -> None:
        with self.assertRaisesRegex(Exception, "duplicate key"):
            load("on: push\npermissions: {}\npermissions:\n  contents: write\njobs: {}\n")


class RequiredCheckTests(unittest.TestCase):
    def test_required_check_passes_unfiltered(self) -> None:
        self.assertEqual(check_required("r.yml", load(REQUIRED)), [])

    def test_path_filters_conditions_and_names_fail(self) -> None:
        cases = {
            "  pull_request:\n": "  pull_request:\n    paths: [src/**]\n",
            PUSH_BRANCHES: PUSH_BRANCHES + "    paths-ignore: [docs/**]\n",
            "    name: Repository integrity\n": "    name: Repository integrity\n"
                                               "    if: github.actor != 'bot'\n",
        }
        for old, new in cases.items():
            with self.subTest(new=new):
                self.assertTrue(check_required("r.yml", load(REQUIRED.replace(old, new, 1))))
        renamed = REQUIRED.replace("name: Repository integrity", "name: Integrity")
        self.assertTrue(check_required("r.yml", load(renamed)))
        no_push = REQUIRED.replace(PUSH_BRANCHES, "")
        self.assertIn("r.yml: required check must run on push",
                      check_required("r.yml", load(no_push)))

    def test_branch_filters_keep_every_pull_request_and_the_landing_pushes(self) -> None:
        cases = {
            ("  pull_request:\n", "  pull_request:\n    branches: [main]\n"):
                "r.yml: required check must run on pull requests to any base",
            ("  pull_request:\n", "  pull_request:\n    branches-ignore: [wip/**]\n"):
                "r.yml: required check must not filter pull_request by branches-ignore",
            (PUSH_BRANCHES, "  push:\n    branches: [main]\n"):
                "r.yml: required check's push branches must include release/**",
            (PUSH_BRANCHES, "  push:\n    branches: ['release/**']\n"):
                "r.yml: required check's push branches must include main",
            (PUSH_BRANCHES, "  push:\n"):
                "r.yml: required check's push branches must include main, release/**",
            (PUSH_BRANCHES, PUSH_BRANCHES + "    branches-ignore: [wip/**]\n"):
                "r.yml: required check must not filter push by branches-ignore",
            (PUSH_BRANCHES, "  push:\n    branches: [main, 'release/**', 'task/**']\n"):
                "r.yml: required check's push branches must not list task/**",
            (PUSH_BRANCHES, "  push:\n    branches: [main, 'release/**', '!main']\n"):
                "r.yml: required check's push branches must not list !main",
        }
        for (old, new), message in cases.items():
            with self.subTest(new=new):
                self.assertIn(message, check_required("r.yml", load(REQUIRED.replace(old, new, 1))))
        single = REQUIRED.replace(PUSH_BRANCHES, "  push:\n    branches: main\n")
        self.assertIn("r.yml: required check's push branches must include release/**",
                      check_required("r.yml", load(single)))


class RepositoryTests(unittest.TestCase):
    def test_repository_workflows_pass(self) -> None:
        self.assertEqual(check_all(), [])

    def test_missing_required_workflow_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "other.yml").write_text(
                "on: push\npermissions: {}\njobs:\n" + textwrap.indent(GOOD_JOB, "  "),
                encoding="utf-8")
            found = check_all(Path(directory))
        self.assertIn("repository-integrity.yml: the required-check workflow is missing", found)


if __name__ == "__main__":
    unittest.main()
