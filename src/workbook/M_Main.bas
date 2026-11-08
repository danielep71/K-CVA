Attribute VB_Name = "M_Main"
Option Explicit
' PURPOSE: Map Excel tables through CVA facade and render complete results.
' STATE: ThisWorkbook output cells only. No Application setting changes.
' ERROR POLICY: Outputs are cleared first; failures are visible on Checks.
' Cleanup errors propagate; no failed operation is labelled successful.
' UPDATED: 2026-11-08. Inputs and output contracts: docs/contracts/PROTOTYPE.md.

Private Function ReadTable(ByVal SheetName As String) As Variant
    Dim Table As ListObject, Values As Variant, Result() As Variant
    Dim i As Long, j As Long, n As Long, Used As Boolean
    Set Table = ThisWorkbook.Worksheets(SheetName).ListObjects(1)
    If Table.DataBodyRange Is Nothing Then Exit Function
    Values = Table.DataBodyRange.Value2
    For i = 1 To UBound(Values, 1)
        Used = False
        For j = 1 To UBound(Values, 2)
            If IsError(Values(i, j)) Then
                Used = True
            ElseIf Not IsEmpty(Values(i, j)) Then
                If Len(CStr(Values(i, j))) > 0 Then Used = True
            End If
        Next j
        If Used Then n = n + 1
    Next i
    If n = 0 Then Exit Function
    ReDim Result(1 To n, 1 To UBound(Values, 2))
    n = 0
    For i = 1 To UBound(Values, 1)
        Used = False
        For j = 1 To UBound(Values, 2)
            If IsError(Values(i, j)) Then
                Used = True
            ElseIf Not IsEmpty(Values(i, j)) Then
                If Len(CStr(Values(i, j))) > 0 Then Used = True
            End If
        Next j
        If Used Then
            n = n + 1
            For j = 1 To UBound(Values, 2)
                Result(n, j) = Values(i, j)
            Next j
        End If
    Next i
    ReadTable = Result
End Function

Private Sub WriteDetail(ByVal SheetName As String, ByVal Data As Variant)
    Dim Target As Range
    If IsEmpty(Data) Then Exit Sub
    Set Target = ThisWorkbook.Worksheets(SheetName).Range("C7").Resize(UBound(Data, 1), UBound(Data, 2))
    Target.Value2 = Data
    Target.Font.Name = "Aptos": Target.Font.Size = 10
    Target.NumberFormat = "#,##0.00;(#,##0.00);-"
    Target.Columns(1).NumberFormat = "@"
    If SheetName = "CounterpartyCalc" Or SheetName = "NettingSetCalc" Or SheetName = "HedgeCalc" Then Target.Columns(2).NumberFormat = "@"
    Select Case SheetName
        Case "CounterpartyCalc": Target.Columns(3).NumberFormat = "0.00%"
        Case "NettingSetCalc": Target.Columns(5).NumberFormat = "0.000000": Target.Columns(6).NumberFormat = "0.00%"
        Case "HedgeCalc": Target.Columns(3).NumberFormat = "0.00%": Target.Columns(4).NumberFormat = "0.00%": Target.Columns(5).NumberFormat = "0.000000"
        Case "IndexCalc": Target.Columns(4).NumberFormat = "0.00%": Target.Columns(5).NumberFormat = "0.000000"
    End Select
End Sub

Public Sub ClearOutputs()
    Dim Name As Variant, Sheet As Worksheet
    For Each Name In Array("CounterpartyCalc", "NettingSetCalc", "HedgeCalc", "IndexCalc", "Checks")
        Set Sheet = ThisWorkbook.Worksheets(CStr(Name))
        If Sheet.UsedRange.Row + Sheet.UsedRange.Rows.Count > 7 Then
            Sheet.Range("C7:K" & (Sheet.UsedRange.Row + Sheet.UsedRange.Rows.Count)).ClearContents
        End If
    Next Name
    ThisWorkbook.Worksheets("Results").Range("E7:E12").ClearContents
    ThisWorkbook.Worksheets("Results").Range("C4").Value2 = "NOT RUN - inputs may have changed."
End Sub

Private Sub CheckParameters()
    Dim P As Worksheet, V As Variant
    Set P = ThisWorkbook.Worksheets("Params")
    V = P.Range("E7").Value2
    If IsError(V) Or IsEmpty(V) Then Err.Raise vbObjectError + 2048, "M_Main", "Calculation date required."
    If Not IsNumeric(V) Then Err.Raise vbObjectError + 2048, "M_Main", "Calculation date must be an Excel date."
    If CDbl(V) < CDbl(DateSerial(2025, 1, 1)) Or CDbl(V) > CDbl(DateSerial(2026, 12, 31)) Then Err.Raise vbObjectError + 2049, "M_Main", "Prototype supports dates from 2025-01-01 through 2026-12-31."
    V = P.Range("E8").Value2
    If IsError(V) Then Err.Raise vbObjectError + 2048, "M_Main", "Currency error."
    If Len(CStr(V)) <> 3 Or CStr(V) Like "*[!A-Z]*" Then Err.Raise vbObjectError + 2048, "M_Main", "Enter a three-letter uppercase reporting currency."
    If P.Range("E9").Value2 <> "Y" Then Err.Raise vbObjectError + 2048, "M_Main", "Confirm all amounts are already in reporting currency."
End Sub

Private Function Execute(ByVal ValidateOnly As Boolean) As String
    Dim R As Variant, Message As String, ErrorNumber As Long
    On Error GoTo Failed
    ClearOutputs
    CheckParameters
    R = CVA_Functions.CVA_Calculate(ReadTable("Counterparties"), ReadTable("NettingSets"), ReadTable("SingleNameHedges"), ReadTable("IndexHedges"), ReadTable("IndexConstituents"))
    If ValidateOnly Then
        ThisWorkbook.Worksheets("Results").Range("C4").Value2 = "VALIDATED - press Run CVA to write results."
    Else
        WriteDetail "CounterpartyCalc", R(0)
        WriteDetail "NettingSetCalc", R(1)
        WriteDetail "HedgeCalc", R(2)
        WriteDetail "IndexCalc", R(3)
        With ThisWorkbook.Worksheets("Results")
            .Range("E7").Value2 = R(4)
            .Range("E8").Value2 = R(5)
            .Range("E9").Value2 = R(7)
            .Range("E10").Value2 = R(6)
            .Range("E11").Value2 = ThisWorkbook.Worksheets("Params").Range("E8").Value2
            .Range("E12").Value = Now
            .Range("C4").Value2 = "CALCULATED - prototype. Review Checks and calculation detail."
        End With
    End If
    With ThisWorkbook.Worksheets("Checks")
        .Range("C7").Value2 = "INFO"
        .Range("D7").Value2 = "All input tables"
        .Range("E7").Value2 = "Input validation passed. Scope, classifications, maturities and hedge eligibility remain caller responsibilities."
    End With
    Execute = "OK"
    Exit Function
Failed:
    ErrorNumber = Err.Number: Message = Err.Description
    ClearOutputs
    ThisWorkbook.Worksheets("Results").Range("C4").Value2 = "FAILED - no capital result. See Checks."
    ThisWorkbook.Worksheets("Checks").Range("C7").Value2 = "ERROR"
    ThisWorkbook.Worksheets("Checks").Range("D7").Value2 = ErrorNumber
    ThisWorkbook.Worksheets("Checks").Range("E7").Value2 = Message
    Execute = "FAILED: " & Message
End Function

Public Sub RunCVA()
    Dim Outcome As String
    Outcome = Execute(False)
    ThisWorkbook.Worksheets("Results").Activate
End Sub

Public Function RunCVA_Silent() As String
    RunCVA_Silent = Execute(False)
End Function

Public Sub ValidateInputs()
    Dim Outcome As String
    Outcome = Execute(True)
    ThisWorkbook.Worksheets("Checks").Activate
End Sub

Public Sub InstallButtons()
    Dim Sheet As Worksheet, Button As Shape, Item As Variant, i As Long
    Dim MacroNames As Variant
    Set Sheet = ThisWorkbook.Worksheets("README")
    MacroNames = Array("RunCVA", "ValidateInputs", "ClearOutputs", "RunPrototypeTests")
    For i = Sheet.Shapes.Count To 1 Step -1
        If Left$(Sheet.Shapes(i).Name, 11) = "CVA_Button_" Then Sheet.Shapes(i).Delete
    Next i
    i = 0
    For Each Item In Array("Run CVA", "Validate inputs", "Clear outputs", "Run tests")
        Set Button = Sheet.Shapes.AddShape(5, 40 + i * 160, 105, 150, 28)
        Button.Name = "CVA_Button_" & CStr(i)
        Button.TextFrame.Characters.Text = CStr(Item)
        Button.Fill.ForeColor.RGB = RGB(31, 56, 100)
        Button.TextFrame.Characters.Font.Color = RGB(255, 255, 255)
        Button.OnAction = "'" & Replace(ThisWorkbook.Name, "'", "''") & "'!" & MacroNames(i)
        i = i + 1
    Next Item
End Sub
