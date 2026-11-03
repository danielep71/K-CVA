"""Check the relative links of the tracked Markdown files, anchors included.

A relative link or image must name a file that exists and, when it has a
``#fragment`` and points to Markdown, an anchor that file defines: a heading,
by GitHub's slug rule, or an explicit ``<a id>``/``<a name>``. The Markdown is
read with markdown-it-py, a CommonMark parser (hash-locked in
tools/requirements.txt), with GitHub's tables and strikethrough, so code
blocks, code spans, Setext headings, reference links, character references
and nested images are read as GitHub reads them. External links are left to
tools/check_external_links.py, which runs on a schedule (docs/CI.md,
Markdown links).
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from markdown_it import MarkdownIt
from markdown_it.token import Token

ROOT = Path(__file__).resolve().parents[1]
PARSER = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
EXPLICIT_ANCHOR = re.compile(r"""<a\s[^>]*?\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.I)


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


def plain_text(children: Sequence[Token] | None) -> str:
    """The text of rendered inline tokens: what a reader sees, without markup."""
    parts = []
    for token in children or []:
        if token.type in ("text", "code_inline"):
            parts.append(token.content)
        elif token.type in ("softbreak", "hardbreak"):
            parts.append("\n")
        elif token.type == "image":
            parts.append(plain_text(token.children))
    return "".join(parts)


def rendered_heading(markdown: str) -> str:
    """The text GitHub renders for a heading's inline Markdown."""
    return "".join(plain_text(token.children) for token in PARSER.parseInline(markdown))


class Slugger:
    """Unique heading anchors in document order, as GitHub's slugger numbers them.

    A repeated slug gets ``-1``, ``-2`` and so on, skipping any suffixed slug
    an earlier heading already produced: ``Foo``, ``Foo``, ``Foo-1`` give
    ``foo``, ``foo-1`` and ``foo-1-1``.
    """

    def __init__(self) -> None:
        self.occurrences: dict[str, int] = {}

    def slug(self, text: str) -> str:
        original = result = github_slug(text)
        while result in self.occurrences:
            self.occurrences[original] += 1
            result = f"{original}-{self.occurrences[original]}"
        self.occurrences[result] = 0
        return result


def parse(text: str) -> tuple[list[Token], dict[str, Any]]:
    env: dict[str, Any] = {}
    return PARSER.parse(text, env), env


def walk(tokens: Iterable[Token]) -> Iterator[Token]:
    """Every token, inline children included, in document order."""
    for token in tokens:
        yield token
        if token.children:
            yield from walk(token.children)


def anchors(text: str) -> set[str]:
    """Every anchor a Markdown document defines."""
    tokens, _ = parse(text)
    found: set[str] = set()
    slugger = Slugger()
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            found.add(slugger.slug(plain_text(tokens[index + 1].children)))
    for token in walk(tokens):
        if token.type in ("html_block", "html_inline"):
            found.update(EXPLICIT_ANCHOR.findall(token.content))
    return found


def links(text: str) -> Iterator[str]:
    """The targets of the links and images of a Markdown document, outside code.

    Reference-style links are resolved; a definition that no link uses is
    not a link.
    """
    tokens, _ = parse(text)
    for token in walk(tokens):
        if token.type == "link_open":
            yield str(token.attrGet("href") or "")
        elif token.type == "image":
            yield str(token.attrGet("src") or "")


def reference_definitions(text: str) -> list[str]:
    """The targets of every reference definition, used or not."""
    _, env = parse(text)
    return [str(entry["href"]) for entry in env.get("references", {}).values()]


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
