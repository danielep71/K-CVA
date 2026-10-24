# Verification

No numerical CVA test suite or host certification exists yet. The deterministic
scaffold is tracked in #10; methodology and fixture conventions in #8; evidence
and host smoke validation in #11.

Reserve fixtures for synthetic inputs, expected for independently justified
outputs, derivations for Python reference work, and evidence for deliberately
retained reviewed results. Disposable run output belongs in test-results at the
repository root and must not be committed.

Evidence must identify the exact source revision and execution environment.
A scaffold pass does not certify regulatory calculations. Reference calculations
must cite the methodology and explain their independence from production VBA.
See [architecture](../docs/REPOSITORY_STRUCTURE.md) for contracts and placement.
