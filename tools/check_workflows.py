"""Check the GitHub Actions workflows against the repository's workflow rules.

Every workflow is parsed as YAML (PyYAML, hash-locked in tools/requirements.txt),
not matched with regular expressions. Rules (docs/CI.md, Workflow rules):

- the workflow sets top-level ``permissions`` as a mapping with no write scope;
- every write scope of a job is listed in ``WRITE_ALLOWED`` for that job;
- every job has a positive ``timeout-minutes`` of at most ``MAX_TIMEOUT``;
- every ``uses:`` names an action or workflow at a full commit SHA;
- every ``actions/checkout`` step sets ``persist-credentials: false``;
- the required check runs on ``pull_request`` and ``push`` without path filters,
  and its job has no ``if:`` condition and keeps its check name.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only without the lock installed
    sys.exit("PyYAML is missing: python -m pip install --require-hashes "
             "--only-binary=:all: -r tools/requirements.txt")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MAX_TIMEOUT = 60
# (workflow file, job id) -> the only write scopes that job may hold.
WRITE_ALLOWED: dict[tuple[str, str], frozenset[str]] = {
    ("codeql.yml", "analyze"): frozenset({"security-events"}),
    ("labels-sync.yml", "reconcile"): frozenset({"issues"}),
    ("pr-milestones.yml", "clear"): frozenset({"pull-requests"}),
    ("traffic-history.yml", "collect"): frozenset({"contents"}),
}
REQUIRED_CHECK = ("repository-integrity.yml", "integrity", "Repository integrity")
PINNED = re.compile(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}")


class UniqueKeyLoader(yaml.SafeLoader):
    """A safe loader that refuses duplicate mapping keys instead of keeping the last."""


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode,
                       deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load(text: str) -> dict[str, Any]:
    data = yaml.load(text, Loader=UniqueKeyLoader)  # noqa: S506 - a SafeLoader subclass
    if not isinstance(data, dict):
        raise ValueError("a workflow must be a mapping")
    return data


def triggers(workflow: Mapping[Any, Any]) -> dict[str, Any]:
    """The ``on:`` block; YAML 1.1 reads an unquoted ``on`` key as ``True``."""
    raw = workflow.get("on", workflow.get(True))
    if isinstance(raw, str):
        return {raw: None}
    if isinstance(raw, list):
        return {str(event): None for event in raw}
    return dict(raw) if isinstance(raw, dict) else {}


def write_scopes(permissions: Any) -> set[str] | None:
    """The write scopes a ``permissions`` value grants; None if it is not explicit."""
    if permissions == {}:
        return set()
    if isinstance(permissions, dict):
        return {str(scope) for scope, level in permissions.items() if level == "write"}
    if permissions == "read-all":
        return set()
    return None  # absent, "write-all" or anything unexpected


def steps(job: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
    for step in job.get("steps") or []:
        if isinstance(step, dict):
            yield step


def check(name: str, workflow: Mapping[Any, Any]) -> list[str]:
    """Return one message per broken rule in workflow ``name``."""
    found: list[str] = []
    top = write_scopes(workflow.get("permissions"))
    if top is None:
        found.append(f"{name}: top-level permissions must be an explicit read-only mapping")
    elif top:
        found.append(f"{name}: top-level permissions grant write: {', '.join(sorted(top))}")
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        return [*found, f"{name}: no jobs"]
    for job_id, job in jobs.items():
        where = f"{name}: job {job_id}"
        if not isinstance(job, dict):
            found.append(f"{where}: not a mapping")
            continue
        scopes = write_scopes(job["permissions"]) if "permissions" in job else set()
        if scopes is None:
            found.append(f"{where}: permissions must be an explicit mapping")
        else:
            extra = scopes - WRITE_ALLOWED.get((name, str(job_id)), frozenset())
            if extra:
                found.append(f"{where}: write scope not allowed: {', '.join(sorted(extra))}")
        timeout = job.get("timeout-minutes")
        if "uses" in job:
            uses = [str(job["uses"])]  # a reusable workflow has no timeout of its own
        else:
            uses = [str(step["uses"]) for step in steps(job) if "uses" in step]
            if not (isinstance(timeout, int) and not isinstance(timeout, bool)
                    and 0 < timeout <= MAX_TIMEOUT):
                found.append(f"{where}: timeout-minutes must be 1 to {MAX_TIMEOUT}")
        found += [f"{where}: action not pinned to a full commit SHA: {use}"
                  for use in uses if not PINNED.fullmatch(use)]
        for step in steps(job):
            if str(step.get("uses", "")).startswith("actions/checkout@"):
                persist = (step.get("with") or {}).get("persist-credentials")
                if persist not in (False, "false"):
                    found.append(f"{where}: checkout must set persist-credentials: false")
    return found


def check_required(name: str, workflow: Mapping[Any, Any]) -> list[str]:
    """The required check must run unfiltered and unconditionally under its name."""
    _, job_id, check_name = REQUIRED_CHECK
    found: list[str] = []
    on = triggers(workflow)
    for event in ("pull_request", "push"):
        if event not in on:
            found.append(f"{name}: required check must run on {event}")
            continue
        config = on[event] or {}
        for key in ("paths", "paths-ignore"):
            if key in config:
                found.append(f"{name}: required check must not filter {event} by {key}")
    job = (workflow.get("jobs") or {}).get(job_id)
    if not isinstance(job, dict):
        return [*found, f"{name}: required job {job_id} is missing"]
    if "if" in job:
        found.append(f"{name}: required job {job_id} must not have an if: condition")
    if job.get("name") != check_name:
        found.append(f"{name}: required job {job_id} must be named {check_name!r}")
    return found


def check_all(directory: Path = WORKFLOWS) -> list[str]:
    found: list[str] = []
    paths = sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")])
    names = {path.name for path in paths}
    if REQUIRED_CHECK[0] not in names:
        found.append(f"{REQUIRED_CHECK[0]}: the required-check workflow is missing")
    for job_key in WRITE_ALLOWED:
        if job_key[0] not in names:
            found.append(f"{job_key[0]}: allowlisted workflow is missing")
    for path in paths:
        try:
            workflow = load(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, yaml.YAMLError) as error:
            found.append(f"{path.name}: unreadable: {error}")
            continue
        found += check(path.name, workflow)
        if path.name == REQUIRED_CHECK[0]:
            found += check_required(path.name, workflow)
    return found


def main() -> int:
    found = check_all()
    for message in found:
        print(message)
    count = len(list(WORKFLOWS.glob("*.y*ml")))
    print(f"{count} workflows checked: {'FAIL' if found else 'PASS'}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
