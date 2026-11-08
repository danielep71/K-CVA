# Validation status

> Ported intake document (#180). Describes the unvalidated prototype; source claims
> are retained for review, not adopted as regulatory or runtime acceptance.
> See [porting record](PORTING.md).

Prepared 8 November 2026. Native Excel is unavailable in the preparation host.

Performed here:
- Inspected K-CVA scope, architecture and the registered regulatory source.
- Read Article 384 formula images on pp.611–615 and Table 1/Table 2.
- Inspected K-SFTs and K-SACCR templates; reused K-SFTs cell styles and layout.
- Generated 10 numeric expected results using 50-digit Decimal and pairwise
  covariance; packaged 12 invalid-input cases for the actual VBA engine.
- Checked VBA encoding, procedure structure, jump targets and dependency direction.
- Inspected workbook tables, input validations, styles and named header anchors;
  recalculated its native formula with Artifact Tool and rendered every sheet.

Not performed here: VBA compilation, VBA execution, Windows COM build execution,
button clicks, Excel table-extension behavior and Workbook_SheetChange events.
A packaged VBA test or a static check is not evidence that VBA execution passed.
The template therefore starts with blank outputs and all 22 cases NOT RUN.

The Windows builder executes the actual tests and demo and refuses a successful
build if any case fails. It writes build/Excel-build-evidence.txt only after success.
It does not change macro security or run a parallel Python calculation engine.

Manual Excel checks after a successful build:
1. Edit NS1 EAD; confirm all prior capital/detail results disappear immediately.
2. Run; confirm new figures. Double every EAD and every hedge notional: capital
   must double. Restore the synthetic demo afterwards.
3. Insert a netting set inside the table, including after a blank row. Confirm it
   is used. A partially filled row must produce FAILED and blank capital.
4. Clear both hedge tables and all constituents. Run: demo unhedged capital is
   675933.479943836. Restore sample hedges to recover 553046.965386535.
5. Validate inputs: details/capital stay blank. Clear outputs: same.
6. Make a duplicate ID, missing EAD, unmatched key or weights not summing to 1:
   the run fails visibly without stale results. Correct and run again.
7. Save, close and reopen. Check buttons and repeat input-change invalidation.
8. Record Excel version/build/bitness, exact package hash and observed outcomes.

Production release, independent regulatory validation and repository integration
remain separate steps. No GitHub release or merge was performed for this package.
