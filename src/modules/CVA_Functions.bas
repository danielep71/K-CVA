Attribute VB_Name = "CVA_Functions"
Option Explicit
' PURPOSE: Public facade for the prototype. No Excel state is mutated.
' INPUTS/RETURNS: See docs/contracts/PROTOTYPE.md. Errors propagate, never become zero.
' REFERENCE: CRR Article 384, pp.611-615. UPDATED: 2026-11-08.
Public Function CVA_Calculate(ByVal CP As Variant, ByVal NS As Variant, ByVal SN As Variant, ByVal IX As Variant, ByVal IC As Variant) As Variant
    CVA_Calculate = CORE_BACVA.Calculate(CP, NS, SN, IX, IC)
End Function

Public Function CVA_Discount(ByVal Maturity As Double) As Double
    CVA_Discount = CORE_BACVA.Discount(Maturity)
End Function

Public Function CVA_RiskWeight(ByVal Sector As String, ByVal Quality As String) As Double
    CVA_RiskWeight = CORE_BACVA.RiskWeight(Sector, Quality)
End Function
