# Methodology work

The initial product targets regulatory CVA capital, as confirmed in
[DECISIONS.md](../DECISIONS.md). No calculation approach or regulatory formula is
implemented or validated.

Issue #8 must establish the source register and fixture contract. EU CRR is the
proposed jurisdictional basis, pending confirmation; Basel is proposed as a
comparison reference. Do not infer applicability from a source publication date.

For each source, record issuer, title, primary URL, exact provision, version,
applicable dates, retrieval date and local-copy provenance/permissions if retained.
Create sources/ only when an actual permitted source artifact is added.

Before implementing calculations, resolve the initial approach, product scope,
exposure inputs, netting/collateral assumptions, hedge treatment, market-data
requirements, output measures and numeric conventions. Record decisions with
their primary sources and affected contract/test identifiers.

Economic/accounting CVA is outside the initial scope. SFT haircuts and SA-CCR
formulas are not CVA defaults. Any future use of externally supplied exposures
must have a documented contract and approach-specific justification.

Synthetic fixtures must distinguish input assumptions, independently derived
expected results and implementation output. The selected rule version and
absolute/relative tolerances must be explicit. Setup scaffolding must never be
labelled numerical certification.
