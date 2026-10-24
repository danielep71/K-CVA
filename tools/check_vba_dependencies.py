#!/usr/bin/env python3
"""Check the dependency direction of docs/REPOSITORY_STRUCTURE.md, Dependencies.

src/core/ and src/classes/ must stay host-independent: no Excel object model,
worksheet, range or UI, no file, registry or process access, and no dynamic
call whose target no check can see; neither may name a facade, adapter, form,
test or example component. src/core/ standard modules also hold no ambient
mutable run state: no module-level or Static variable. examples/modules/ use
only the supported facade. These are name-based static rules over every
#If branch at once, not a resolution of calls; docs/CI.md lists their limits.
Written for this repository.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from check_vba_jumps import PROC_CLOSE, is_procedure
from vba_lexer import (
    Finding,
    logical_units,
    read_component,
    report,
    split_statements,
    tracked_components,
)

ROOT = Path(__file__).resolve().parents[1]
CORE = "src/core/"
CLASSES = "src/classes/"
EXAMPLES = "examples/modules/"
INDEPENDENT = (CORE, CLASSES)

# Excel and UI globals; an unqualified use reaches the host. Reusing one of
# these names as a local identifier is rejected too, since it shadows the host.
HOST_NAMES = ("Application", "ActiveWorkbook", "ActiveSheet", "ActiveCell", "ActiveChart",
              "ActiveWindow", "ThisWorkbook", "Workbooks", "Worksheets", "Sheets", "Charts",
              "Range", "Cells", "Rows", "Columns", "Selection", "Names", "WorksheetFunction",
              "Excel", "MSForms", "UserForms", "MsgBox", "InputBox", "DoEvents")
HOST = re.compile(rf"(?<![\w.])({'|'.join(HOST_NAMES)})\b", re.I)
HOST_TYPE = re.compile(r"\bAs\s+(?:New\s+)?(Worksheet|Workbook|Chart|Window|Shape|ListObject|"
                       r"PivotTable|Name|UserForm|Control)\b", re.I)
# Bracketed expressions such as [A1] are evaluated by Excel; an Enum's hidden
# member such as [_First] is not.
BRACKET = re.compile(r"\[(?!_\w*\])")
STRING = re.compile(r'"(?:[^"]|"")*"?')
FILE_STATEMENT = re.compile(r"^(?:Open\b.*\bFor\b|Kill|FileCopy|MkDir|RmDir|ChDir|ChDrive|"
                            r"SaveSetting|DeleteSetting|SendKeys|AppActivate|Name\b.*\bAs)\b|"
                            r"^(?:Close|Print|Input|Line\s+Input|Write|Get|Put|Seek|Lock|Unlock)"
                            r"\s*#", re.I)
FILE_FUNCTION = re.compile(r"(?<![\w.])(Dir|Shell|GetSetting|GetAllSettings|Environ|CurDir|"
                           r"FreeFile)\b\$?", re.I)
DYNAMIC = re.compile(r"(?<![\w.])(CallByName|Evaluate|ExecuteExcel4Macro|AddressOf)\b", re.I)
OBJECT = re.compile(r'(?<![\w.])(CreateObject|GetObject)\s*\(\s*(?:"([^"]*)")?', re.I)
ALLOWED_OBJECTS = frozenset({"scripting.dictionary"})
# Components that src/core/ and src/classes/ may not name: the facade and the
# host adapters above them, and the tests and examples beside them. VBA
# resolves names ignoring case, so tracked component names and the CVA_ and
# TEST_ prefixes match in any case; the M_, sh, frm and Example prefixes match
# only as the house style writes them, since in lower case they are ordinary
# identifiers such as m_Total.
UPPER_HOMES = ("src/modules/", "src/workbook/", "src/forms/", "tests/modules/", EXAMPLES)
UPWARD_ANY_CASE = re.compile(r"(?<![\w.])((?:CVA|TEST)_\w+)", re.I)
UPWARD = re.compile(r"(?<![\w.])(M_\w+|Example[A-Z]\w*|sh[A-Z]\w*|frm[A-Z]\w*)")
# Components that examples may not name: everything but the facade. Model
# classes match only by their tracked names: a C prefix pattern would also
# match ordinary identifiers such as Count.
HIDDEN_HOMES = (CORE, CLASSES, "src/workbook/", "src/forms/", "tests/modules/")
HIDDEN_ANY_CASE = re.compile(r"(?<![\w.])((?:CORE|TEST)_\w+)", re.I)
HIDDEN = re.compile(r"(?<![\w.])(M_\w+|sh[A-Z]\w*|frm[A-Z]\w*)")
# The statements after Then and Else of a single-line If, as in
# If Flag Then Kill Path Else Exit Sub.
SINGLE_LINE_IF = re.compile(r"^If\b.*?\bThen\b\s*(\S.*)$", re.I)
ELSE = re.compile(r"\bElse\b", re.I)
MODULE_VARIABLE = re.compile(r"^(?:Dim|Private|Public|Global|Static)\s+(?!(?:Const|Declare|Enum|"
                             r"Type|Sub|Function|Property|Event)\b)(?:WithEvents\s+)?[A-Za-z_]",
                             re.I)
STATIC = re.compile(r"^Static\s+[A-Za-z_]", re.I)


def names(components: Sequence[str]) -> re.Pattern[str] | None:
    """Any of these component names, ignoring case, or None for no component."""
    stems = sorted({Path(path).stem for path in components}, key=len, reverse=True)
    return re.compile(rf"(?<![\w.])({'|'.join(map(re.escape, stems))})\b", re.I) if stems \
        else None


def references(code: str, patterns: Sequence[re.Pattern[str] | None]) -> list[str]:
    """Distinct names matched by any of ``patterns``, in order of appearance."""
    found = sorted((match.start(), match.group(1)) for pattern in patterns if pattern
                   for match in pattern.finditer(code))
    return list(dict.fromkeys(name for _, name in found))


def executable_parts(code: str) -> list[str]:
    """The statement and, for a single-line If, the statements after Then and Else."""
    parts: list[str] = []
    pending = [code.strip()]
    while pending:
        for piece in (item.strip() for item in ELSE.split(pending.pop())):
            parts.append(piece)
            branch = SINGLE_LINE_IF.match(piece)
            if branch:
                pending.append(branch.group(1))
    return parts


def object_calls(raw: str) -> list[re.Match[str]]:
    """CreateObject and GetObject calls outside string literals."""
    literals = [match.span() for match in STRING.finditer(raw)]
    return [match for match in OBJECT.finditer(raw)
            if not any(start <= match.start() < end for start, end in literals)]


def host_independent(path: str, line: int, code: str, raw: str,
                     upper: re.Pattern[str] | None) -> list[Finding]:
    """Host, file, process, dynamic-call and upward references in one statement."""
    findings: list[Finding] = []

    def add(message: str) -> None:
        findings.append(Finding(path, line, message))

    for match in HOST.finditer(code):
        add(f"{match.group(1)} reaches the Excel host; core and classes are host-independent")
    for match in HOST_TYPE.finditer(code):
        add(f"As {match.group(1)} is an Excel or UI type; core and classes are host-independent")
    if BRACKET.search(STRING.sub('""', raw)):
        add("a [...] expression is evaluated by Excel; core and classes are host-independent")
    if any(FILE_STATEMENT.match(part) for part in executable_parts(code)) or \
            FILE_FUNCTION.search(code):
        add("file, registry or process access; core and classes do no I/O")
    for match in DYNAMIC.finditer(code):
        add(f"{match.group(1)}: a dynamic call that no check can resolve")
    for match in object_calls(raw):
        if match.group(1).casefold() == "getobject" or \
                (match.group(2) or "").casefold() not in ALLOWED_OBJECTS:
            add(f"{match.group(1)} creates an object no check can see; only "
                'CreateObject("Scripting.Dictionary") is allowed')
    for name in references(code, (upper, UPWARD_ANY_CASE, UPWARD)):
        add(f"{name} names a facade, host, test or example component; core and "
            "classes depend on nothing above them")
    return findings


def statements(text: str) -> list[tuple[int, str, str]]:
    """``(line, code, raw)`` per statement, code with strings blanked; directives
    are skipped, so every #If branch is read."""
    lines = text.split("\n")
    blanked = logical_units(lines, blank_strings=True)
    kept = logical_units(lines)
    result: list[tuple[int, str, str]] = []
    for (line, _, kind, code), (_, _, _, raw) in zip(blanked, kept, strict=True):
        if kind == "directive" or code.lstrip().startswith(("Attribute ", "Option ")):
            continue
        result.extend((line, part, raw_part) for part, raw_part
                      in zip(split_statements(code), split_statements(raw), strict=False))
    return result


def analyze(path: str, text: str, upper: re.Pattern[str] | None = None,
            hidden: re.Pattern[str] | None = None) -> list[Finding]:
    """Findings for one component; ``upper`` and ``hidden`` match the tracked
    components that core and classes, or examples, may not name."""
    findings: list[Finding] = []
    core_module = path.startswith(CORE) and path.lower().endswith(".bas")
    inside = False
    for line, code, raw in statements(text):
        header = is_procedure(code)
        if path.startswith(INDEPENDENT):
            findings.extend(host_independent(path, line, code, raw, upper))
        elif path.startswith(EXAMPLES):
            findings.extend(Finding(path, line, f"{name} is behind the facade; examples use only "
                                                "the supported API")
                            for name in references(code, (hidden, HIDDEN_ANY_CASE, HIDDEN)))
        if core_module and header and re.match(r"^\s*(?:\w+\s+)?Static\b", code, re.I):
            findings.append(Finding(path, line, f"Static procedure {header.group(2)} keeps state "
                                                "between calls; core holds no run state"))
        elif core_module and not inside and MODULE_VARIABLE.match(code.strip()):
            findings.append(Finding(path, line, "module-level variable; core holds no ambient "
                                                "mutable run state"))
        elif core_module and inside and STATIC.match(code.strip()):
            findings.append(Finding(path, line, "Static variable; core holds no run state"))
        if header:
            inside = True
        elif PROC_CLOSE.match(code):
            inside = False
    return list(dict.fromkeys(findings))


def check(root: Path) -> tuple[list[Finding], int]:
    tracked = tracked_components(root)
    upper = names([path for path in tracked if path.startswith(UPPER_HOMES)])
    hidden = names([path for path in tracked if path.startswith(HIDDEN_HOMES)])
    components = [path for path in tracked if path.startswith((*INDEPENDENT, EXAMPLES))]
    findings: list[Finding] = []
    for path in components:
        findings.extend(analyze(path, read_component(root, path), upper, hidden))
    return findings, len(components)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    findings, components = check(args.root.resolve())
    return report("vba-dependencies", findings,
                  f"{components} component(s) in {', '.join((*INDEPENDENT, EXAMPLES))}")


if __name__ == "__main__":
    sys.exit(main())
