# BA-CVA prototype methodology

> Ported intake document (#180). Describes the unvalidated prototype; source claims
> are retained for review, not adopted as regulatory or runtime acceptance.
> See [porting record](../prototype/PORTING.md).

Basis: K-CVA's registered CRR 26 June 2026, Article 384, printed pages
611–615. Source: https://publications.europa.eu/resource/celex/02013R0575-20260626
The formulas were read from the repository PDF page images, including the
formulas absent from the PDF text layer. This is the fixed prototype regime;
no claim is made that every later amendment is incorporated.

For each counterparty c:

- DF(M) = (1 − exp(−0.05 M))/(0.05 M). For IMM netting sets only, DF = 1.
- SCVA(c) = RW(c)/1.4 × sum_NS[M × EAD × DF].
- H(h) = RW(h) × M(h) × N(h) × DF(h).
- SNH(c) = sum_h[r(h,c) × H(h)].
- HMA(c) = sum_h[(1 − r(h,c)^2) × H(h)^2].
- IH = sum_index[RW(index) × M(index) × N(index) × DF(index)].
- RW(index) = 0.7 × sum_constituents[weight × RW(constituent)].

With rho=0.5, DS=0.65, beta=0.25:

- U = DS × sqrt[(rho × sum SCVA)^2 + (1 − rho^2) × sum SCVA^2].
- H = sqrt[(rho × sum(SCVA − SNH) − IH)^2
  + (1 − rho^2) × sum(SCVA − SNH)^2 + sum HMA].
- No eligible hedge rows: capital = U, Article 384(1)(b)/(3).
- One or more eligible hedge rows: capital = beta × U + DS × (1 − beta) × H,
  Article 384(1)(a)/(2). DS is not applied a second time to U.

No exposure or hedge intermediate is rounded. Negative residuals caused by
overhedging are retained inside the formula, not floored away. HMA has units
of currency squared. Capital has units of reporting currency.

Table 1 risk weights and Table 2 correlations are transcribed in CORE_BACVA
and shown on Params. DIRECT/RELATED/SECTOR encode the three relationships
under Article 386(3)(a)(i)/(ii)/(iii); the caller must establish eligibility.
No automatic hedge-eligibility or transaction-scope decision is made.

The independent reference uses Decimal with 50-digit precision, exponential
DF, and pairwise covariance: sum(x²)+2 rho² sum_(i<j)(xi xj), instead of the
engine's systematic/idiosyncratic aggregation. Cases are synthetic analytical
checks, not third-party or published benchmark validation.

Prototype implementation choices for previously open K-CVA decisions:
one reporting currency; supplied EAD/maturity; explicit caller attestations;
positive protection-bought hedge notionals; one pre-aggregated index row;
all-or-nothing portfolio failure; strict typed input; no automatic rating
mapping. These choices apply to this standalone prototype and do not close
repository methodology decisions or establish production acceptance.
