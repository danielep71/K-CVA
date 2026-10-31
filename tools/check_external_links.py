"""Report broken external links in the tracked Markdown files.

Run weekly by the External links workflow, never on pull requests and never
as a required check: an outside site can be down for a day without any change
here (docs/CI.md, Markdown links). Uses only the standard library.

Each http(s) URL from an inline link, an autolink ``<https://...>`` or a
reference definition is requested once (HEAD, then GET if HEAD is refused).
A 2xx or 3xx answer passes. 401, 403 and 429 are reported as *unverified*:
the site refuses automated clients or rate-limits, which says nothing about
the link. Pages that only a signed-in maintainer can open, listed in
``SIGN_IN_REQUIRED``, are not requested and are reported as unverified too:
GitHub answers an anonymous request for them with 404. Anything else, after
one retry, is *broken* and fails the run.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from check_links import ROOT, links, reference_definitions, tracked_markdown

UNVERIFIED = {401, 403, 429}
# URL prefixes that need a signed-in maintainer; an anonymous check cannot tell.
SIGN_IN_REQUIRED = ("https://github.com/danielep71/K-CVA/settings/",)
USER_AGENT = "K-CVA-link-check (+https://github.com/danielep71/K-CVA)"
Opener = Callable[[urllib.request.Request, float], int]


@dataclass(frozen=True)
class Result:
    url: str
    status: str  # "ok", "unverified" or "broken"
    detail: str
    sources: tuple[str, ...]


def external_links(text: str) -> list[str]:
    """The http(s) URLs a Markdown document links to, outside code.

    Links, images and autolinks are read by the CommonMark parser of
    tools/check_links.py; reference definitions count even when unused.
    """
    found = [*links(text), *reference_definitions(text)]
    return list(dict.fromkeys(url for url in found if url.startswith(("http://", "https://"))))


def collect(paths: Iterable[Path], root: Path = ROOT) -> dict[str, list[str]]:
    """Each URL with the files that link to it."""
    urls: dict[str, list[str]] = {}
    for path in paths:
        name = path.relative_to(root).as_posix()
        for url in external_links(path.read_text(encoding="utf-8")):
            sources = urls.setdefault(url.split("#")[0], [])
            if name not in sources:
                sources.append(name)
    return urls


def urlopen_status(request: urllib.request.Request, timeout: float) -> int:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - http(s) only
            return int(response.status)
    except urllib.error.HTTPError as error:
        return error.code


def probe(url: str, opener: Opener = urlopen_status, timeout: float = 20.0,
          retry_delay: float = 5.0) -> tuple[str, str]:
    """Classify one URL as ok, unverified or broken, with the reason."""
    if url.startswith(SIGN_IN_REQUIRED):
        return "unverified", "sign-in required; not requested"
    detail = ""
    for attempt in range(2):
        code: int | None = None
        # Some servers mishandle HEAD, so a HEAD that fails in any way,
        # with an error status or a network error, is retried as GET.
        for method in ("HEAD", "GET"):
            request = urllib.request.Request(  # noqa: S310 - http(s) URLs from external_links only
                url, method=method, headers={"User-Agent": USER_AGENT})
            try:
                code = opener(request, timeout)
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                code, detail = None, f"{method} {type(error).__name__}: {error}"
                continue
            detail = f"{method} {code}"
            if code < 400:
                return "ok", detail
        if code is not None and code in UNVERIFIED:
            return "unverified", detail
        if code is not None and code < 500:
            return "broken", detail
        if attempt == 0:
            time.sleep(retry_delay)  # one retry for server errors and network failures
    return "broken", detail


def check(urls: dict[str, list[str]], opener: Opener = urlopen_status, retry_delay: float = 5.0) -> list[Result]:
    return [Result(url, *probe(url, opener, retry_delay=retry_delay), tuple(sources))
            for url, sources in sorted(urls.items())]


def report(results: list[Result]) -> str:
    broken = [r for r in results if r.status == "broken"]
    unverified = [r for r in results if r.status == "unverified"]
    lines = ["# External links", "",
             f"{len(results)} URLs checked: {len(broken)} broken, {len(unverified)} unverified.", ""]
    for title, items in (("Broken", broken), ("Unverified (the site refused an automated check)", unverified)):
        if items:
            lines += [f"## {title}", "", "| URL | Result | Linked from |", "| --- | --- | --- |"]
            lines += [f"| {r.url} | {r.detail} | {', '.join(r.sources)} |" for r in items]
            lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--summary", type=Path, help="append the Markdown report to this file")
    args = parser.parse_args(argv)
    results = check(collect(tracked_markdown()))
    text = report(results)
    print(text)
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    return 1 if any(r.status == "broken" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
