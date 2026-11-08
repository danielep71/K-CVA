Attribute VB_Name = "CORE_BACVA"
Option Explicit
Option Private Module

' PURPOSE: Pure CRR Article 384 calculation and strict prototype validation.
' INPUTS: One-based 2D Variant arrays; Empty means no records. Amounts are
' unscaled in one reporting currency, maturity in years, weights as decimals.
' RETURNS: Array(counterparty detail, netting detail, hedge detail, index detail,
' unhedged capital, hedged component before DS, final capital, index offset).
' ERROR POLICY: Invalid inputs raise ERR_INPUT; no partial result is returned.
' DEPENDENCIES: VBA only. STATE OWNERSHIP: Local variables only.
' REFERENCE: CRR 26.06.2026, Article 384(1)-(3), printed pp.611-615.
' UPDATED: 2026-11-08. Prototype, not a certified regulatory implementation.
Private Const ERR_INPUT As Long = vbObjectError + 2048
Private Const ALPHA As Double = 1.4
Private Const RHO As Double = 0.5
Private Const DS As Double = 0.65
Private Const BETA As Double = 0.25

Public Function Discount(ByVal Maturity As Double) As Double
    ' Article 384(2), p.613. Series avoids cancellation near zero.
    Dim X As Double
    If Maturity <= 0 Then Reject "Maturity must be positive."
    X = 0.05 * Maturity
    If X < 0.00001 Then
        Discount = 1 - X / 2 + X * X / 6 - X * X * X / 24
    Else
        Discount = (1 - Exp(-X)) / X
    End If
End Function

Public Function RiskWeight(ByVal Sector As String, ByVal Quality As String) As Double
    ' Article 384 Table 1, p.614. CQS1_3; CQS4_6 or UNRATED.
    Dim HighQuality As Boolean
    If Quality <> "CQS1_3" And Quality <> "CQS4_6" And Quality <> "UNRATED" Then Reject "Invalid credit quality."
    HighQuality = (Quality = "CQS1_3")
    Select Case Sector
        Case "SOV": If HighQuality Then RiskWeight = 0.005 Else RiskWeight = 0.02
        Case "PSE": If HighQuality Then RiskWeight = 0.01 Else RiskWeight = 0.04
        Case "FIN", "OTHER": If HighQuality Then RiskWeight = 0.05 Else RiskWeight = 0.12
        Case "IND": If HighQuality Then RiskWeight = 0.03 Else RiskWeight = 0.07
        Case "CONS": If HighQuality Then RiskWeight = 0.03 Else RiskWeight = 0.085
        Case "TECH": If HighQuality Then RiskWeight = 0.02 Else RiskWeight = 0.055
        Case "HEALTH": If HighQuality Then RiskWeight = 0.015 Else RiskWeight = 0.05
        Case Else: Reject "Invalid sector code."
    End Select
End Function

Private Sub Reject(ByVal Message As String)
    Err.Raise ERR_INPUT, "CORE_BACVA", Message
End Sub

Private Function CountRows(ByVal Data As Variant) As Long
    If IsEmpty(Data) Then Exit Function
    If Not IsArray(Data) Then Reject "Expected a table array."
    CountRows = UBound(Data, 1)
End Function

Private Function Number(ByVal Value As Variant, ByVal Label As String, ByVal AllowZero As Boolean) As Double
    If IsError(Value) Or IsEmpty(Value) Or IsNull(Value) Then Reject Label & ": number required."
    Select Case VarType(Value)
        Case vbByte, vbInteger, vbLong, vbSingle, vbDouble, vbCurrency, vbDecimal
        Case Else: Reject Label & ": typed numeric value required."
    End Select
    Number = CDbl(Value)
    If Number < 0 Then Reject Label & ": negative value."
    If Not AllowZero And Number = 0 Then Reject Label & ": positive value required."
End Function

Private Function Text(ByVal Value As Variant) As String
    If IsError(Value) Or IsNull(Value) Or IsEmpty(Value) Then Reject "Required text is missing."
    If VarType(Value) <> vbString Then Reject "Expected text code or identifier."
    Text = Trim$(CStr(Value))
    If Len(Text) = 0 Then Reject "Blank text or identifier."
End Function

Private Function FindID(ByVal Data As Variant, ByVal ID As String) As Long
    Dim i As Long
    For i = 1 To CountRows(Data)
        If StrComp(Text(Data(i, 1)), ID, vbTextCompare) = 0 Then
            FindID = i
            Exit Function
        End If
    Next i
    Reject "Unknown identifier: " & ID
End Function

Private Sub UniqueIDs(ByVal Data As Variant)
    Dim i As Long, j As Long, ID As String
    For i = 1 To CountRows(Data)
        ID = Text(Data(i, 1))
        For j = 1 To i - 1
            If StrComp(ID, Text(Data(j, 1)), vbTextCompare) = 0 Then Reject "Duplicate identifier: " & ID
        Next j
    Next i
End Sub

Public Function Calculate(ByVal CP As Variant, ByVal NS As Variant, ByVal SN As Variant, ByVal IX As Variant, ByVal IC As Variant) As Variant
    Dim NC As Long, NN As Long, NH As Long, NI As Long
    Dim i As Long, j As Long, k As Long, M As Double, N As Double, DF As Double
    Dim RW As Double, Corr As Double, H As Double, Weight As Double, WeightSum As Double
    Dim SumS As Double, SumS2 As Double, SumD As Double, SumD2 As Double
    Dim SumHMA As Double, IH As Double, KU As Double, KH As Double, Total As Double
    Dim COut() As Variant, NOut() As Variant, HOut As Variant, IOut As Variant
    Dim Seen() As Long, Relation As String, Residual As Double
    NC = CountRows(CP): NN = CountRows(NS): NH = CountRows(SN): NI = CountRows(IX)
    If NC = 0 Or NN = 0 Then Reject "At least one counterparty and netting set are required."
    UniqueIDs CP: UniqueIDs NS: UniqueIDs SN: UniqueIDs IX
    ReDim COut(1 To NC, 1 To 7)
    ReDim NOut(1 To NN, 1 To 7)
    ReDim Seen(1 To NC)
    If NH > 0 Then ReDim HOut(1 To NH, 1 To 7)
    If NI > 0 Then ReDim IOut(1 To NI, 1 To 6)
    For i = 1 To NC
        COut(i, 1) = Text(CP(i, 1))
        COut(i, 2) = Text(CP(i, 2))
        COut(i, 3) = RiskWeight(Text(CP(i, 3)), Text(CP(i, 4)))
        COut(i, 4) = 0#: COut(i, 5) = 0#: COut(i, 6) = 0#: COut(i, 7) = 0#
    Next i
    For i = 1 To NN
        j = FindID(CP, Text(NS(i, 2)))
        Seen(j) = Seen(j) + 1
        N = Number(NS(i, 3), "EAD", True)
        M = Number(NS(i, 4), "Netting-set maturity", False)
        Select Case Text(NS(i, 5))
            Case "Y": DF = 1
            Case "N": DF = Discount(M)
            Case Else: Reject "IMM must be Y or N."
        End Select
        If Text(NS(i, 6)) <> "Y" Then Reject "Confirm Article 382 scope for every netting set."
        H = COut(j, 3) * M * N * DF / ALPHA
        COut(j, 4) = COut(j, 4) + H
        NOut(i, 1) = Text(NS(i, 1)): NOut(i, 2) = Text(NS(i, 2))
        NOut(i, 3) = N: NOut(i, 4) = M: NOut(i, 5) = DF
        NOut(i, 6) = COut(j, 3): NOut(i, 7) = H
    Next i
    For i = 1 To NC
        If Seen(i) = 0 Then Reject "Counterparty without a netting set."
    Next i
    For i = 1 To NH
        j = FindID(CP, Text(SN(i, 2)))
        RW = RiskWeight(Text(SN(i, 3)), Text(SN(i, 4)))
        M = Number(SN(i, 5), "Single-name maturity", False)
        N = Number(SN(i, 6), "Single-name notional", False)
        Relation = Text(SN(i, 7))
        Select Case Relation
            Case "DIRECT": Corr = 1
            Case "RELATED": Corr = 0.8
            Case "SECTOR": Corr = 0.5
            Case Else: Reject "Invalid Article 386(3)(a) relationship."
        End Select
        If Text(SN(i, 8)) <> "Y" Then Reject "Hedge eligibility must be confirmed."
        DF = Discount(M): H = RW * M * N * DF
        COut(j, 5) = COut(j, 5) + Corr * H
        COut(j, 6) = COut(j, 6) + (1 - Corr * Corr) * H * H
        HOut(i, 1) = Text(SN(i, 1)): HOut(i, 2) = Text(SN(i, 2))
        HOut(i, 3) = RW: HOut(i, 4) = Corr: HOut(i, 5) = DF
        HOut(i, 6) = Corr * H: HOut(i, 7) = (1 - Corr * Corr) * H * H
    Next i
    ' Validate all constituents, including orphan rows, before aggregation.
    For i = 1 To CountRows(IC)
        j = FindID(IX, Text(IC(i, 1)))
        RW = RiskWeight(Text(IC(i, 3)), Text(IC(i, 4)))
        Weight = Number(IC(i, 5), "Constituent weight", False)
        If Weight > 1 Then Reject "Constituent weight exceeds 1."
        For k = 1 To i - 1
            If StrComp(Text(IC(k, 1)), Text(IC(i, 1)), vbTextCompare) = 0 And StrComp(Text(IC(k, 2)), Text(IC(i, 2)), vbTextCompare) = 0 Then Reject "Duplicate index constituent."
        Next k
        Relation = Text(IC(i, 2))
    Next i
    For i = 1 To NI
        M = Number(IX(i, 2), "Index maturity", False)
        N = Number(IX(i, 3), "Index notional", False)
        If Text(IX(i, 4)) <> "Y" Then Reject "Index eligibility must be confirmed."
        WeightSum = 0: RW = 0
        For j = 1 To CountRows(IC)
            If StrComp(Text(IC(j, 1)), Text(IX(i, 1)), vbTextCompare) = 0 Then
                Weight = Number(IC(j, 5), "Constituent weight", False)
                WeightSum = WeightSum + Weight
                RW = RW + Weight * RiskWeight(Text(IC(j, 3)), Text(IC(j, 4)))
            End If
        Next j
        If Abs(WeightSum - 1) > 0.0000000001 Then Reject "Index constituent weights must sum to 1."
        RW = RW * 0.7: DF = Discount(M): H = RW * M * N * DF
        IH = IH + H
        IOut(i, 1) = Text(IX(i, 1)): IOut(i, 2) = M: IOut(i, 3) = N
        IOut(i, 4) = RW: IOut(i, 5) = DF: IOut(i, 6) = H
    Next i
    For i = 1 To NC
        H = COut(i, 4): Residual = H - COut(i, 5)
        COut(i, 7) = Residual
        SumS = SumS + H: SumS2 = SumS2 + H * H
        SumD = SumD + Residual: SumD2 = SumD2 + Residual * Residual
        SumHMA = SumHMA + COut(i, 6)
    Next i
    KU = DS * Sqr((RHO * SumS) ^ 2 + (1 - RHO ^ 2) * SumS2)
    KH = Sqr((RHO * SumD - IH) ^ 2 + (1 - RHO ^ 2) * SumD2 + SumHMA)
    If NH + NI = 0 Then
        Total = KU
    Else
        Total = BETA * KU + DS * (1 - BETA) * KH
    End If
    Calculate = Array(COut, NOut, HOut, IOut, KU, KH, Total, IH)
End Function
