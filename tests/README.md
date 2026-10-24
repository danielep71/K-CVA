# Verification

No numerical CVA test suite or host certification exists yet. The deterministic
scaffold is tracked in #10; evidence and host smoke validation in #11. The
fixture and expected-result format, reference classes and tolerances are
defined in [TEST_CASES.md](../docs/methodology/TEST_CASES.md) (#8); the only
case is an illustrative format example.

Reserve fixtures for synthetic inputs, expected for independently justified
outputs, derivations for Python reference work, and evidence for deliberately
retained reviewed results. Disposable run output belongs in test-results at the
repository root and must not be committed.

Evidence must identify the exact source revision and execution environment.
A scaffold pass does not certify regulatory calculations. Reference calculations
must cite the methodology and explain their independence from production VBA.
See [architecture](../docs/REPOSITORY_STRUCTURE.md) for contracts and placement.
