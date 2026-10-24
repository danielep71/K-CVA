Attribute VB_Name = "TEST_DefectProbe"
Option Explicit
Option Private Module

' Temporary #13 enforcement probe: GoTo names a label this procedure
' does not define, so vba-jumps must fail. Removed before merge.
Private Sub Probe()
        GoTo Missing
End Sub
