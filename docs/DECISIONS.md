# Scope and architecture decisions

Decisions for issue [#3](https://github.com/danielep71/MKT-K-CVA/issues/3),
recorded 2026-10-24. This register distinguishes confirmed product choices,
accepted architecture conventions, and unresolved methodology choices.
No formula or regulatory applicability is established by this document.

| ID | Decision | Status and evidence |
| --- | --- | --- |
| A1 | Initial product scope is regulatory CVA capital. Economic/accounting CVA valuation is outside the initial product. | Confirmed by the maintainer in the #3 implementation discussion. |
| A2 | Excel/VBA application; Python for tooling and independent reference tests only. No parallel Python engine or Python runtime dependency. | Confirmed by the maintainer in the #3 implementation discussion. |
| A3 | Application profile; exported VBA is authoritative, workbook is built from source. Pure calculation core, public facade, Excel host adapter. | Accepted setup architecture through merged [PR #24](https://github.com/danielep71/MKT-K-CVA/pull/24) (#3), integrated into main by PR #28. Compatible with the application label profile; implementation is still pending. |
| A4 | Microsoft 365 Excel desktop on Windows, 64-bit is the intended initial host. No host is certified yet. | Intended host policy established by #5 in [INSTALLATION.md](../INSTALLATION.md), delivered through [PR #26](https://github.com/danielep71/MKT-K-CVA/pull/26). Exact tested builds and host evidence remain #11 work; onboarding remains #16. |
| M1 | EU CRR3 as the regulatory basis: Regulation (EU) No 575/2013 as amended by Regulation (EU) 2024/1623, Part Three, Title VI (own funds requirements for CVA risk). Do not mix regimes within a result. | Confirmed by the maintainer on 2026-10-24 in [#8](https://github.com/danielep71/MKT-K-CVA/issues/8). Exact provisions, the consolidated version and applicable dates are recorded in the #8 source register (M3); no Basel text is a controlling source. |
| M2 | Approaches: the full basic approach (BA-CVA, with recognition of eligible CVA hedges) and the standardised approach (SA-CVA). Full BA-CVA is implemented first, SA-CVA after it. The reduced BA-CVA is not a separate deliverable. | Confirmed by the maintainer on 2026-10-24 in #8. The reduced formula (Article 384(3)) is a component of the full one (Article 384(2)), so it is implemented and tested as part of it ([methodology](methodology/README.md#approaches)). Nothing is implemented yet. |
| M3 | Source versions, applicability dates, permissions and source register. | Recorded in #8: the consolidated CRR of 26.06.2026 (version 021.001), applicable from 2025-01-01, with a copy of Article 162 and Title VI and its reuse terms ([source register](methodology/README.md#source-register), [version applicability](methodology/README.md#version-applicability)). Sources a later rule relies on are registered before use. Repository licensing and provenance policy were completed by #4; see [NOTICE.md](../NOTICE.md). |
| M4 | Product scope, exemptions, counterparty classifications and aggregation boundaries. | Open; record in methodology before implementing affected contracts. |
| M5 | Exposure inputs, netting and collateral treatment. EAD and effective maturity per netting set are supplied as inputs, not computed. | EAD supplied: confirmed by the maintainer on 2026-10-24 in #8. Effective maturity supplied: confirmed by the maintainer on 2026-10-24 in #8. The methodology records them as the exposure value and maturity Article 384 defines; their field contract belongs to docs/contracts. Netting-set and collateral assumptions remain open; no SFT haircut or SA-CCR formula is imported as a default. |
| M6 | Required market data, sensitivities, hedges, mapping and eligibility rules. | Open; depends on the selected approach. |
| M7 | Output measures, currencies, sign conventions, rounding, tolerances and error policy. | Test tolerances and comparison rules defined by #8 in [TEST_CASES.md](methodology/TEST_CASES.md#tolerance) and accepted by the maintainer on 2026-10-24; no intermediate rounding. Output measures, sign conventions and the facade error policy remain open. |

A methodology decision must identify its owner, dated primary source, exact
provision, applicability, rationale and validation consequences. Closing it
requires a reviewed change to this register and the affected contracts/tests.
Implementation cannot silently resolve an open decision.

The setup milestone may establish contracts and a deterministic scaffold.
It must not present synthetic scaffold outputs as validated regulatory capital.
