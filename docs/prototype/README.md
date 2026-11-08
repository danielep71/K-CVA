# Prototype intake

Original archive supplied on 2026-11-08. SHA256: `d756a85d23223b54c1ce4e94693b03e9a35c6e8d694f631d98ef8a4fd71036bb`.

This branch preserves the ZIP unchanged. It is not an accepted engine or release. v0.2.0 covers porting and tooling only; mathematical correctness, regulatory validation and new capabilities belong to later milestones.

Porting destinations follow K-SACCR: src/core/, src/modules/, src/workbook/CVA_Template.xlsx and workbook adapters; tools/ for build, export and synchronization; tests/modules/, tests/fixtures/, tests/expected/, tests/derivations/; docs/contracts/ and docs/methodology/. Generated .xlsm files stay outside tracked source. Approve a narrow template ignore exception during porting. Preserve source provenance and distinguish operational smoke tests from numerical certification.
