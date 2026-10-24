"""Valid and invalid fixtures for the VBA static checks (tools/check_vba_*.py).

Each fixture is a throw-away Git repository holding synthetic VBA components,
written with CRLF as the VBE exports them and stored under this repository's
.gitattributes. The components are fixtures for the checks only: no
calculation, product or regulatory value is implied by them. Adapted from
CCR-K-SFTs; see NOTICE.md.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

import check_vba_conditionals
import check_vba_dependencies
import check_vba_jumps
import check_vba_public_api
import check_vba_source
from vba_lexer import Finding, strip_code

ROOT = Path(__file__).resolve().parents[1]

CORE = '''Attribute VB_Name = "CORE_Validation"
Option Explicit
Option Private Module

Public Function IsPositive( _
    ByVal Value As Double) _
    As Boolean

        On Error GoTo Failed
        IsPositive = Value > 0
        Exit Function

Failed:
        Err.Raise Err.Number, "CORE_Validation.IsPositive", Err.Description
End Function
'''
FACADE = '''Attribute VB_Name = "CVA_Functions"
Option Explicit

Public Const CVA_FORMAT_TEXT As String = "0.00"


Public Function CVA_IsPositive( _
    ByVal Value As Double) _
    As Variant

        CVA_IsPositive = CORE_Validation.IsPositive(Value)
End Function
'''
INVENTORY = (
    "# Supported VBA declarations\n"
    "CVA_Functions\tConst\tCVA_FORMAT_TEXT\n"
    '# SIG\tCVA_Functions\tConst\tCVA_FORMAT_TEXT\tPublic Const CVA_FORMAT_TEXT As String = "0.00"\n'
    "CVA_Functions\tFunction\tCVA_IsPositive\n"
    "# SIG\tCVA_Functions\tFunction\tCVA_IsPositive\t"
    "Public Function CVA_IsPositive(ByVal Value As Double) As Variant\n"
)
CLASS = '''VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CCalculationResult"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

Private mAmount As Double  'Synthetic value of the fixture


Public Property Get Amount() As Double
        Amount = mAmount
End Property


Public Property Let Amount(ByVal Value As Double)
        mAmount = Value
End Property
'''
WORKBOOK = '''VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ThisWorkbook"
Attribute VB_Base = "0{00020819-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Option Explicit
'''
FORM = '''VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmRunOptions
   Caption         =   "Run options"
   OleObjectBlob   =   "frmRunOptions.frx":0000
End
Attribute VB_Name = "frmRunOptions"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit
'''
HARNESS = '''Attribute VB_Name = "TEST_Harness"
Option Explicit
Option Private Module

Public Sub RunAll()
        Debug.Print "It's ""quoted"": GoTo Nowhere", ['Sheet 1'!A1]
        Rem A comment with an open " quote
End Sub
'''
EXAMPLE = '''Attribute VB_Name = "ExampleInputs"
Option Explicit

Public Sub Run()
        Debug.Print CVA_Functions.CVA_IsPositive(1)
End Sub
'''
VALID: dict[str, str | bytes] = {
    "src/core/CORE_Validation.bas": CORE,
    "src/modules/CVA_Functions.bas": FACADE,
    "src/classes/CCalculationResult.cls": CLASS,
    "src/workbook/ThisWorkbook.cls": WORKBOOK,
    "src/forms/frmRunOptions.frm": FORM,
    "src/forms/frmRunOptions.frx": b"\x00\x01\x02\x03",
    "tests/modules/TEST_Harness.bas": HARNESS,
    "examples/modules/ExampleInputs.bas": EXAMPLE,
    "docs/PUBLIC_API.txt": INVENTORY,
}


@contextlib.contextmanager
def repository(files: Mapping[str, str | bytes], *, attributes: bool = True) -> Iterator[Path]:
    """A Git repository holding ``files``: text written with CRLF, then staged."""
    with tempfile.TemporaryDirectory(prefix="vba-check-") as temporary:
        root = Path(temporary)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        if attributes:
            shutil.copyfile(ROOT / ".gitattributes", root / ".gitattributes")
        for relative, data in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, str):
                data = data.replace("\n", "\r\n").encode("ascii", errors="surrogateescape") \
                    if relative.endswith((".bas", ".cls", ".frm")) else data.encode("utf-8")
            path.write_bytes(data)
        subprocess.run(["git", "-C", str(root), "-c", "core.autocrlf=false", "-c",
                        "core.safecrlf=false", "add", "--all"], check=True)
        yield root


def run_check(check: Callable[[Path], tuple[list[Finding], *tuple[int, ...]]],
              files: Mapping[str, str | bytes], *, attributes: bool = True) -> list[str]:
    with repository(files, attributes=attributes) as root:
        return [str(finding) for finding in check(root)[0]]


def changed(path: str, old: str, new: str, files: Mapping[str, str | bytes] = VALID
            ) -> dict[str, str | bytes]:
    text = files[path]
    assert isinstance(text, str) and old in text, (path, old)
    return {**files, path: text.replace(old, new, 1)}


def standalone(source: str) -> dict[str, str | bytes]:
    """One test module holding ``source``, plus an empty inventory."""
    return {"tests/modules/TEST_Fixture.bas": source, "docs/PUBLIC_API.txt": "# None\n"}


class SourceTest(unittest.TestCase):
    def findings(self, files: Mapping[str, str | bytes], **options: bool) -> list[str]:
        return run_check(check_vba_source.check, files, **options)

    def assertFinding(self, files: Mapping[str, str | bytes], text: str) -> None:
        findings = self.findings(files)
        self.assertTrue(any(text in item for item in findings), findings)

    def test_valid_project_passes(self) -> None:
        self.assertEqual(self.findings(VALID), [])

    def test_empty_repository_passes(self) -> None:
        self.assertEqual(self.findings({"README.md": "# Empty\n"}), [])

    def test_component_outside_its_homes(self) -> None:
        self.assertFinding({"src/CORE_Stray.bas": CORE.replace("CORE_Validation", "CORE_Stray")},
                           "outside its homes")
        self.assertFinding({"src/core/sub/CORE_Validation.bas": CORE}, "outside its homes")
        self.assertFinding({"tools/CORE_Validation.bas": CORE}, "outside its homes")

    def test_home_without_that_component_kind(self) -> None:
        self.assertFinding({"src/core/CORE_Validation.cls": CORE}, "holds no .cls components")
        self.assertFinding({"src/modules/frmRunOptions.frm": FORM}, "holds no .frm components")

    def test_role_prefixes(self) -> None:
        cases = {
            "src/core/Validation.bas": "CORE_<Subject>",
            "src/modules/Functions.bas": "CVA_<Subject>",
            "src/classes/CalculationResult.cls": "C<Noun>",
            "src/workbook/Inputs.cls": "ThisWorkbook or sh<Noun>",
            "src/workbook/Main.bas": "M_<Subject>",
            "tests/modules/Harness.bas": "TEST_<Subject>",
            "examples/modules/Inputs.bas": "Example<Subject>",
        }
        for path, rule in cases.items():
            with self.subTest(path=path):
                source = CORE.replace("CORE_Validation", Path(path).stem)
                self.assertFinding({path: source}, f"is named {rule}")

    def test_form_resource_rules(self) -> None:
        without = {k: v for k, v in VALID.items() if not k.endswith(".frx")}
        self.assertFinding(without, "form resource frmRunOptions.frx is not tracked")
        self.assertFinding({**VALID, "src/forms/frmRunOptions.frx": b""},
                           "resource offset is outside")
        self.assertFinding(changed("src/forms/frmRunOptions.frm",
                                   '"frmRunOptions.frx":0000', '"Other"'),
                           "no form resource")
        self.assertFinding({"src/workbook/frmLost.frx": b"\x00"}, "beside its form")

    def test_vb_name_must_equal_file_name(self) -> None:
        self.assertFinding(changed("src/core/CORE_Validation.bas", 'VB_Name = "CORE_Validation"',
                                   'VB_Name = "CORE_Checks"'),
                           'exactly one Attribute VB_Name = "CORE_Validation"')

    def test_bas_starts_with_vb_name(self) -> None:
        self.assertFinding(changed("src/core/CORE_Validation.bas", "Attribute VB_Name",
                                   "'Banner\nAttribute VB_Name"),
                           "starts with its Attribute VB_Name line")

    def test_names_are_case_insensitive(self) -> None:
        files = {"src/core/CORE_Ab.bas": CORE.replace("CORE_Validation", "CORE_Ab"),
                 "src/core/CORE_AB.bas": CORE.replace("CORE_Validation", "CORE_AB")}
        self.assertFinding(files, "component name also used by")

    def test_name_length_limit(self) -> None:
        name = "CORE_" + "A" * 27
        self.assertFinding({f"src/core/{name}.bas": CORE.replace("CORE_Validation", name)},
                           "longer than 31 characters")

    def test_module_options(self) -> None:
        self.assertFinding(changed("src/modules/CVA_Functions.bas", "Option Explicit\n", ""),
                           "missing Option Explicit")
        for path in ("src/core/CORE_Validation.bas", "tests/modules/TEST_Harness.bas"):
            with self.subTest(path=path):
                self.assertFinding(changed(path, "Option Private Module\n", ""),
                                   "missing Option Private Module")
        for base in ("0", "1"):
            with self.subTest(base=base):
                self.assertFinding(changed("src/core/CORE_Validation.bas", "Option Explicit\n",
                                           f"Option Explicit\nOption Base {base}\n"),
                                   "Option Base; declare explicit array bounds")

    def test_ascii_only(self) -> None:
        self.assertFinding(changed("src/core/CORE_Validation.bas", "Err.Description",
                                   "Err.Description & \"\udce9\""), "non-ASCII byte 0xE9")
        bom = {"src/core/CORE_Validation.bas": b"\xef\xbb\xbf" + CORE.encode("ascii")}
        self.assertFinding(bom, "byte-order mark")

    def test_tabs_and_trailing_white_space(self) -> None:
        self.assertFinding(changed("src/core/CORE_Validation.bas", "        IsPositive =",
                                   "\tIsPositive ="), "tab character")
        self.assertFinding(changed("src/core/CORE_Validation.bas", "Exit Function",
                                   "Exit Function  "), "trailing white space")

    def test_unclosed_string_literal(self) -> None:
        self.assertFinding(changed("tests/modules/TEST_Harness.bas", 'Debug.Print "It',
                                   'Debug.Print "Open\n        Debug.Print "It'),
                           "string literal not closed")

    def test_comment_continuation_is_comment(self) -> None:
        source = changed("tests/modules/TEST_Harness.bas", "End Sub",
                         "        ' A comment that continues _\n        on \" this line\nEnd Sub")
        self.assertEqual(self.findings(source), [])

    def test_storage_needs_lf_and_crlf_checkout(self) -> None:
        findings = self.findings({"src/core/CORE_Validation.bas": CORE}, attributes=False)
        self.assertTrue(any("stored with crlf" in item for item in findings), findings)
        self.assertTrue(any("check it out with CRLF" in item for item in findings), findings)

    def test_workbooks_are_not_committed(self) -> None:
        self.assertFinding({"src/workbook/MKT-K-CVA.xlsm": b"PK\x03\x04"}, "workbook committed")

    def test_main_exit_codes(self) -> None:
        for files, expected in ((VALID, 0), ({"src/Stray.bas": CORE}, 1)):
            with self.subTest(expected=expected), repository(files) as root, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(check_vba_source.main(["--root", str(root)]), expected)
                self.assertIn("static check, nothing compiled or run", output.getvalue())


CONDITIONAL_VALID = {
    "nested": '''#If VBA7 Then
    #If Win64 Then
        Private Declare PtrSafe Function F64 Lib "kernel32" () As LongPtr
    #ElseIf Win32 Then
        Private Declare PtrSafe Function F32 Lib "kernel32" () As Long
    #End If
#Else
    Private Declare Function FLegacy Lib "kernel32" () As Long
#End If
''',
    "inactive-legacy": '''#If Not VBA7 Then
    #If Win64 Then
        Private Declare Function Impossible Lib "kernel32" () As Long
    #End If
#End If
''',
    "boolean-expression": '''#If Not VBA7 Then
    Private Declare Function Legacy Lib "kernel32" () As Long
#ElseIf VBA7 And (Win64 Or Win32) Then
    Private Declare PtrSafe Function Modern Lib "kernel32" () As LongPtr
#End If
''',
    "continued-declare": '''#If VBA7 Then
    Private Declare PtrSafe Function Modern Lib "kernel32" _
        () As LongPtr
#Else
    Private Declare Function Legacy Lib "kernel32" _
        () As Long
#End If
''',
    "colon-separated-ptrsafe": '''Private Const N As Long = 1: Private Declare PtrSafe Function B Lib "kernel32" () As LongPtr
''',
    "colon-separated-legacy-under-vba6": '''#If Not VBA7 Then
    Private Const N As Long = 1: Private Declare Function B Lib "kernel32" () As Long
#End If
''',
    "literals": '''#If True And Not 0 Then
    Private Declare PtrSafe Function Modern Lib "kernel32" () As LongPtr
#End If
''',
}
CONDITIONAL_INVALID = {
    "declare-without-ptrsafe": ('''#If VBA7 And Win64 Then
    Private Declare Function Bad Lib "kernel32" () As Long
#End If
''', "without PtrSafe in vba7-win64"),
    "unconditional-declare": ('Private Declare Function Bad Lib "kernel32" () As Long\n',
                              "without PtrSafe in vba7-win32, vba7-win64"),
    "win32-is-true-on-win64": ('''#If Win32 Then
    Private Declare Function WrongOrder Lib "kernel32" () As Long
#ElseIf Win64 Then
    Private Declare PtrSafe Function NeverReached Lib "kernel32" () As LongPtr
#End If
''', "vba7-win64"),
    "colon-separated-declare": ('Private Const N As Long = 1: Private Declare Function B Lib "kernel32" '
                                '() As Long\n', "without PtrSafe in vba7-win32, vba7-win64"),
    "declare-after-two-colons": ('Private Const N As Long = 1: Private Const M As Long = 2: '
                                 'Private Declare Sub C Lib "kernel32" ()\n',
                                 "without PtrSafe in vba7-win32, vba7-win64"),
    "unknown-symbol": ("#If Mac Then\n#End If\n", "unsupported conditional-compilation symbol"),
    "vba6-is-true-under-vba7": ('''#If VBA6 Then
    Private Declare Function Legacy Lib "kernel32" () As Long
#End If
''', "without PtrSafe in vba7-win32, vba7-win64"),
    "integer-literal": ("#If 2 Then\n#End If\n", "-1 and 0"),
    "missing-then": ("#If VBA7\n#End If\n", "must end with Then"),
    "project-const": ("#Const FEATURE = True\n", "project #Const"),
    "unclosed": ("#If VBA7 Then\n", "not closed"),
    "stray-elseif": ("#ElseIf VBA7 Then\n", "#ElseIf without #If"),
    "elseif-after-else": ("#If VBA7 Then\n#Else\n#ElseIf Win64 Then\n#End If\n",
                          "#ElseIf after #Else"),
    "duplicate-else": ("#If VBA7 Then\n#Else\n#Else\n#End If\n", "duplicate #Else"),
    "stray-end-if": ("#End If\n", "#End If without #If"),
    "unsupported-directive": ("#Region Main\n", "unsupported conditional-compilation directive"),
}


def module(body: str) -> str:
    return f'Attribute VB_Name = "TEST_Fixture"\nOption Explicit\nOption Private Module\n{body}'


class ConditionalTest(unittest.TestCase):
    def test_valid_fixtures_pass(self) -> None:
        self.assertEqual(run_check(check_vba_conditionals.check, VALID), [])
        for name, body in CONDITIONAL_VALID.items():
            with self.subTest(name=name):
                self.assertEqual(run_check(check_vba_conditionals.check,
                                           standalone(module(body))), [])

    def test_invalid_fixtures_fail(self) -> None:
        for name, (body, text) in CONDITIONAL_INVALID.items():
            with self.subTest(name=name):
                findings = run_check(check_vba_conditionals.check, standalone(module(body)))
                self.assertTrue(any(text in item for item in findings), findings)

    def test_reachable_sources_blank_inactive_lines(self) -> None:
        sources, findings = check_vba_conditionals.reachable_sources(
            "x.bas", "A\n#If VBA7 Then\nB\n#Else\nC\n#End If")
        self.assertEqual(findings, [])
        self.assertEqual(sources["vba7-win64"].split("\n"), ["A", "", "B", "", "", ""])
        self.assertEqual(sources["vba6-win32"].split("\n"), ["A", "", "", "", "C", ""])


JUMPS_VALID = {
    "local-handler": '''Public Sub First(ByVal Value As Long)
        On Error GoTo Handler
        GoSub Worker
        Resume 100
Worker:
        Return
100:    Exit Sub
Handler:
        Resume Next
End Sub
''',
    "same-label-in-two-procedures": '''Private Sub First()
Shared:
        Exit Sub
End Sub

Private Sub Second()
Shared:
        Exit Sub
End Sub
''',
    "numbered-label": '''Private Sub First()
        GoTo 100
100     Exit Sub
End Sub
''',
    "special-error-controls": '''Private Sub First()
        On Error GoTo 0
        On Error GoTo -1
        On Error Resume Next
        Resume Next
End Sub
''',
    "quoted-jump-text": '''Private Sub First()
        Debug.Print "GoSub Missing", "GoTo Lost", "Resume Nowhere"
        Debug.Print "He said ""GoSub Missing""; it's text"
        Debug.Print "GoSub Missing" & _
            "Resume Lost"
        Debug.Print "GoSub Missing": GoSub Worker
        Exit Sub
Worker:
        Return
End Sub
''',
    "keyword-before-colon": '''Private Sub First(ByVal Flag As Boolean)
        If Flag Then
            Debug.Print 1
        Else: Debug.Print 2
        End If
        If Not Flag Then
            Debug.Print 3
        Else: Debug.Print 4
        End If
End Sub
''',
    "rem-after-separator": '''Private Sub First()
        Debug.Print 1: Rem GoTo Missing
        Debug.Print 2:Rem GoSub Lost
End Sub
''',
    "one-line-procedure": '''Private Sub First(): Debug.Print 1: End Sub

Private Sub Second(): Debug.Print 2: End Sub
''',
    "rem-after-line-number": '''Private Sub First()
100 Rem GoTo Missing
        Exit Sub
End Sub
''',
    "numbered-comment-line-as-target": '''Private Sub First()
        GoTo 100
100 Rem target
        GoTo 200
200 ' target
End Sub
''',
    "bracketed-sheet-name": '''Private Sub First(): Debug.Print ['Sheet 1'!A1]: End Sub

Private Sub Second()
        Debug.Print [A1:B2]: GoTo Done
Done:
End Sub
''',
    "jump-keyword-in-a-sheet-name": '''Private Sub First()
        Debug.Print ['GoTo Missing'!A1], [GoSub!B2]: GoTo Done
Done:
End Sub
''',
    "computed-jump": '''Private Sub First(ByVal Choice As Long)
        On Choice GoTo One, Two
        On Choice GoSub One, Two
One:
Two:
End Sub
''',
    "colons-in-a-date-literal": '''Private Sub First()
        Debug.Print #12:30:00 PM#: GoTo Done
Done:
End Sub
''',
    "exclusive-branches": '''Private Sub First()
#If VBA7 Then
        GoTo Modern
Modern:
#Else
        GoTo Legacy
Legacy:
#End If
End Sub
''',
}
JUMPS_INVALID = {
    "cross-procedure": ('''Private Sub First()
        GoTo Shared
End Sub

Private Sub Second()
Shared:
        Exit Sub
End Sub
''', "GoTo target 'Shared' is not a label of procedure First"),
    "duplicate-label": ('''Private Sub First()
Again:
Again:
        Exit Sub
End Sub
''', "duplicate label 'Again' in procedure First; first defined at line"),
    "jump-after-string": ('''Private Sub First()
        Debug.Print "it's ""quoted""": GoSub Missing
End Sub
''', "GoSub target 'Missing'"),
    "resume-to-missing-label": ('''Private Sub First()
        On Error GoTo Handler
        Exit Sub
Handler:
        Resume Retry
End Sub
''', "Resume target 'Retry'"),
    "label-in-other-branch": ('''Private Sub First()
#If VBA7 Then
        GoTo Legacy
#Else
Legacy:
#End If
End Sub
''', "[vba7-win32, vba7-win64]"),
    "procedure-not-closed": ("Private Sub First()\n        Exit Sub\n", "is not closed"),
    "procedure-opened-twice": ("Private Sub First()\nPrivate Sub Second()\nEnd Sub\n",
                               "is not closed before Second"),
    "stray-end": ("End Sub\n", "End statement outside any procedure"),
    "computed-jump-missing-target": ("Private Sub First(ByVal Choice As Long)\n"
                                     "        On Choice GoTo Present, Missing\nPresent:\nEnd Sub\n",
                                     "GoTo target 'Missing'"),
    "jump-after-bracketed-sheet-name": ("Private Sub First()\n"
                                        "        Debug.Print ['Sheet 1'!A1]: GoTo Lost\nEnd Sub\n",
                                        "GoTo target 'Lost'"),
    "one-line-procedure-missing-label": ("Private Sub First(): GoTo Lost: End Sub\n",
                                         "GoTo target 'Lost'"),
}


class JumpTest(unittest.TestCase):
    def test_valid_fixtures_pass(self) -> None:
        self.assertEqual(run_check(check_vba_jumps.check, VALID), [])
        for name, body in JUMPS_VALID.items():
            with self.subTest(name=name):
                self.assertEqual(run_check(check_vba_jumps.check, standalone(module(body))), [])

    def test_invalid_fixtures_fail(self) -> None:
        for name, (body, text) in JUMPS_INVALID.items():
            with self.subTest(name=name):
                findings = run_check(check_vba_jumps.check, standalone(module(body)))
                self.assertTrue(any(text in item for item in findings), findings)

    def test_counts_procedures(self) -> None:
        with repository(VALID) as root:
            _, components, procedures = check_vba_jumps.check(root)
        self.assertEqual((components, procedures), (7, 6))


API_FACADE = '''Attribute VB_Name = "CVA_Api"
Option Explicit
Public Const CVA_LIMIT As Long = 7
Private Declare PtrSafe Function Tick Lib "kernel32" () As Long
Private mStatus As Long
Public Enum CvaMode
    smFirst = 1
End Enum
Public Type CvaPair
    Left As Long
    Right As Long
End Type
Private mHidden As Long

Public Function CVA_Echo( _
    ByVal Value As Long) _
    As Long
        CVA_Echo = Value
End Function

Public Property Get CVA_Current() As Long
        CVA_Current = mStatus
End Property

Public Property Let CVA_Current(ByVal Value As Long)
        mStatus = Value
End Property

Private Sub Helper()
End Sub
'''
API_ROWS = [
    ("Const", "CVA_LIMIT", "Public Const CVA_LIMIT As Long = 7"),
    ("Enum", "CvaMode", "Public Enum CvaMode | smFirst = 1 | End Enum"),
    ("Type", "CvaPair", "Public Type CvaPair | Left As Long | Right As Long | End Type"),
    ("Function", "CVA_Echo", "Public Function CVA_Echo(ByVal Value As Long) As Long"),
    ("Property Get", "CVA_Current", "Public Property Get CVA_Current() As Long"),
    ("Property Let", "CVA_Current", "Public Property Let CVA_Current(ByVal Value As Long)"),
]


def api_inventory(rows: list[tuple[str, str, str]], extra: str = "") -> str:
    lines = ["# Supported VBA declarations"]
    for kind, name, signature in rows:
        lines += [f"CVA_Api\t{kind}\t{name}", f"# SIG\tCVA_Api\t{kind}\t{name}\t{signature}"]
    return "\n".join(lines) + "\n" + extra


def api_files(facade: str = API_FACADE, inventory: str | None = None,
              **others: str) -> dict[str, str | bytes]:
    files: dict[str, str | bytes] = {
        "src/modules/CVA_Api.bas": facade,
        "src/core/CORE_Internal.bas": 'Attribute VB_Name = "CORE_Internal"\nOption Explicit\n'
                                      "Option Private Module\nPublic Function Inside() As Long\n"
                                      "End Function\n",
        "tests/modules/TEST_Api.bas": 'Attribute VB_Name = "TEST_Api"\nOption Explicit\n'
                                      "Option Private Module\nPublic Sub RunAll()\nEnd Sub\n",
        "docs/PUBLIC_API.txt": api_inventory(API_ROWS) if inventory is None else inventory,
    }
    files.update({f"src/modules/{name}.bas": text for name, text in others.items()})
    return files


MODERN = 'Public Const CVA_HOST As String = "vba7"'
LEGACY = 'Public Const CVA_HOST As String = "vba6"'
HOST_ROW = "CVA_Api\tConst\tCVA_HOST\n"
MODERN_ROW = f"# SIG\tCVA_Api\tConst\tCVA_HOST\t{MODERN}\n"
LEGACY_ROW = f"# SIG\tCVA_Api\tConst\tCVA_HOST\t{LEGACY}\n"
CONDITIONAL = API_FACADE + f"\n#If VBA7 Then\n{MODERN}\n#Else\n{LEGACY}\n#End If\n"


class PublicApiTest(unittest.TestCase):
    def findings(self, files: Mapping[str, str | bytes]) -> list[str]:
        return run_check(check_vba_public_api.check, files)

    def assertFinding(self, files: Mapping[str, str | bytes], text: str) -> None:
        findings = self.findings(files)
        self.assertTrue(any(text in item for item in findings), findings)

    def test_valid_fixtures_pass(self) -> None:
        self.assertEqual(self.findings(VALID), [])
        self.assertEqual(self.findings(api_files()), [])

    def test_repository_inventory_matches_empty_source(self) -> None:
        inventory = (ROOT / "docs/PUBLIC_API.txt").read_text(encoding="utf-8")
        self.assertEqual(self.findings({"docs/PUBLIC_API.txt": inventory}), [])

    def test_implicit_visibility_is_rejected_everywhere(self) -> None:
        self.assertFinding(api_files(API_FACADE.replace("Public Function CVA_Echo",
                                                        "Function CVA_Echo")),
                           "implicit public procedure: CVA_Echo")
        hidden = 'Attribute VB_Name = "CORE_Implicit"\nOption Explicit\nOption Private Module\n' \
                 "Sub Hidden()\nEnd Sub\nEnum Mode\n    mA = 1\nEnd Enum\n"
        findings = self.findings({"src/core/CORE_Implicit.bas": hidden,
                                  "docs/PUBLIC_API.txt": "# None\n"})
        self.assertTrue(any("implicit public procedure: Hidden" in f for f in findings), findings)
        self.assertTrue(any("implicit public module-level declaration: Enum Mode" in f
                            for f in findings), findings)

    def test_one_identifier_per_public_statement(self) -> None:
        self.assertFinding(api_files(API_FACADE.replace("Private mHidden As Long",
                                                        "Public gFirst As Long, gOther")),
                           "Public variable statement must declare one identifier")
        self.assertFinding(api_files(API_FACADE.replace("= 7", "= 7, CVA_MORE As Long = 8")),
                           "Public Const statement must declare one identifier")

    def test_inventory_must_list_every_declaration(self) -> None:
        self.assertFinding(api_files(inventory=api_inventory(API_ROWS[1:])),
                           "public declaration not listed: CVA_Api\tConst\tCVA_LIMIT")
        rows = api_inventory(API_ROWS).replace("CVA_Api\tFunction\tCVA_Echo\n", "")
        self.assertFinding(api_files(inventory=rows), "not listed: CVA_Api\tFunction\tCVA_Echo")

    def test_signature_records(self) -> None:
        rows = api_inventory(API_ROWS).replace("(ByVal Value As Long) As Long", "() As Long")
        self.assertFinding(api_files(inventory=rows), "signature mismatch for CVA_Api\tFunction")
        missing = "\n".join(line for line in api_inventory(API_ROWS).splitlines()
                            if "SIG\tCVA_Api\tFunction" not in line) + "\n"
        self.assertFinding(api_files(inventory=missing), "signature record missing")
        duplicate = api_inventory(API_ROWS, api_inventory(API_ROWS[:1]).splitlines()[2] + "\n")
        self.assertFinding(api_files(inventory=duplicate), "duplicate signature record")
        self.assertFinding(api_files(inventory=api_inventory(API_ROWS, "# SIG\tCVA_Api\n")),
                           "malformed # SIG record")

    def test_stale_and_malformed_rows(self) -> None:
        stale = api_inventory(API_ROWS, "CVA_Api\tFunction\tGone\n"
                                        "# SIG\tCVA_Api\tFunction\tGone\tPublic Function Gone()\n")
        findings = self.findings(api_files(inventory=stale))
        self.assertTrue(any("listed declaration not in src/modules/" in f for f in findings))
        self.assertTrue(any("stale signature record" in f for f in findings))
        self.assertFinding(api_files(inventory=api_inventory(API_ROWS, "CVA_Api\tFunction\n")),
                           "needs component, kind and name")
        self.assertFinding(api_files(inventory=api_inventory(API_ROWS, "CVA_Api\tConst\tcva_limit\n")),
                           "duplicate inventory row")

    def test_only_the_facade_is_supported_api(self) -> None:
        rows = api_inventory(API_ROWS, "CORE_Internal\tFunction\tInside\n")
        self.assertFinding(api_files(inventory=rows),
                           "listed declaration not in src/modules/: CORE_Internal")

    def test_missing_inventory(self) -> None:
        files = {k: v for k, v in api_files().items() if k != "docs/PUBLIC_API.txt"}
        self.assertFinding(files, "public API inventory is missing")

    def test_collisions(self) -> None:
        twice = API_FACADE + "\nPublic Function CVA_Echo(ByVal Value As String) As String\n" \
                             "End Function\n"
        self.assertFinding(api_files(twice), "public declaration appears more than once")
        other = 'Attribute VB_Name = "CVA_Other"\nOption Explicit\n' \
                "Public Function CVA_Echo(ByVal Value As Long) As Long\nEnd Function\n"
        self.assertFinding(api_files(CVA_Other=other), "public name 'CVA_Echo' collides with "
                                                       "CVA_Api.CVA_Echo (Function)")

    def test_no_public_globals_or_declares_in_standard_modules(self) -> None:
        self.assertFinding(api_files(API_FACADE.replace("Private mHidden As Long",
                                                        "Public gState As Long")),
                           "public variable gState in a standard module")
        self.assertFinding(api_files(API_FACADE.replace("Private mHidden As Long",
                                                        "Global gState As Long")),
                           "public variable gState in a standard module")
        self.assertFinding(api_files(API_FACADE.replace("Private Declare", "Public Declare")),
                           "public Declare Tick; declare native procedures Private")
        core = 'Attribute VB_Name = "CORE_State"\nOption Explicit\nOption Private Module\n' \
               "Public gCounter As Long\n"
        self.assertFinding({"src/core/CORE_State.bas": core, "docs/PUBLIC_API.txt": "# None\n"},
                           "public variable gCounter in a standard module")
        field = CLASS.replace("Private mAmount As Double", "Public Label As String")
        self.assertEqual(self.findings({"src/classes/CCalculationResult.cls": field,
                                        "docs/PUBLIC_API.txt": "# None\n"}), [])

    def test_conditional_variants(self) -> None:
        variants = api_inventory(API_ROWS, HOST_ROW + MODERN_ROW + LEGACY_ROW)
        self.assertEqual(self.findings(api_files(CONDITIONAL, variants)), [])
        self.assertFinding(api_files(CONDITIONAL, api_inventory(API_ROWS, HOST_ROW + MODERN_ROW)),
                           "signature mismatch")
        self.assertFinding(api_files(API_FACADE + "\n" + MODERN + "\n", variants),
                           "signature mismatch")
        self.assertFinding(api_files(CONDITIONAL + MODERN + "\n", variants),
                           "appears more than once")
        dead = API_FACADE + f"\n#If False Then\n{MODERN.replace('HOST', 'DEAD')}\n#End If\n"
        self.assertEqual(self.findings(api_files(dead)), [])
        self.assertFinding(api_files(CONDITIONAL.replace("#If VBA7", "#If Unknown"), variants),
                           "indeterminate #If")

    def test_exclusive_names_across_modules(self) -> None:
        modern_only = API_FACADE + f"\n#If VBA7 Then\n{MODERN}\n#End If\n"
        legacy = f'Attribute VB_Name = "CVA_Legacy"\nOption Explicit\n#If Not VBA7 Then\n{LEGACY}\n' \
                 "#End If\n"
        rows = api_inventory(API_ROWS, HOST_ROW + MODERN_ROW + "CVA_Legacy\tConst\tCVA_HOST\n"
                             + LEGACY_ROW.replace("CVA_Api", "CVA_Legacy"))
        self.assertEqual(self.findings(api_files(modern_only, rows, CVA_Legacy=legacy)), [])
        self.assertFinding(api_files(API_FACADE + "\n" + MODERN + "\n", rows, CVA_Legacy=legacy),
                           "collides")

    def test_signatures_keep_string_literals(self) -> None:
        facade = API_FACADE.replace("Private Sub Helper()", "Public Function CVA_Pad( _\n"
                                    '    Optional ByVal Text As String = "A  ( B )") _\n'
                                    "    As String\nEnd Function\n\nPrivate Sub Helper()")
        exact = api_inventory(API_ROWS + [("Function", "CVA_Pad", 'Public Function CVA_Pad('
                                           'Optional ByVal Text As String = "A  ( B )") '
                                           "As String")])
        self.assertEqual(self.findings(api_files(facade, exact)), [])
        collapsed = exact.replace('"A  ( B )"', '"A (B)"')
        self.assertFinding(api_files(facade, collapsed), "signature mismatch for CVA_Api\tFunction"
                                                         "\tCVA_Pad")

    def test_declare_inside_a_literal_is_text(self) -> None:
        facade = API_FACADE.replace("Private Sub Helper()", "Public Function CVA_Say("
                                    'Optional ByVal Text As String = " declare ") As String\n'
                                    "End Function\n\nPrivate Sub Helper()")
        rows = api_inventory(API_ROWS + [("Function", "CVA_Say", "Public Function CVA_Say("
                                          'Optional ByVal Text As String = " declare ") As String')])
        self.assertEqual(self.findings(api_files(facade, rows)), [])

    def test_colon_separated_and_commented_statements(self) -> None:
        facade = API_FACADE.replace("Private mHidden As Long",
                                    "Private mHidden As Long: Public gExtra As Long ' note: x")
        self.assertFinding(api_files(facade), "public variable gExtra in a standard module")
        dated = API_FACADE.replace("Private mHidden As Long",
                                   "Private Const START_DATE As Date = #1/2/2026#: Rem : Public x")
        self.assertEqual(self.findings(api_files(dated)), [])


def core_module(body: str) -> str:
    return f'Attribute VB_Name = "CORE_Fixture"\nOption Explicit\nOption Private Module\n{body}'


def class_module(body: str) -> str:
    return CLASS.split("Option Explicit")[0].replace("CCalculationResult", "CFixture") + \
        f"Option Explicit\n{body}"


def example_module(body: str) -> str:
    return f'Attribute VB_Name = "ExampleFixture"\nOption Explicit\n{body}'


CORE_PATH, CLASS_PATH = "src/core/CORE_Fixture.bas", "src/classes/CFixture.cls"
EXAMPLE_PATH = "examples/modules/ExampleFixture.bas"

DEPENDENCY_VALID = {
    "pure-core": (CORE_PATH, core_module('''Private Const LIMIT As Long = 3

Private Enum Slot
    [_First] = 0
    slA = 0
End Enum

Private Type Pair
    Low As Double
    High As Double
End Type

Public Function Count(ByVal Items As Object) As Long
        ' Application, MsgBox and [A1] in a comment are not code.
        Dim Seen As Object
        Set Seen = CreateObject("Scripting.Dictionary")
        Debug.Print "Range and MsgBox inside a string"
        Count = Items.Count + Items.Rows + LIMIT
End Function
''')),
    "class-instance-state": (CLASS_PATH, class_module('''Private mTotal As Double


Public Property Get Total() As Double
        Total = mTotal
End Property


Public Property Let Total(ByVal Value As Double)
        mTotal = Value
End Property
''')),
    "example-uses-facade": (EXAMPLE_PATH, example_module('''Public Sub Run()
        Debug.Print CVA_Functions.CVA_IsPositive(1)
End Sub
''')),
    "object-calls-in-strings-are-text": (CORE_PATH, core_module('''Public Sub Work()
        Debug.Print "GetObject(", "CreateObject(""Excel.Application"")"
End Sub
''')),
    "lower-case-member-prefix-is-an-identifier": (CLASS_PATH, class_module('''Private m_Total As Double


Public Sub Add(ByVal Amount As Double)
        m_Total = m_Total + Amount
End Sub
''')),
    "single-line-if-without-io": (CORE_PATH, core_module('''Public Sub Work(ByVal Flag As Boolean)
        If Flag Then Debug.Print "Kill" Else Debug.Print "Open"
End Sub
''')),
    "ordinary-names-and-early-bound-dictionary": (CORE_PATH, core_module('''Public Function Pick(ByVal Inputs As Long, ByVal Location As Long) As String
        Dim Seen As Scripting.Dictionary
        Set Seen = New Scripting.Dictionary
100     Debug.Print Date, Inputs + Location
        Pick = VBA.Strings.Left("ab", 1)
        Call Helper(1)
End Function

Private Sub Helper(ByVal Value As Long)
End Sub
''')),
    "tests-and-facade-are-not-restricted": ("tests/modules/TEST_Fixture.bas", module('''
Public Sub RunAll()
        Debug.Print Application.Name, CORE_Validation.IsPositive(1)
End Sub
''')),
}


def in_procedure(body: str) -> str:
    return core_module(f"Public Sub Work()\n{body}\nEnd Sub\n")


DEPENDENCY_INVALID = {
    "application": (CORE_PATH, in_procedure("        Application.Run \"Macro\""),
                    "Application reaches the Excel host"),
    "msgbox": (CORE_PATH, in_procedure("        MsgBox \"x\""), "MsgBox reaches the Excel host"),
    "worksheets": (CORE_PATH, in_procedure("        Debug.Print Worksheets.Count"),
                   "Worksheets reaches the Excel host"),
    "excel-type": (CORE_PATH, in_procedure("        Dim Target As Worksheet"),
                   "As Worksheet is an Excel or UI type"),
    "qualified-excel-type": (CORE_PATH, in_procedure("        Dim Target As Excel.Range"),
                             "Excel reaches the Excel host"),
    "bracket-evaluate": (CORE_PATH, in_procedure("        Debug.Print [A1]"),
                         "evaluated by Excel"),
    "open-file": (CORE_PATH, in_procedure('        Open "data.txt" For Input As #1'),
                  "file, registry or process access"),
    "print-to-file": (CORE_PATH, in_procedure("        Print #1, 1"),
                      "file, registry or process access"),
    "environment": (CORE_PATH, in_procedure('        Debug.Print Environ("TEMP")'),
                    "file, registry or process access"),
    "shell": (CORE_PATH, in_procedure('        Debug.Print Shell("cmd")'),
              "file, registry or process access"),
    "call-by-name": (CORE_PATH, in_procedure('        Debug.Print CallByName(Me, "X", VbGet)'),
                     "CallByName: a dynamic call"),
    "evaluate": (CORE_PATH, in_procedure('        Debug.Print Evaluate("1+1")'),
                 "Evaluate: a dynamic call"),
    "create-host-object": (CORE_PATH,
                           in_procedure('        Debug.Print CreateObject("Word.Application")'),
                           "CreateObject creates an object no check can see"),
    "create-object-from-variable": (CORE_PATH,
                                    in_procedure("        Debug.Print CreateObject(ProgId)"),
                                    "CreateObject creates an object no check can see"),
    "get-object": (CORE_PATH, in_procedure('        Debug.Print GetObject(, "Excel.Sheet")'),
                   "GetObject creates an object no check can see"),
    "core-calls-facade": (CORE_PATH, in_procedure("        Debug.Print CVA_Functions.CVA_IsPositive(1)"),
                          "CVA_Functions names a facade, host, test or example component"),
    "class-calls-adapter": (CLASS_PATH, class_module("Public Sub Go()\n        M_Run.Start\nEnd Sub\n"),
                            "M_Run names a facade, host, test or example component"),
    "class-reaches-host": (CLASS_PATH, class_module("Public Sub Go()\n        Range(\"A1\").Value = 1\n"
                                                    "End Sub\n"),
                           "Range reaches the Excel host"),
    "module-level-private": (CORE_PATH, core_module("Private mCount As Long\n"),
                             "module-level variable; core holds no ambient mutable run state"),
    "module-level-dim": (CORE_PATH, core_module("Dim mCount As Long\n"), "module-level variable"),
    "static-variable": (CORE_PATH, in_procedure("        Static Calls As Long"),
                        "Static variable; core holds no run state"),
    "static-procedure": (CORE_PATH, core_module("Private Static Function Next1() As Long\n"
                                                "End Function\n"),
                         "Static procedure Next1 keeps state between calls"),
    "inactive-branch-is-read": (CORE_PATH, in_procedure("#If VBA7 Then\n        Debug.Print 1\n#Else\n"
                                                        "        MsgBox \"legacy\"\n#End If"),
                                "MsgBox reaches the Excel host"),
    "core-calls-facade-in-lower-case": (CORE_PATH, in_procedure("        Debug.Print cva_functions.Calculate(1)"),
                                        "cva_functions names a facade, host, test or example component"),
    "single-line-if-kill": (CORE_PATH, in_procedure('        If Flag Then Kill "f.txt"'),
                            "file, registry or process access"),
    "single-line-else-kill": (CORE_PATH, in_procedure('        If Flag Then Debug.Print 1 Else Kill "f.txt"'),
                              "file, registry or process access"),
    "nested-single-line-if": (CORE_PATH, in_procedure('        If A Then If B Then Open "f" For Input As #1'),
                              "file, registry or process access"),
    "block-else-on-same-line": (CORE_PATH, in_procedure('        If A Then\n        Else Kill "f.txt"\n        End If'),
                                "file, registry or process access"),
    "file-length": (CORE_PATH, in_procedure('        Debug.Print FileLen("data.txt")'),
                    "file, registry or process access"),
    "file-date": (CORE_PATH, in_procedure('        Debug.Print FileDateTime("data.txt")'),
                  "file, registry or process access"),
    "get-attributes": (CORE_PATH, in_procedure('        Debug.Print GetAttr("data.txt")'),
                       "file, registry or process access"),
    "set-attributes": (CORE_PATH, in_procedure('        SetAttr "data.txt", vbHidden'),
                       "file, registry or process access"),
    "end-of-file": (CORE_PATH, in_procedure("        Debug.Print EOF(1)"),
                    "file, registry or process access"),
    "command-line": (CORE_PATH, in_procedure("        Debug.Print Command$"),
                     "file, registry or process access"),
    "set-system-date": (CORE_PATH, in_procedure("        Date = #1/2/2026#"),
                        "file, registry or process access"),
    "unload-form": (CLASS_PATH, class_module("Public Sub Go()\n        Unload Me\nEnd Sub\n"),
                    "file, registry or process access"),
    "numbered-kill": (CORE_PATH, in_procedure('100     Kill "data.txt"'),
                      "file, registry or process access"),
    "numbered-static": (CORE_PATH, in_procedure("100     Static Calls As Long"),
                        "Static variable; core holds no run state"),
    "numbered-single-line-if": (CORE_PATH, in_procedure('100     If Flag Then Kill "data.txt"'),
                                "file, registry or process access"),
    "qualified-kill": (CORE_PATH, in_procedure('        VBA.FileSystem.Kill "data.txt"'),
                       "file, registry or process access"),
    "vba-qualified-kill": (CORE_PATH, in_procedure('        VBA.Kill "data.txt"'),
                           "file, registry or process access"),
    "qualified-shell": (CORE_PATH, in_procedure('        Debug.Print VBA.Interaction.Shell("cmd")'),
                        "file, registry or process access"),
    "qualified-msgbox": (CORE_PATH, in_procedure('        VBA.Interaction.MsgBox "x"'),
                         "MsgBox reaches the Excel host"),
    "call-save-setting": (CORE_PATH, in_procedure('        Call SaveSetting("App", "Section", "Key", "1")'),
                          "file, registry or process access"),
    "call-qualified-save-setting": (CORE_PATH, in_procedure(
        '        Call VBA.Interaction.SaveSetting("App", "Section", "Key", "1")'),
        "file, registry or process access"),
    "call-kill": (CLASS_PATH, class_module('Public Sub Go()\n        Call Kill("data.txt")\nEnd Sub\n'),
                  "file, registry or process access"),
    "call-after-then": (CORE_PATH, in_procedure('        If Flag Then Call MkDir("out")'),
                        "file, registry or process access"),
    "numbered-call": (CORE_PATH, in_procedure('100     Call FileCopy("a", "b")'),
                      "file, registry or process access"),
    "close-all-files": (CORE_PATH, in_procedure("        Close"), "file, registry or process access"),
    "close-without-hash": (CORE_PATH, in_procedure("        Close 1"), "file, registry or process access"),
    "get-without-hash": (CORE_PATH, in_procedure("        Get 1, , Value"),
                         "file, registry or process access"),
    "seek-without-hash": (CORE_PATH, in_procedure("        Seek 1, 1"), "file, registry or process access"),
    "native-declare": (CORE_PATH, core_module('Private Declare PtrSafe Function GetTickCount Lib '
                                              '"kernel32" () As Long\n'),
                       "a native Declare; core and classes call no external library"),
    "file-system-object": (CORE_PATH, in_procedure("        Dim Fso As Scripting.FileSystemObject"),
                           "Scripting.FileSystemObject is an external object model"),
    "new-file-system-object": (CLASS_PATH, class_module("Private mFso As New FileSystemObject\n"),
                               "As FileSystemObject is a file-system type"),
    "database-object-model": (CORE_PATH, in_procedure("        Dim Connection As ADODB.Connection"),
                              "ADODB.Connection is an external object model"),
    "example-behind-facade-in-lower-case": (EXAMPLE_PATH, example_module("Public Sub Run()\n"
                                                                         "        Debug.Print core_validation.IsPositive(1)\n"
                                                                         "End Sub\n"),
                                            "core_validation is behind the facade"),
    "example-behind-facade": (EXAMPLE_PATH, example_module("Public Sub Run()\n"
                                                           "        Debug.Print CORE_Validation.IsPositive(1)\n"
                                                           "End Sub\n"),
                              "CORE_Validation is behind the facade"),
}


class DependencyTest(unittest.TestCase):
    def test_valid_fixtures_pass(self) -> None:
        self.assertEqual(run_check(check_vba_dependencies.check, VALID), [])
        for name, (path, source) in DEPENDENCY_VALID.items():
            with self.subTest(name=name):
                self.assertEqual(run_check(check_vba_dependencies.check, {path: source}), [])

    def test_invalid_fixtures_fail(self) -> None:
        for name, (path, source, text) in DEPENDENCY_INVALID.items():
            with self.subTest(name=name):
                findings = run_check(check_vba_dependencies.check, {path: source})
                self.assertTrue(any(text in item for item in findings), findings)

    def test_tracked_component_names_match_in_any_case(self) -> None:
        adapter = 'Attribute VB_Name = "M_Run"\nOption Explicit\nPublic Sub Start()\nEnd Sub\n'
        files = {CLASS_PATH: class_module("Public Sub Go()\n        m_run.Start\nEnd Sub\n"),
                 "src/workbook/M_Run.bas": adapter}
        findings = run_check(check_vba_dependencies.check, files)
        self.assertTrue(any("m_run names a facade" in item for item in findings), findings)
        workbook_module = files["src/workbook/M_Run.bas"].replace("M_Run", "M_Inputs")
        hidden = {EXAMPLE_PATH: example_module("Public Sub Run()\n        m_inputs.Load\nEnd Sub\n"),
                  "src/workbook/M_Inputs.bas": workbook_module}
        findings = run_check(check_vba_dependencies.check, hidden)
        self.assertTrue(any("m_inputs is behind the facade" in item for item in findings), findings)

    def test_examples_do_not_use_model_classes(self) -> None:
        example = example_module("Public Sub Run()\n        Dim Result As New CCalculationResult\n"
                                 "        Result.Amount = 10\nEnd Sub\n")
        files = {EXAMPLE_PATH: example, "src/classes/CCalculationResult.cls": CLASS}
        findings = run_check(check_vba_dependencies.check, files)
        self.assertTrue(any("CCalculationResult is behind the facade" in item for item in findings),
                        findings)
        lower = {**files, EXAMPLE_PATH: example.replace("New CCalculationResult",
                                                        "New ccalculationresult")}
        findings = run_check(check_vba_dependencies.check, lower)
        self.assertTrue(any("ccalculationresult is behind the facade" in item for item in findings),
                        findings)
        counted = {EXAMPLE_PATH: example_module("Public Sub Run()\n        Debug.Print Count\n"
                                                "End Sub\n"),
                   "src/classes/CCalculationResult.cls": CLASS}
        self.assertEqual(run_check(check_vba_dependencies.check, counted), [])

    def test_keywords_inside_ordinary_identifiers_are_not_reported(self) -> None:
        # Every keyword the I/O, host and dynamic-call rules look for, used as
        # the start of an ordinary identifier, in each statement position.
        keywords = ("Open Kill FileCopy MkDir RmDir ChDir ChDrive SetAttr Reset SaveSetting "
                    "DeleteSetting SendKeys AppActivate Load Unload Name Close Print Input Write "
                    "Width Get Put Seek Lock Unlock Date Time Dir Shell GetSetting GetAllSettings "
                    "Environ CurDir FreeFile FileLen FileDateTime GetAttr Command FileAttr EOF LOF "
                    "Loc InputB Call Declare CallByName Evaluate AddressOf CreateObject GetObject "
                    + " ".join(check_vba_dependencies.HOST_NAMES)).split()
        body = "".join(f"        {word}Amount = 1\n        Total = {word}Amount\n"
                       f"        Call {word}Rate(1)\n        If Flag Then {word}Count = 2\n"
                       for word in keywords)
        helpers = "".join(f"Private Sub {word}Rate(ByVal Value As Long)\nEnd Sub\n" for word in keywords)
        source = core_module("Public Sub Work(ByVal Flag As Boolean)\n"
                             f"        Dim Total As Long\n{body}End Sub\n{helpers}")
        self.assertEqual(run_check(check_vba_dependencies.check, {CORE_PATH: source}), [])
        hashless = in_procedure("        Get 1, , Value\n        Get #1, , Value\n        Lock 1\n"
                                "        Unlock #1\n        Put 1, , Value")
        findings = run_check(check_vba_dependencies.check, {CORE_PATH: hashless})
        self.assertEqual(len(findings), 5, findings)

    def test_counts_only_restricted_homes(self) -> None:
        with repository(VALID) as root:
            _, components = check_vba_dependencies.check(root)
        self.assertEqual(components, 3)


class LexerTest(unittest.TestCase):
    def test_comments_end_the_code(self) -> None:
        cases = {
            "x = 1 ' note": "x = 1",
            "Rem whole line": "",
            "  Rem": "",
            "Debug.Print 1: Rem GoTo Missing": "Debug.Print 1:",
            'Debug.Print "a: Rem b"': 'Debug.Print "a: Rem b"',
            "Call Run(Remainder:=1)": "Call Run(Remainder:=1)",
            "Report Name:= Rem": "Report Name:= Rem",
            "Remove 1": "Remove 1",
            "100 Rem GoTo Missing": "100",
            "  10 x = 1 ' note": "  10 x = 1",
            "10: Rem note": "10:",
            "x = ['Sheet 1'!A1] ' note": "x = ['Sheet 1'!A1]",
            "x = [A1] ' note": "x = [A1]",
            "x = 1: Remark = 2": "x = 1: Remark = 2",
            '"it\'s": GoTo Label': '"it\'s": GoTo Label',
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(strip_code(raw), expected)
        self.assertEqual(strip_code('Debug.Print "GoTo x": GoTo y', blank_strings=True),
                         "Debug.Print         : GoTo y")
        self.assertEqual(strip_code("x = ['GoTo z'!A1]: GoTo y", blank_strings=True),
                         "x = [" + " " * len("'GoTo z'!A1") + "]: GoTo y")


class MainTest(unittest.TestCase):
    def test_every_gate_exits_0_when_valid_and_1_when_invalid(self) -> None:
        # Each gate has its own defect here: no Option Explicit, an unknown
        # #If symbol, a jump to a missing label, an implicit public function
        # and a core module that reaches the host.
        invalid = standalone(module("Private Sub First()\n        GoTo Lost\nEnd Sub\n"
                                    "Function Implicit()\nEnd Function\n#If Mac Then\n#End If\n"))
        invalid["tests/modules/TEST_Fixture.bas"] = \
            str(invalid["tests/modules/TEST_Fixture.bas"]).replace("Option Explicit\n", "")
        invalid["src/core/CORE_Fixture.bas"] = core_module(
            'Private Sub Warn()\n        MsgBox "x"\nEnd Sub\n')
        mains = (check_vba_source.main, check_vba_conditionals.main, check_vba_jumps.main,
                 check_vba_public_api.main, check_vba_dependencies.main)
        for files, expected in ((VALID, 0), (invalid, 1)):
            with repository(files) as root:
                for main in mains:
                    with self.subTest(main=main.__module__, expected=expected), \
                            contextlib.redirect_stdout(io.StringIO()) as output:
                        self.assertEqual(main(["--root", str(root)]), expected)
                        verdict = output.getvalue().splitlines()[-1]
                        self.assertIn("PASS" if expected == 0 else "FAIL", verdict)
                        self.assertIn("static check, nothing compiled or run", verdict)


if __name__ == "__main__":
    unittest.main()
