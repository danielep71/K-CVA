# Methodology

This directory records **what MKT-K-CVA will implement and on what authority**:
the controlling text and its dates, the source register, the approaches and
their CRR articles, the inputs they need, the assumptions and open decisions,
and the trace from each rule to its formula, code and tests. The numerical
test-case contract is in [TEST_CASES.md](TEST_CASES.md); copies of the texts
relied on are in [sources/](sources/README.md). The structure is adapted from
CCR-K-SFTs's `docs/methodology/` (see [NOTICE.md](../../NOTICE.md)); none of
its SFT methods, sources or values applies here.

> [!IMPORTANT]
> **Status on 2026-10-24: skeleton only.** The regulatory basis, the
> approaches, the version in force and the source register are recorded. No
> formula, parameter, risk weight or table is transcribed, implemented or
> validated. The product targets regulatory CVA capital only
> ([DECISIONS.md](../DECISIONS.md) A1); economic or accounting CVA is out of
> scope.

<a id="regulatory-basis"></a>

## Regulatory basis

Decided by the maintainer on 2026-10-24 in
[#8](https://github.com/danielep71/MKT-K-CVA/issues/8)
([DECISIONS.md](../DECISIONS.md) M1).

| Role | Source | Use |
| --- | --- | --- |
| **Controlling** | Regulation (EU) No 575/2013 (CRR), incorporating the amendments of Regulation (EU) 2024/1623 (CRR3) | The calculation specification. Every implemented rule cites a CRR article and paragraph |

No other regime is a calculation source. The Basel Framework is not
registered: the maintainer chose the EU CRR alone as the basis. EBA products
(regulatory technical standards, guidelines, Q&As) are registered with their
own role only when a rule relies on one.

### CRR provisions

Part Three, Title VI *Own funds requirements for credit valuation adjustment
risk*, as replaced or amended by CRR3 Article 1, points (197) to (202).
Printed pages are those of the registered consolidated text (`CRR`).

| Article | Heading | Pages | Role |
| --- | --- | --- | --- |
| 381 | Meaning of credit valuation adjustment | 580 | Definitions of CVA and CVA risk |
| 382 | Scope | 581 to 583 | Transactions in and out of scope, exemptions; open decision M4 |
| 382a | Approaches for calculating the own funds requirements for CVA risk | 583 to 584 | The standardised (Article 383), basic (Article 384) and simplified (Article 385) approaches, and their combination |
| 383 to 383z | Standardised approach (SA-CVA) and its regulatory CVA model, sensitivities, risk weights and correlations | 584 to 611 | Second approach (M2); needs the competent authority's permission (Article 383(1)) |
| 384 | Basic approach (BA-CVA) | 611 to 615 | First approach (M2) |
| 385 | Simplified approach | 615 | Not selected |
| 386 | Eligible hedges | 615 to 616 | Hedges recognised by Articles 383 and 384 |
| 162 | Maturity | 243 to 246 | Effective maturity of a netting set, referenced by Article 384(2) |

<a id="approaches"></a>

## Approaches

Decided by the maintainer on 2026-10-24 in #8 (M2): the full basic approach
first, then the standardised approach.

Article 384(1) has two formulae, which an institution may not combine:

| Name used here | CRR | When it applies |
| --- | --- | --- |
| **Full BA-CVA** | Article 384(1), point (a), and paragraph 2 (`BACVA^total`) | The institution includes one or more eligible hedges recognised under Article 386 |
| **Reduced BA-CVA** | Article 384(1), point (b), and paragraph 3 (`BACVA^csr-unhedged`) | The institution includes no eligible hedge |

The CRR does not use the words *full* and *reduced*; they are used here only
as names for these two formulae.

**Reduced BA-CVA is a component of the full one.** Article 384(2) defines
`BACVA^total` from `BACVA^csr-unhedged`, which it defines as calculated in
accordance with paragraph 3 (page 611). Implementing the full BA-CVA
therefore implements paragraph 3 as well. This settles the question left open
in M2; the reduced BA-CVA is not delivered as a separate approach, but its
formula is traced and tested as part of the full one.

The SA-CVA follows the BA-CVA. Its scope, the regulatory CVA model of
Article 383a and its permission requirements are to be recorded here before
any SA-CVA work starts.

<a id="inputs"></a>

### BA-CVA inputs

What Article 384 needs, by the terms of its definitions (pages 611 to 615).
Field names, units and validation belong to the input contract
(`docs/contracts/`, not yet written); this table only records which data the
text requires and who provides it.

| Level | Data required by Article 384 | Provided by |
| --- | --- | --- |
| Counterparty | Sector and credit quality, mapped to a risk weight by Table 1; a counterparty without an external rating takes the unrated column unless an internal-rating mapping is approved by the competent authority | Caller: the Table 1 sector and credit-quality category. The tool does not rate counterparties or map internal ratings |
| Netting set | Counterparty credit risk exposure value, including collateral, under Title II, Chapter 6, Sections 3 to 6 | Caller: supplied EAD (M5) |
| Netting set | Effective maturity under Article 162, capped at the longest contractual remaining maturity in the netting set instead of five years | Caller: supplied in years (M5). The tool takes it as given and does not apply Article 162 or the cap |
| Netting set | Supervisory discount factor: 1 for an institution using Title II, Chapter 6, Section 6; otherwise a formula of the maturity | Calculated, from a caller-supplied indicator of the exposure method |
| Single-name hedge (full BA-CVA) | Residual maturity, notional, supervisory discount factor, risk weight of the reference name (Table 1) and correlation `r_hc` by its relation to the counterparty (Table 2, Article 386(3), point (a)) | Caller supplies maturity, notional, reference sector and credit quality, and relation; the rest is calculated |
| Index hedge (full BA-CVA) | Residual (notional-weighted) maturity, full notional, supervisory discount factor, and a risk weight from the index constituents' sectors and credit qualities | Caller supplies maturity, notional and constituent categories; the rest is calculated |

The tool does not decide whether a hedge is eligible under Article 386(1) or
whether a transaction is in scope under Article 382; the caller supplies
eligible hedges and in-scope netting sets, and the contract must say so.

<a id="version-applicability"></a>

## Version applicability

A calculation uses the version of the controlling text that applies on its
calculation date; for a test case, its `valuation_date`. An expected result is
accepted only for a regime listed here, and only when its case's
`valuation_date` falls within that row's dates. A blank *To* means no later
version is registered.

| Regime | Source ID | From | To |
| --- | --- | --- | --- |
| `CRR` | `CRR` | 2025-01-01 | |

**Why 2025-01-01.** CRR3 applies from 1 January 2025 (its Article 2). Of its
points amending Title VI, (197) to (202), only two applied earlier, from
9 July 2024: point (198)(c), adding Article 382(6), and point (201) concerning
Article 383a(4) and (5). Both are mandates for regulatory technical standards,
not calculation rules; Article 384, the BA-CVA (point (202)), applies from
1 January 2025. Calculation dates before 1 January 2025 need the pre-CRR3
Title VI, which is not registered, and are not supported.

**Later amendments.** In the registered consolidated text, the amendment
markers within Title VI are M17 (CRR3), M19 (Regulation (EU) 2024/2987, in
Article 382(4) and (4c), the scope exemptions for intragroup transactions)
and the corrigendum C2. The consolidated text dated 1 January 2027
(version 022.001) differs from the registered one in Title VI only in line
breaks and hyphenation, compared on 2026-10-24; it is not registered.

<a id="source-register"></a>

## Source register

Cite sources by ID in code `REFERENCE` sections, in the
[traceability](#traceability) table and in test cases. Reference values may
come only from a source in this register; add a row before citing a new one.
A later version is a new row, not an edit. Retrieval details, hashes and
reuse terms are in [sources/README.md](sources/README.md).

| ID | Role | Source | Version | Status |
| --- | --- | --- | --- | --- |
| `CRR` | Controlling | Regulation (EU) No 575/2013, consolidated text | 26.06.2026, version 021.001 | **Relied on.** Copy in `sources/`: page 1, pages 243 to 246 (Article 162) and pages 580 to 616 (Part Three, Title VI, Articles 381 to 386). Read on 2026-10-24: the article headings of Title VI; Article 382a(1); Article 384 in full, with its formulas and tables as printed; Article 385; Article 386(1) and (3). Formulas and tables are not yet transcribed or checked |
| `CRR3` | Controlling (amending act) | Regulation (EU) 2024/1623, OJ L, 19.6.2024 | As published | Read on 2026-10-24 for its date of application (Article 2) and the list of its points amending Title VI |

Pending registration, each to be found and read before a rule relies on it:
the regulatory technical standards and guidelines mandated by Title VI
(for example Articles 382(6) and 383a(4) and (5)), the Commission
implementing acts under Article 382(4c), and Regulation (EU) 2024/2987.
An external implementation, the only source of an `independent` reference
value, is registered with an ID starting `IMPL-`
([reference classes](TEST_CASES.md#reference-classes)). None is registered.

The consolidated CRR has no legal effect, as its first page states; the
authentic text is the one published in the Official Journal.

<a id="assumptions"></a>

## Assumptions

| Topic | Current position |
| --- | --- |
| Units | Amounts in a stated currency, unscaled; rates, weights and factors as decimals; maturities in years ([VBA_HOUSE_STYLE.md](../VBA_HOUSE_STYLE.md#contracts-units-and-errors)). Test cases follow the same rules ([TEST_CASES.md](TEST_CASES.md#fixture-format)) |
| Exposure | EAD and effective maturity per netting set are supplied, not computed (M5). The tool takes them as the exposure value and maturity Article 384 defines and does not check how they were calculated |
| Scope and eligibility | The caller supplies only in-scope netting sets (Article 382) and eligible hedges (Article 386); the tool does not apply exemptions or eligibility tests (M4, M6) |
| Supervisory parameters | Taken only from a registered controlling text, recorded with its locator, and never typed in code without a `REFERENCE` |
| Numeric conventions | `Double` arithmetic, no intermediate rounding; tolerances are explicit on every expected value ([TEST_CASES.md](TEST_CASES.md#tolerance)) |
| Market data | None for the BA-CVA beyond the caller's inputs. The SA-CVA needs sensitivities and market data, decided before SA-CVA work (M6) |

<a id="open-decisions"></a>

## Open decisions

The decisions are listed in [DECISIONS.md](../DECISIONS.md). M1, M2 and M3
are closed by this document. Still open, each to be closed by a reviewed
change that records it here with its controlling source:

- **M4:** scope and exemptions under Article 382, including the amendments of
  Regulation (EU) 2024/2987, and counterparty classification for Table 1.
- **M5:** netting-set and collateral assumptions beyond the supplied EAD
  and effective maturity.
- **M6:** hedge data and eligibility; SA-CVA market data and sensitivities.
- **M7:** output measures, currencies, sign conventions and the error policy
  of the facade.

<a id="traceability"></a>

## Traceability

Every implemented rule is traced **source → article and paragraph →
effective date → formula → test case**. Rule IDs are
`CRR.<article>[.<paragraph>]`, for example `CRR.384.3`. A rule enters this
table when code first implements it.

| Rule ID | Source | Article and paragraph | Effective from | Formula | Implemented in | Cases | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| *None yet* | | | | | | | |

- **Formula** is transcribed in `docs/methodology/` from the registered
  copy, naming the printed page and the formula or table it comes from, and
  checked against it. The formulas of Article 384 are images in the PDF and
  absent from its text layer; they are read from the page, not from
  extracted text.
- **Cases** lists the case IDs; **Status** is the validation status of the
  [completeness policy](TEST_CASES.md#completeness-policy).

## Rules

- Every formula, parameter, risk weight or correlation used later cites its
  registered controlling source and printed page here.
- No SFT, SA-CCR or other counterparty-credit-risk formula is a default for
  CVA; the exposure value comes from the caller (M5).
- Source documents are copied only under their publishers' terms, recorded
  in [sources/README.md](sources/README.md), and never edited.
