"""Check the relative links of the tracked Markdown files, anchors included.

A relative link must name a file that exists and, when it has a ``#fragment``
and points to Markdown, an anchor that file defines: a heading, by GitHub's
slug rule, or an explicit ``<a id>``/``<a name>``. Links and headings inside
fenced code blocks or inline code are not links or headings. External links
are left to tools/check_external_links.py, which runs on a schedule
(docs/CI.md, Markdown links).
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
# Lines that cannot be the text of a Setext heading: block starts and table rows.
NOT_PARAGRAPH = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|>|<|\|)|\|")
EXPLICIT_ANCHOR = re.compile(r"""<a\s[^>]*?\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.I)
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
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


@dataclass(frozen=True)
class InlineLink:
    """An inline link or image: ``[label](target)`` or ``![label](target)``."""

    start: int
    end: int
    label: str
    target: str


def inline_links(text: str) -> list[InlineLink]:
    """The inline links and images of one line, outermost first.

    A small scanner rather than a regular expression, so that labels may
    nest brackets and hold code spans, and targets may hold balanced
    parentheses or be written ``<like this>``, as CommonMark allows.
    """
    found = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "`":
            code = INLINE_CODE.match(text, index)
            index = code.end() if code else index + 1
            continue
        if char == "[" or text.startswith("![", index):
            opening = index + (2 if char == "!" else 1)
            closing = _closing_bracket(text, opening)
            if closing is not None and text.startswith("(", closing + 1):
                destination = _destination(text, closing + 2)
                if destination is not None:
                    target, end = destination
                    found.append(InlineLink(index, end, text[opening:closing], target))
                    index = end
                    continue
        index += 1
    return found


def _closing_bracket(text: str, index: int) -> int | None:
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "`":
            code = INLINE_CODE.match(text, index)
            index = code.end() if code else index + 1
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            if depth == 0:
                return index
            depth -= 1
        index += 1
    return None


def _destination(text: str, index: int) -> tuple[str, int] | None:
    """Parse ``target "title")`` from ``index``; return the target and the end."""
    while index < len(text) and text[index] in " \t":
        index += 1
    if text.startswith("<", index):
        closing = text.find(">", index + 1)
        if closing < 0:
            return None
        target, index = text[index + 1:closing], closing + 1
    else:
        start, depth = index, 0
        while index < len(text):
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char.isspace() or (char == ")" and depth == 0):
                break
            depth += {"(": 1, ")": -1}.get(char, 0)
            index += 1
        target = text[start:index]
    while index < len(text) and text[index] in " \t":
        index += 1
    if index < len(text) and text[index] in "\"'(":
        closing = text.find({"(": ")"}.get(text[index], text[index]), index + 1)
        if closing < 0:
            return None
        index = closing + 1
        while index < len(text) and text[index] in " \t":
            index += 1
    if not text.startswith(")", index):
        return None
    return target, index + 1


def rendered_heading(markdown: str) -> str:
    """The text GitHub renders for a heading's inline Markdown.

    Code spans keep their content as written. Elsewhere links and images
    become their label, HTML tags disappear, emphasis markers are removed and
    character references such as ``&amp;`` become their character.
    """
    spans: list[str] = []

    def protect(match: re.Match[str]) -> str:
        spans.append(match.group(2).strip())
        return f"\ue000{len(spans) - 1}\ue001"

    text = _labels_only(INLINE_CODE.sub(protect, markdown))
    text = html.unescape(EMPHASIS.sub("", HTML_TAG.sub("", text)))
    return re.sub("\ue000(\\d+)\ue001", lambda match: spans[int(match.group(1))], text)


def _labels_only(text: str) -> str:
    """Replace each inline link or image, nested ones included, by its label."""
    parts = []
    last = 0
    for link in inline_links(text):
        parts += [text[last:link.start], _labels_only(link.label)]
        last = link.end
    return "".join([*parts, text[last:]])


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


class Slugger:
    """Unique heading anchors in document order, as GitHub's slugger numbers them.

    A repeated slug gets ``-1``, ``-2`` and so on, skipping any suffixed slug
    an earlier heading already produced: ``Foo``, ``Foo``, ``Foo-1`` give
    ``foo``, ``foo-1`` and ``foo-1-1``.
    """

    def __init__(self) -> None:
        self.occurrences: dict[str, int] = {}

    def slug(self, heading: str) -> str:
        original = result = github_slug(rendered_heading(heading))
        while result in self.occurrences:
            self.occurrences[original] += 1
            result = f"{original}-{self.occurrences[original]}"
        self.occurrences[result] = 0
        return result


def headings(text: str) -> Iterator[str]:
    """The inline Markdown of every heading, ATX or Setext, in document order."""
    paragraph: list[str] = []
    for line in prose_lines(text):
        atx = HEADING.match(line)
        underline = SETEXT_UNDERLINE.match(line)
        if atx:
            paragraph = []
            yield atx.group(2)
        elif underline and paragraph:
            yield " ".join(part.strip() for part in paragraph)
            paragraph = []
        elif not line.strip() or NOT_PARAGRAPH.match(line):
            paragraph = []
        else:
            paragraph.append(line)


def anchors(text: str) -> set[str]:
    """Every anchor a Markdown document defines."""
    found: set[str] = set()
    for line in prose_lines(text):
        found.update(EXPLICIT_ANCHOR.findall(INLINE_CODE.sub("", line)))
    slugger = Slugger()
    found.update(slugger.slug(heading) for heading in headings(text))
    return found


def link_targets(text: str) -> Iterator[str]:
    """The targets of the inline links and images in ``text``, nested ones included."""
    for link in inline_links(text):
        yield link.target
        # A linked image, [![alt](image)](target), has a target of its own.
        yield from link_targets(link.label)


def links(text: str) -> Iterator[str]:
    """The inline-link and image targets of a Markdown document, outside code."""
    for line in prose_lines(text):
        yield from link_targets(INLINE_CODE.sub("", line))


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
