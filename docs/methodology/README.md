# Methodology work

The initial product targets regulatory CVA capital, as confirmed in
[DECISIONS.md](../DECISIONS.md). No calculation approach or regulatory formula is
implemented or validated.

Issue #8 must establish the source register and fixture contract. The
maintainer selected EU CRR3 as the regulatory basis, the full BA-CVA and then
the SA-CVA as approaches, and EAD supplied as an input
([DECISIONS.md](../DECISIONS.md) M1, M2 and M5). Do not infer applicability
from a source publication date.

For each source, record issuer, title, primary URL, exact provision, version,
applicable dates, retrieval date and local-copy provenance/permissions if retained.
Create sources/ only when an actual permitted source artifact is added.

Before implementing calculations, resolve the product scope, the EAD input
contract, netting/collateral assumptions, hedge treatment, market-data
requirements, output measures and numeric conventions. Record decisions with
their primary sources and affected contract/test identifiers.

Economic/accounting CVA is outside the initial scope. SFT haircuts and SA-CCR
formulas are not CVA defaults. The supplied EAD needs a documented input
contract and approach-specific justification.

Synthetic fixtures must distinguish input assumptions, independently derived
expected results and implementation output. The selected rule version and
absolute/relative tolerances must be explicit. Setup scaffolding must never be
labelled numerical certification.
