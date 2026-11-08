Attribute VB_Name = "TEST_Prototype"
Option Explicit
Option Private Module
' PURPOSE: Execute numerical and rejection cases against the actual VBA facade.
' REFERENCE: docs/methodology/PROTOTYPE.md; decimal reference uses pairwise covariance.
' STATE: TestCatalogue actual/result cells only. UPDATED: 2026-11-08.
Private Function Rows(ParamArray Items() As Variant) As Variant
    Dim Result() As Variant, i As Long, j As Long, Item As Variant
    Item = Items(0)
    ReDim Result(1 To UBound(Items) + 1, 1 To UBound(Item) + 1)
    For i = 0 To UBound(Items)
        Item = Items(i)
        For j = 0 To UBound(Item)
            Result(i + 1, j + 1) = Item(j)
        Next j
    Next i
    Rows = Result
End Function

Private Sub CheckCase(ByVal RowNumber As Long, ByVal Expected As Variant, ByVal CP As Variant, ByVal NS As Variant, ByVal SN As Variant, ByVal IX As Variant, ByVal IC As Variant)
    Dim R As Variant, Actual As Variant, Passed As Boolean
    On Error GoTo Failed
    R = CVA_Functions.CVA_Calculate(CP, NS, SN, IX, IC)
    Actual = R(6)
    If IsNumeric(Expected) Then Passed = (Abs(CDbl(Actual) - CDbl(Expected)) <= 0.000001)
    GoTo Record
Failed:
    Actual = "ERROR " & CStr(Err.Number)
    If VarType(Expected) = vbString Then Passed = (Err.Number = vbObjectError + 2048)
Record:
    With ThisWorkbook.Worksheets("TestCatalogue")
        .Cells(RowNumber, 6).Value2 = Actual
        If Passed Then .Cells(RowNumber, 7).Value2 = "PASS" Else .Cells(RowNumber, 7).Value2 = "FAIL"
    End With
End Sub

Public Sub RunPrototypeTests()
    Dim CP As Variant, NS As Variant, SN As Variant, IX As Variant, IC As Variant
    Dim OneCP As Variant, OneNS As Variant, Bad As Variant, None As Variant
    CP = Rows(Array("BANK", "Bank A", "FIN", "CQS1_3"), Array("TECH", "Technology B", "TECH", "CQS1_3"))
    NS = Rows(Array("NS1", "BANK", 10000000#, 3#, "N", "Y"), Array("NS2", "TECH", 5000000#, 2#, "Y", "Y"))
    OneCP = Rows(Array("BANK", "Bank A", "FIN", "CQS1_3"))
    OneNS = Rows(Array("NS1", "BANK", 10000000#, 3#, "N", "Y"))
    SN = Rows(Array("H1", "BANK", "FIN", "CQS1_3", 3#, 2000000#, "DIRECT", "Y"))
    IX = Rows(Array("IDX1", 4#, 1000000#, "Y"))
    IC = Rows(Array("IDX1", "NAME1", "FIN", "CQS1_3", 0.6), Array("IDX1", "NAME2", "TECH", "CQS1_3", 0.4))
    CheckCase 7, 646712.966597946, OneCP, OneNS, None, None, None
    CheckCase 8, 675933.479943836, CP, NS, None, None, None
    CheckCase 9, 541768.486384413, CP, NS, SN, None, None
    SN(1, 7) = "RELATED"
    CheckCase 10, 576737.626095336, CP, NS, SN, None, None
    SN(1, 7) = "SECTOR"
    CheckCase 11, 624181.91889178, CP, NS, SN, None, None
    CheckCase 12, 651820.772324365, CP, NS, None, IX, IC
    SN(1, 7) = "RELATED"
    CheckCase 13, 553046.965386535, CP, NS, SN, IX, IC
    Bad = Rows(Array("NS1", "BANK", 10000000#, 3#, "N", "Y"), Array("NS2", "TECH", 5000000#, 2#, "Y", "Y"), Array("NS3", "BANK", 10000000#, 3#, "N", "Y"))
    CheckCase 14, 1319706.41127874, CP, Bad, None, None, None
    Bad = OneNS: Bad(1, 3) = 0#
    CheckCase 15, 0, OneCP, Bad, None, None, None
    SN(1, 7) = "DIRECT": SN(1, 6) = 20000000#
    CheckCase 16, 1027288.08357717, CP, NS, SN, None, None
    Bad = NS: Bad(1, 3) = Empty
    CheckCase 17, "INVALID INPUT", CP, Bad, None, None, None
    Bad = NS: Bad(1, 3) = -1#
    CheckCase 18, "INVALID INPUT", CP, Bad, None, None, None
    Bad = NS: Bad(1, 4) = 0#
    CheckCase 19, "INVALID INPUT", CP, Bad, None, None, None
    Bad = NS: Bad(2, 1) = "NS1"
    CheckCase 20, "INVALID INPUT", CP, Bad, None, None, None
    Bad = NS: Bad(1, 2) = "UNKNOWN"
    CheckCase 21, "INVALID INPUT", CP, Bad, None, None, None
    Bad = CP: Bad(1, 3) = "UNKNOWN"
    CheckCase 22, "INVALID INPUT", Bad, NS, None, None, None
    Bad = IC: Bad(1, 5) = 0.5
    CheckCase 23, "INVALID INPUT", CP, NS, None, IX, Bad
    Bad = SN: Bad(1, 8) = "N"
    CheckCase 24, "INVALID INPUT", CP, NS, Bad, None, None
    Bad = NS: Bad(1, 3) = "10000000"
    CheckCase 25, "INVALID INPUT", CP, Bad, None, None, None
    Bad = IC: Bad(1, 1) = "UNKNOWN"
    CheckCase 26, "INVALID INPUT", CP, NS, None, IX, Bad
    Bad = IC: Bad(2, 2) = "NAME1"
    CheckCase 27, "INVALID INPUT", CP, NS, None, IX, Bad
    Bad = NS: Bad(1, 6) = "N"
    CheckCase 28, "INVALID INPUT", CP, Bad, None, None, None
End Sub
