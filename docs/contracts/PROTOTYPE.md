# Input and output contract

> Ported intake document (#180). Describes the unvalidated prototype; source claims
> are retained for review, not adopted as regulatory or runtime acceptance.
> See [porting record](../prototype/PORTING.md).

The facade `CVA_Functions.CVA_Calculate(CP, NS, SN, IX, IC)` accepts one-based,
rectangular, two-dimensional Variant arrays. `Empty` denotes an empty optional
hedge or constituent table. No Excel object is passed to the core.

| Table | Columns in order |
|---|---|
| CP | CounterpartyID, Name, Sector, Quality |
| NS | NettingSetID, CounterpartyID, EAD, MaturityYears, IMM, InScope |
| SN | HedgeID, CounterpartyID, ReferenceSector, ReferenceQuality, MaturityYears, Notional, Relationship, Eligible |
| IX | IndexID, WeightedMaturityYears, FullNotional, Eligible |
| IC | IndexID, ConstituentID, Sector, Quality, Weight |

IDs are trimmed nonempty strings, matched case-insensitively. Each entity ID
is unique within its table; constituent IDs are unique within each index.
Codes are uppercase and exact. Credit quality is CQS1_3, CQS4_6 or UNRATED.
Sector is SOV/PSE/FIN/IND/CONS/TECH/HEALTH/OTHER; see Params for definitions.
Numeric strings, Boolean values and blanks are rejected as numbers. EAD may
be zero; maturity, hedge notional and constituent weight must be positive.
IMM is Y/N. InScope and Eligible must be Y. Constituent weights sum to 1
within 1e-10; weights are not silently normalised. Every CP has at least one
NS. All foreign keys must resolve. Entirely blank Excel table rows are ignored;
partly populated rows are validated and cannot disappear silently.

The caller supplies EAD including collateral, effective maturity following
Article 162 as modified by Article 384, correct classifications, only in-scope
transactions and eligible hedges. All amounts use the same reporting currency
and scale of one currency unit. No FX conversion or statutory maturity cap is
computed. Same-index positions must be pre-aggregated using full notional and
notional-weighted residual maturity; the core discounts that aggregate maturity.

The returned zero-based array has: 0 counterparty detail, 1 netting-set detail,
2 single-name detail, 3 index detail, 4 U, 5 H before DS, 6 capital, 7 IH.
Detail arrays are one-based; their columns match the workbook output headers.
Empty optional details return Empty. No partial result is returned on error.
Validation raises vbObjectError+2048. Excel date-window rejection uses +2049.
Unexpected numerical/host errors propagate to the adapter and are reported as
FAILED; no successful-looking zero is substituted.

The adapter checks the calculation date (2025–2026), reporting-currency syntax
and single-currency confirmation. It reports the first error on Checks and
clears old output before each operation. Workbook_SheetChange invalidates
results on input edits. No global Excel application state is changed. A failed
output cleanup is a host error that propagates, not a successful run. Tables
can be extended using native Excel table insertion; cells outside tables are
not input records. The prototype is intended for small review portfolios.
