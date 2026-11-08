VERSION 1.0 CLASS
BEGIN
  MultiUse = -1
END
Attribute VB_Name = "ThisWorkbook"
Attribute VB_PredeclaredId = True
Option Explicit
' Invalidate results whenever inputs are edited; do not change Excel globals.
Private Sub Workbook_SheetChange(ByVal Sh As Object, ByVal Target As Range)
    Select Case Sh.Name
        Case "Params", "Counterparties", "NettingSets", "SingleNameHedges", "IndexHedges", "IndexConstituents"
            M_Main.ClearOutputs
    End Select
End Sub
