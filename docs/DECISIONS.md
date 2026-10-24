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
| M1 | EU CRR as the initial jurisdictional basis, Basel as a methodological comparison reference; do not mix regimes within a result. | Proposed, not a confirmed regulatory decision. Confirm controlling sources and jurisdiction in #8 before any regulatory calculation is implemented. |
| M2 | Initial regulatory CVA approach and implementation order. | Open in #8; no approach is selected or implemented by #3. |
| M3 | Source versions, applicability dates, permissions and source register. | Methodology source versions, applicability and permissions remain open in #8. Repository licensing and provenance policy were completed by #4; see [NOTICE.md](../NOTICE.md). |
| M4 | Product scope, exemptions, counterparty classifications and aggregation boundaries. | Open; record in methodology before implementing affected contracts. |
| M5 | Exposure inputs, netting and collateral treatment; whether exposures are supplied or derived. | Open; no SFT haircut or SA-CCR formula is imported as a default. |
| M6 | Required market data, sensitivities, hedges, mapping and eligibility rules. | Open; depends on the selected approach. |
| M7 | Output measures, currencies, sign conventions, rounding, tolerances and error policy. | Open; #8 defines fixture conventions before numerical tests are accepted. |

A methodology decision must identify its owner, dated primary source, exact
provision, applicability, rationale and validation consequences. Closing it
requires a reviewed change to this register and the affected contracts/tests.
Implementation cannot silently resolve an open decision.

The setup milestone may establish contracts and a deterministic scaffold.
It must not present synthetic scaffold outputs as validated regulatory capital.
