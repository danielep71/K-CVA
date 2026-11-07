"""End-to-end tests of .github/scripts/labels-sync.mjs against a local fake GitHub API.

The script's self-test covers its functions; these tests run its command line,
so that the order of its steps is covered too. They need Node.js.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/labels-sync.mjs"
MANIFEST = ROOT / ".github/labels.json"
NODE = shutil.which("node")


class FakeGitHub:
    """The repository's labels, the issues that carry them, and every request made."""

    def __init__(self, labels: list[dict[str, Any]], issue_labels: list[str]) -> None:
        self.labels = labels
        self.issue_labels = issue_labels
        self.requests: list[tuple[str, str]] = []

    def answer(self, method: str, target: str) -> tuple[int, Any]:
        self.requests.append((method, target))
        url = urlsplit(target)
        query = parse_qs(url.query)
        if method == "GET" and url.path.endswith("/labels"):
            page = int(query.get("page", ["1"])[0])
            return 200, self.labels if page == 1 else []
        if method == "GET" and url.path.endswith("/issues"):
            wanted = query.get("labels", [None])[0]
            carried = [] if wanted not in self.issue_labels else [{"number": 1, "labels": [{"name": wanted}]}]
            return 200, carried
        return 500, {"message": f"unexpected {method} {target}"}

    @property
    def writes(self) -> list[tuple[str, str]]:
        return [request for request in self.requests if request[0] != "GET"]


def serve(api: FakeGitHub) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def respond(self) -> None:
            status, body = api.answer(self.command, self.path)
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_PATCH = do_DELETE = respond

        def log_message(self, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@unittest.skipIf(NODE is None and not os.environ.get("GITHUB_ACTIONS"), "Node.js is not on PATH")
class ReconcileOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(manifest["prune"])
        # The resolved catalogue: the core plus the labels of every selected overlay.
        catalogue = list(manifest["core"])
        for name in manifest["selected_overlays"]:
            catalogue += manifest["overlays"][name]
        # Every catalogue label, plus one outside it that an issue still carries.
        live = [dict(label) for label in catalogue] + [
            {"name": "legacy", "color": "ABCDEF", "description": "outside the catalogue"}]
        self.api = FakeGitHub(live, issue_labels=["legacy"])
        self.server = serve(self.api)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def run_script(self, *extra: str, manifest: Path = MANIFEST) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            env = {key: value for key, value in os.environ.items()
                   if key not in {"GITHUB_STEP_SUMMARY", "GITHUB_REPOSITORY"}}
            env.update(GITHUB_API_URL=f"http://127.0.0.1:{self.server.server_port}",
                       GITHUB_TOKEN="test-token")  # noqa: S106 - synthetic local fake API credential
            return subprocess.run(
                [NODE or "node", str(SCRIPT), "--manifest", str(manifest), "--mode", "reconcile",
                 "--repository", "example/project", *extra],
                capture_output=True, text=True, encoding="utf-8", env=env, cwd=directory, timeout=60, check=False)

    def test_a_selected_overlay_is_reconciled_with_the_core(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest["overlays"] = {"regime": [
            {"name": "zz-regime", "color": "ABCDEF", "description": "overlay label"}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.json"
            manifest["selected_overlays"] = ["regime"]
            path.write_text(json.dumps(manifest), encoding="utf-8")
            selected = self.run_script("--dry-run", manifest=path)
            manifest["selected_overlays"] = []
            path.write_text(json.dumps(manifest), encoding="utf-8")
            unselected = self.run_script("--dry-run", manifest=path)
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertIn("| create | `zz-regime` | missing live label |", selected.stdout)
        core = len(manifest["core"])
        self.assertIn(f"- Core / overlays defined / selected / resolved: **{core} / 1 / 1 / {core + 1}**",
                      selected.stdout)
        self.assertIn("- Selected overlays (1): `regime`", selected.stdout)
        self.assertEqual(unselected.returncode, 0, unselected.stderr)
        self.assertNotIn("zz-regime", unselected.stdout)
        self.assertIn(f"- Core / overlays defined / selected / resolved: **{core} / 1 / 0 / {core}**",
                      unselected.stdout)
        self.assertEqual(self.api.writes, [])

    def test_a_dry_run_previews_the_deletion_of_a_label_in_use(self) -> None:
        result = self.run_script("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("(dry run)", result.stdout)
        self.assertIn("| delete | `legacy` |", result.stdout)
        self.assertEqual(self.api.writes, [])
        self.assertFalse([target for _, target in self.api.requests if "/issues" in target],
                         "a dry run must not query label usage")

    def test_reconcile_refuses_to_prune_a_label_in_use_before_any_write(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Refusing to prune labels still used by an issue or pull request: "legacy"',
                      result.stderr)
        self.assertEqual(self.api.writes, [])


if __name__ == "__main__":
    unittest.main()
