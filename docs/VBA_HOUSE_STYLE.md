# VBA house style

These conventions apply to the first and subsequent VBA components.
No production VBA exists yet; tests/modules holds the test harness and its
example suite (#10). The mechanical rules are checked
statically by the [VBA static checks](CI.md#vba-static-checks), which also
list what they cannot see; runtime verification and failure-path evidence
belong to #10/#11.
[Architecture](REPOSITORY_STRUCTURE.md) owns placement and dependency direction;
[installation](../INSTALLATION.md) owns import/export and host status.

## Naming and visibility

| Element | Convention | Example (not an implemented component) |
| --- | --- | --- |
| Core standard module | CORE_ plus subject | CORE_Validation |
| Public facade module/function | CVA_ plus subject/quantity | CVA_Functions |
| Host-independent class | C plus noun | CCalculationResult |
| Excel adapter module | M_ plus subject | M_Run |
| Document module | ThisWorkbook or sh plus role | shInputs |
| UserForm | frm plus role | frmRunOptions |
| Test module | TEST_ plus subject | TEST_Harness |
| Example module | Example plus subject | ExampleInputs |
| Procedure | PascalCase verb phrase | ValidateInput |
| Parameter/local | Descriptive PascalCase | CalculationCurrency |
| Constant/error constant | UPPER_SNAKE_CASE / ERR_ prefix | ERR_INVALID_INPUT |
| Enum / member | Cva plus noun / short prefix | CvaRunStatus / rsFailed |

Component names must match exported Attribute VB_Name and filename stems.
Names are case-insensitive in VBA; review unintentional capitalization changes.
Single-letter names are reserved for loop counters. No mutable public globals.

Every component uses Option Explicit. Core and test standard modules use
Option Private Module. Procedures are Private unless called by another
component. Public does not mean supported: only declarations in
[PUBLIC_API.txt](PUBLIC_API.txt) form the supported API. API changes update
the inventory, contracts and tests together.

Use explicit array bounds, never Option Base. Prefer specific types to Variant;
use Variant only where the boundary needs missing/error/heterogeneous values,
with explicit validation. Default to ByVal; document every ByRef mutation.
Core code has no Excel object-model access or mutable run state.

Any future native declaration needs a separate compatibility review: PtrSafe
alone does not make a declaration correct. Use LongPtr for pointers/handles,
and the actual API-defined widths for other arguments; no blanket Long-to-LongPtr
replacement. No external declarations are needed by this setup.

## Contracts, units and errors

Each procedure documents PURPOSE, INPUTS, RETURNS, ERROR POLICY, DEPENDENCIES,
STATE OWNERSHIP and REFERENCE where applicable. Include an UPDATED date.
INPUTS must state meaning, type, unit, currency/date basis, valid domain and
ownership. Comments explain invariants and reasons, not obvious assignments.

Use Double for calculation amounts and proportions, Long for counts, Boolean
for flags, String for identifiers/currency codes, and Date for host-side dates.
Boundary serialization specifies an unambiguous date representation.
Names or contracts distinguish decimal rates from basis points and currency
units from scaled display amounts. Do not invent rounding, day counts,
regulatory parameters or allowed domains: record them under #8 before formulas.
No silent conversion of missing input to zero and no undocumented defaults.

Internal errors use named ERR_ constants, allocated once in a documented
project range (vbObjectError + 2048 through +4095). Err.Source identifies the
component and procedure. Messages describe the condition without leaking
confidential inputs. Error codes distinguish invalid input, unsupported scope,
numerical failure and host/cleanup failure.

Core procedures raise documented errors. Facade entry points translate them
according to their contract: macros return/report structured failure, while
worksheet functions may return a documented CVErr value in a Variant.
Worksheet functions do not mutate Excel state or show dialogs. A facade never
turns an unexpected failure into a successful-looking amount.

On Error Resume Next is limited to a single guarded operation followed
immediately by capture/check of Err and restoration of the intended handler.
Never suppress an entire calculation or cleanup sequence.

## Operation and cleanup outcomes

Host operations expose both outcomes in their caller-facing result contract:

| Field | Meaning |
| --- | --- |
| OperationSucceeded | Whether the intended work completed |
| PrimaryError | Saved number, source and description, or no primary error |
| CleanupSucceeded | Whether every required restoration succeeded |
| CleanupErrors | All failed restoration steps, with their error details |
| RecoveryRequired | True when host state could not be restored |

A successful operation with failed cleanup is not overall success. A failed
operation with successful cleanup remains failed. Callers must inspect both
outcomes. These are required semantic fields, not an implemented public type.

Capture each setting before changing it; track capture and restoration ownership
per setting. Register restoration responsibility before attempting a mutation,
so a setter that fails after a partial effect is still covered. Never restore
an uncaptured value. Restore only settings the operation attempted to change,
to the captured values; nested operations preserve their caller's state.

Both normal and error paths enter cleanup. Save the primary Err.Number,
Err.Source and Err.Description into ordinary variables before cleanup or any
other call. Use a separate helper/error handler for each restoration; attempt
all restorations even when one fails. Cleanup must never replace the saved
primary error. Return both outcomes, or publish cleanup diagnostics through a
documented output before re-raising the saved primary error. If only cleanup
fails, return/report cleanup failure rather than success.

Do not reset Calculation, EnableEvents, ScreenUpdating, DisplayAlerts or
StatusBar to assumed defaults. Capture only those actually needed. Worksheet
ownership and created artifacts need equivalent explicit cleanup rules.
Failure-path tests must cover partial capture, mutation failure, primary failure,
each restoration failure and simultaneous primary/cleanup failure (#10/#11).
`TEST_Examples.RunExampleOperation` is the reference implementation, with a
case for each of these paths ([tests/README.md](../tests/README.md#vba-harness));
it has not been run in Excel yet (#11).

## Source representation

Exported .bas, .cls and .frm text is ASCII only, without BOM; non-ASCII text
requires an explicit runtime representation (for example ChrW) or a separately
specified resource. This avoids relying on a particular Windows code page.
Form .frx files are binary and stay beside their .frm.

Git stores normalized LF text; .gitattributes checks VBA out with CRLF.
Preserve VBE-generated VERSION/BEGIN/END and Attribute metadata. EditorConfig
does not enforce ASCII; the `vba-source` check does.

Use four spaces per indentation level, no tabs or trailing whitespace.
Keep procedure declarations, End statements and labels at their natural outer
level. Use clear MODULE SETTINGS, DECLARE, INITIALIZE and FAIL sections when
they make a routine easier to follow; do not add empty ceremonial sections.
Separate procedures with two blank lines. Generated components identify their
generator and are regenerated rather than hand-edited.

Changed VBA must be imported, compiled and exercised on the declared target
host before its runtime behavior is accepted. Static checks are not compilation.
Record full commit, host version/bitness, reference list and results, as in
[recording an Excel run](../INSTALLATION.md#recording-an-excel-run).
