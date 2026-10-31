"""Check the relative links of the tracked Markdown files, anchors included.

A relative link must name a file that exists and, when it has a ``#fragment``
and points to Markdown, an anchor that file defines: a heading, by GitHub's
slug rule, or an explicit ``<a id>``/``<a name>``. Links and headings inside
fenced code blocks or inline code are not links or headings. External links
are left to tools/check_external_links.py, which runs on a schedule
(docs/CI.md, Markdown links).
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Iterator
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
EXPLICIT_ANCHOR = re.compile(r"""<a\s[^>]*?\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.I)
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'(][^)]*)?\s*\)")
IMAGE_OR_LINK_TEXT = re.compile(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")
EMPHASIS = re.compile(r"(?<![\w*_])[*_]{1,3}(?=\S)|(?<=\S)[*_]{1,3}(?![\w*_])")


def github_slug(text: str) -> str:
    """GitHub's heading anchor for the rendered heading ``text``.

    Lower-case; keep Unicode letters, marks (so U+FE0F after an emoji stays),
    decimal digits, connector punctuation, ``-`` and spaces; drop every other
    character; then turn each space into ``-``.
    """
    kept = []
    for char in text.lower():
        category = unicodedata.category(char)
        if category[0] in "LM" or category in ("Nd", "Pc") or char in "- ":
            kept.append(char)
    return "".join(kept).replace(" ", "-")


def rendered_heading(markdown: str) -> str:
    """The text GitHub renders for a heading's inline Markdown.

    Code spans keep their content as written; elsewhere links and images
    become their text, HTML tags disappear and emphasis markers are removed.
    """
    parts = []
    last = 0
    for match in INLINE_CODE.finditer(markdown):
        parts.append(_plain(markdown[last:match.start()]))
        parts.append(match.group(2).strip())
        last = match.end()
    parts.append(_plain(markdown[last:]))
    return "".join(parts)


def _plain(text: str) -> str:
    text = IMAGE_OR_LINK_TEXT.sub(r"\1", text)
    text = HTML_TAG.sub("", text)
    return EMPHASIS.sub("", text)


def prose_lines(text: str) -> Iterator[str]:
    """The lines of ``text`` outside fenced code blocks."""
    fence = ""
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) \
                    and not line.strip()[len(match.group(1)):].strip():
                fence = ""
            continue
        if match:
            fence = match.group(1)
            continue
        yield line


def anchors(text: str) -> set[str]:
    """Every anchor a Markdown document defines."""
    found: set[str] = set()
    counts: dict[str, int] = {}
    for line in prose_lines(text):
        found.update(EXPLICIT_ANCHOR.findall(INLINE_CODE.sub("", line)))
        heading = HEADING.match(line)
        if heading:
            slug = github_slug(rendered_heading(heading.group(2)))
            seen = counts.get(slug, 0)
            counts[slug] = seen + 1
            found.add(slug if seen == 0 else f"{slug}-{seen}")
    return found


def links(text: str) -> Iterator[str]:
    """The inline-link targets of a Markdown document, outside code."""
    for line in prose_lines(text):
        yield from LINK.findall(INLINE_CODE.sub("", line))


def check_file(path: Path, root: Path, cache: dict[Path, set[str]]) -> list[str]:
    """Problems with the relative links of the Markdown file ``path``."""
    found = []
    name = path.relative_to(root).as_posix()
    for target in links(path.read_text(encoding="utf-8")):
        if "://" in target or target.startswith(("mailto:", "tel:")):
            continue
        location, _, fragment = target.partition("#")
        resolved = (path.parent / unquote(location)).resolve() if location else path
        if not resolved.exists():
            found.append(f"{name}: missing link target {target}")
            continue
        if not fragment or resolved.suffix.lower() != ".md":
            continue
        if resolved not in cache:
            cache[resolved] = anchors(resolved.read_text(encoding="utf-8"))
        if unquote(fragment) not in cache[resolved]:
            found.append(f"{name}: missing anchor #{fragment} in {resolved.relative_to(root).as_posix()}")
    return found


def check_all(paths: Iterable[Path], root: Path = ROOT) -> list[str]:
    cache: dict[Path, set[str]] = {}
    found: list[str] = []
    for path in paths:
        found += check_file(path.resolve(), root.resolve(), cache)
    return found


def tracked_markdown(root: Path = ROOT) -> list[Path]:
    names = subprocess.check_output(["git", "ls-files", "-z", "*.md"], cwd=root).decode().split("\0")
    return [root / name for name in names if name]


def main() -> int:
    paths = tracked_markdown()
    found = check_all(paths)
    for message in found:
        print(message)
    print(f"{len(paths)} Markdown files checked: {'FAIL' if found else 'PASS'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
