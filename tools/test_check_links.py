"""Fixtures for the Markdown link and anchor checks in tools/check_links.py.

Every anchor of the tracked Markdown on main was compared with GitHub's own
rendering on 2026-10-31 (155 anchors in 23 files, no difference); these
fixtures pin the slug rule and the edge cases.
"""

from __future__ import annotations

import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from check_external_links import Result, check, external_links, probe, report
from check_links import anchors, check_all, github_slug, links, rendered_heading


def slug(heading: str) -> str:
    return github_slug(rendered_heading(heading))


class SlugTests(unittest.TestCase):
    def test_letters_digits_hyphens_and_spaces(self) -> None:
        self.assertEqual(slug("Repository integrity"), "repository-integrity")
        self.assertEqual(slug("Version 0.1.0 (2026)"), "version-010-2026")
        self.assertEqual(slug("Pre-release - notes"), "pre-release---notes")

    def test_punctuation_is_dropped_and_spaces_kept(self) -> None:
        self.assertEqual(slug("Current visibility — verified 2026-10-28"),
                         "current-visibility--verified-2026-10-28")
        self.assertEqual(slug("C++ & C# / Go"), "c--c--go")
        self.assertEqual(slug("100% safe?"), "100-safe")
        self.assertEqual(slug("Tab\tand  two  spaces"), "taband--two--spaces")

    def test_connector_punctuation_and_unicode_are_kept(self) -> None:
        self.assertEqual(slug("snake_case_name"), "snake_case_name")
        self.assertEqual(slug("Résumé ÄÖÜ ß"), "résumé-äöü-ß")
        self.assertEqual(slug("数字 ٣"), "数字-٣")
        self.assertEqual(slug("Circled ①"), "circled-")  # ① is category No, not Nd

    def test_emoji_is_dropped_but_its_variation_selector_stays(self) -> None:
        self.assertEqual(slug("Emoji ❤️ heart"), "emoji-️-heart")
        self.assertEqual(slug("Emoji \U0001f389 party"), "emoji--party")

    def test_markup_is_rendered_first(self) -> None:
        self.assertEqual(slug("Feature `observed_at` and _emphasis_"),
                         "feature-observed_at-and-emphasis")
        self.assertEqual(slug("**Bold** and *italic*"), "bold-and-italic")
        self.assertEqual(slug("[Linked](x.md) heading"), "linked-heading")
        self.assertEqual(slug("<span>HTML</span> tag"), "html-tag")
        self.assertEqual(slug("Research &amp; development"), "research--development")
        self.assertEqual(slug("Caf&eacute; &#169; `&amp;`"), "café--amp")
        self.assertEqual(slug("[API `foo`](api.md)"), "api-foo")
        self.assertEqual(slug("**[Bold link](x.md)** and `__init__`"), "bold-link-and-__init__")
        self.assertEqual(slug("![logo](l.png) [outer ![in](i.png)](o.md)"), "logo-outer-in")
        self.assertEqual(slug("mid_word_name"), "mid_word_name")

    def test_repeated_headings_are_numbered(self) -> None:
        text = "# Notes\n\n## Notes\n\n### Notes\n\n## Other\n"
        self.assertEqual(anchors(text), {"notes", "notes-1", "notes-2", "other"})

    def test_numbering_skips_slugs_already_produced(self) -> None:
        # GitHub: Foo, Foo, Foo-1 give foo, foo-1 and foo-1-1.
        self.assertEqual(anchors("# Foo\n\n# Foo\n\n# Foo-1\n"), {"foo", "foo-1", "foo-1-1"})
        self.assertEqual(anchors("# Foo-1\n\n# Foo\n\n# Foo\n"), {"foo-1", "foo", "foo-2"})

    def test_setext_headings(self) -> None:
        text = ("Setup\n=====\n\nTwo-line\nheading\n---\n\nText\n\n---\n\n"
                "| a | b |\n| --- | --- |\n\n- item\n---\n")
        # The line break of a two-line heading is a newline in its text, which
        # the slug rule drops, as GitHub's own anchor shows.
        self.assertEqual(anchors(text), {"setup", "two-lineheading"})

    def test_explicit_anchors_and_closing_hashes(self) -> None:
        text = '<a id="kept-anchor"></a>\n\n## Title ##\n\n<a name="old-name"></a>\n'
        self.assertEqual(anchors(text), {"kept-anchor", "title", "old-name"})

    def test_code_is_neither_heading_nor_link(self) -> None:
        text = ("```sh\n# not a heading\n[x](missing.md)\n```\n\n"
                "~~~\n## nor this\n~~~\n\n`[y](also-missing.md)` and [z](real.md)\n")
        self.assertEqual(anchors(text), set())
        self.assertEqual(list(links(text)), ["real.md"])

    def test_targets_with_parentheses_titles_and_escapes(self) -> None:
        text = ("[w](https://en.wikipedia.org/wiki/Value_(mathematics)) "
                "[n](a_(b_(c)).md) [t](one.md 'Title') [p](two.md (Title)) "
                "[a](<three (x).md> \"Title\") \\[not](a link) [esc](four\\).md)\n")
        self.assertEqual(list(links(text)), [
            "https://en.wikipedia.org/wiki/Value_(mathematics)", "a_(b_(c)).md", "one.md", "two.md",
            "three%20(x).md", "four).md"])
        self.assertEqual(list(links("[open](unclosed.md and [ok](ok.md)\n")), ["ok.md"])

    def test_an_inline_code_span_does_not_open_a_fence(self) -> None:
        # A backtick fence's info string cannot hold a backtick: this line is code, not a fence.
        text = "```inline``` code\n\n# After\n\n[broken](missing.md)\n"
        self.assertEqual(anchors(text), {"after"})
        self.assertEqual(list(links(text)), ["missing.md"])

    def test_reference_links_resolve_in_headings_and_links(self) -> None:
        text = "# [API][api-docs] notes\n\nSee [it][api-docs].\n\n[api-docs]: api.md#intro\n"
        self.assertEqual(anchors(text), {"api-notes"})
        self.assertEqual(list(links(text)), ["api.md#intro", "api.md#intro"])

    def test_link_forms(self) -> None:
        text = ('[a](one.md#x) ![img](pic.png) [b](<two.md> "title") '
                "[c](https://example.org/x#y) [[d]](three.md) [![badge](badge.svg)](four.md)\n")
        self.assertEqual(list(links(text)),
                         ["one.md#x", "pic.png", "two.md", "https://example.org/x#y", "three.md",
                          "four.md", "badge.svg"])


class CheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "guide.md").write_text(
            "# Guide\n\n## Setup steps\n\n<a id=\"pinned\"></a>\n\nSee [below](#setup-steps).\n",
            encoding="utf-8")
        (self.root / "script.py").write_text("print()\n", encoding="utf-8")

    def check(self, text: str) -> list[str]:
        path = self.root / "README.md"
        path.write_text(text, encoding="utf-8")
        return check_all([path, self.root / "docs" / "guide.md"], self.root)

    def test_valid_links_pass(self) -> None:
        self.assertEqual(self.check(
            "[a](docs/guide.md) [b](docs/guide.md#setup-steps) [c](docs/guide.md#pinned)\n"
            "[d](script.py#L1) [e](#readme) [f](https://example.org/#anything)\n\n# Readme\n"), [])

    def test_missing_file_and_anchors_fail(self) -> None:
        self.assertEqual(self.check(
            "[a](docs/missing.md) [b](docs/guide.md#setup) [c](#nowhere)\n"), [
            "README.md: missing link target docs/missing.md",
            "README.md: missing anchor #setup in docs/guide.md",
            "README.md: missing anchor #nowhere in README.md",
        ])

    def test_percent_encoded_paths_and_fragments(self) -> None:
        (self.root / "docs" / "Two words.md").write_text("## Café\n", encoding="utf-8")
        self.assertEqual(self.check("[a](docs/Two%20words.md#caf%C3%A9)\n"), [])


class FakeOpener:
    """Answers (method, url) from a table, ("*", url) for any method; records the calls."""

    def __init__(self, answers: dict[tuple[str, str], int | Exception]) -> None:
        self.answers = answers
        self.calls: list[tuple[str, str]] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> int:
        key = (request.get_method(), request.full_url)
        self.calls.append(key)
        answer = self.answers.get(key, self.answers.get(("*", request.full_url), 200))
        if isinstance(answer, Exception):
            raise answer
        return answer


opener_for = FakeOpener


class ExternalLinkTests(unittest.TestCase):
    def test_external_links_are_found_outside_code(self) -> None:
        text = ("[![b](https://img.example/b.svg)](https://a.example/x#frag) <https://b.example> [rel](local.md)\n"
                "\n[ref]: https://c.example/doc\n\n"
                "`https://d.example` and [e](https://e.example)\n"
                "```\n[f](https://f.example)\n```\n")
        self.assertEqual(external_links(text), ["https://a.example/x#frag", "https://img.example/b.svg",
                                                "https://b.example", "https://e.example",
                                                "https://c.example/doc"])

    def test_classification(self) -> None:
        url = "https://x.example"
        cases: dict[str, tuple[dict[tuple[str, str], int | Exception], str]] = {
            "head ok": ({("HEAD", url): 200}, "ok"),
            "redirect": ({("HEAD", url): 301}, "ok"),
            "head refused, get ok": ({("HEAD", url): 405, ("GET", url): 200}, "ok"),
            "head 404, get ok": ({("HEAD", url): 404, ("GET", url): 200}, "ok"),
            "not found": ({("*", url): 404}, "broken"),
            "gone": ({("*", url): 410}, "broken"),
            "forbidden": ({("*", url): 403}, "unverified"),
            "rate limited": ({("*", url): 429}, "unverified"),
            "server error": ({("*", url): 503}, "broken"),
            "network": ({("*", url): urllib.error.URLError("no route")}, "broken"),
            "head drops, get ok": ({("HEAD", url): TimeoutError("closed"), ("GET", url): 200}, "ok"),
            "head drops, get 404": ({("HEAD", url): OSError("reset"), ("GET", url): 404}, "broken"),
            "timeout": ({("*", url): TimeoutError("slow")}, "broken"),
        }
        for name, (answers, expected) in cases.items():
            with self.subTest(name=name):
                status, _ = probe(url, opener_for(answers), retry_delay=0)
                self.assertEqual(status, expected)

    def test_sign_in_pages_are_not_requested(self) -> None:
        opener = opener_for({})
        url = "https://github.com/danielep71/K-CVA/settings/security_analysis"
        self.assertEqual(probe(url, opener, retry_delay=0), ("unverified", "sign-in required; not requested"))
        self.assertEqual(opener.calls, [])

    def test_server_errors_are_retried_once(self) -> None:
        opener = opener_for({("*", "https://x.example"): 502})
        probe("https://x.example", opener, retry_delay=0)
        self.assertEqual(len(opener.calls), 4)  # HEAD and GET, twice

    def test_report_lists_broken_and_unverified_with_sources(self) -> None:
        results = check({"https://ok.example": ["README.md"], "https://bad.example": ["a.md", "b.md"],
                         "https://shy.example": ["c.md"]},
                        opener_for({("*", "https://bad.example"): 404, ("*", "https://shy.example"): 403}),
                        retry_delay=0)
        self.assertEqual([r.status for r in results], ["broken", "ok", "unverified"])
        text = report(results)
        self.assertIn("3 URLs checked: 1 broken, 1 unverified.", text)
        self.assertIn("| https://bad.example | GET 404 | a.md, b.md |", text)
        self.assertNotIn("ok.example", text)
        self.assertIsInstance(results[0], Result)


if __name__ == "__main__":
    unittest.main()
