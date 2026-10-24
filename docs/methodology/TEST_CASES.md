# Numerical test cases

This document defines how K-CVA's numerical test cases are written:
files, inputs and their units, expected results and their provenance,
tolerances, case categories, invalid inputs and when a rule counts as
validated. Sources, approaches and rule IDs come from the
[methodology](README.md). The structure is adapted from CCR-K-SFTs's
`docs/methodology/TEST_CASES.md` (see [NOTICE.md](../../NOTICE.md)); no SFT
case, value or threshold is reused.

> [!IMPORTANT]
> **Status on 2026-10-24: format only.** The one case,
> `illustrative-format-example`, shows the format and holds no regulatory
> value. The input and output fields of real cases are fixed with the input
> and output contract (`docs/contracts/`, not yet written) once M4 to M7 are
> decided. `python tools/check_repository.py` (gate `test-cases`) enforces
> what a file can show ([checking](#checking)); it never runs a calculation.

## Files

A case is one input file and one expected-result file per calculation regime:

| File | Holds |
| --- | --- |
| `tests/fixtures/<case-id>.json` | Synthetic inputs: counterparties, netting sets with their supplied exposure values, eligible hedges |
| `tests/expected/<case-id>.<regime>.json` | Expected results for one regime, each with its provenance. The only regime is `crr` ([version applicability](README.md#version-applicability)) |
| `tests/derivations/<name>.py` | Optional: a script that computes expected values from the documented method, separately from the code under test |

- Case IDs are lowercase kebab-case, equal to the fixture's file name and
  never reused.
- A case whose expected values are all `illustrative` starts with
  `illustrative-`, and only such a case may.
- Every fixture has at least one expected file, and every expected file a
  fixture.
- Files are UTF-8 JSON, stored with LF. All data is **synthetic**: never real
  counterparties, portfolios, exposures, ratings or market data
  ([SECURITY.md](../../SECURITY.md#data-and-credentials)).

<a id="fixture-format"></a>

## Fixture format

```json
{
  "schema_version": 1,
  "kind": "cva-fixture",
  "id": "illustrative-format-example",
  "synthetic": true,
  "description": "What the case exercises, in one sentence",
  "category": "nominal",
  "approach": "ba_cva_reduced",
  "calculation_currency_code": "EUR",
  "valuation_date": "2026-01-02",
  "counterparties": [
    {"id": "CP1", "inputs": {"illustrative_sector_code": "SECTOR-A"}}
  ],
  "netting_sets": [
    {
      "id": "NS1",
      "counterparty_id": "CP1",
      "inputs": {"currency_code": "EUR", "exposure_value_amount": 1000000}
    }
  ],
  "hedges": []
}
```

| Rule | Detail |
| --- | --- |
| Envelope | `schema_version` (1), `kind` (`cva-fixture`), `id`, `synthetic` (`true`), `description`, `category`, `approach`, `calculation_currency_code`, `valuation_date`, `counterparties`, `netting_sets` and `hedges` are required, and no other key is allowed; an `invalid` case relaxes this for the calculation inputs ([invalid inputs](#invalid-inputs)) |
| Approach | `ba_cva_reduced` (Article 384(1), point (b), and paragraph 3) requires an empty `hedges` list; `ba_cva_full` (Article 384(1), point (a), and paragraph 2) requires at least one hedge. SA-CVA has no value yet: it is added when its scope is recorded in the methodology |
| Identifiers | Each counterparty, netting set and hedge has an `id`, unique in the fixture. Each netting set names an existing `counterparty_id`. A single-name hedge names the `counterparty_id` it hedges; an index hedge has `counterparty_id: null` |
| Hedges | Each hedge has `kind`, `single_name` or `index`, and an `inputs` object. Only eligible hedges appear: eligibility under Article 386 is the caller's responsibility, not tested by a case |
| Inputs | Every quantity sits in an `inputs` object, whose keys are lower snake case and end in a unit suffix (below). Which keys exist is decided by the input contract; until it is written, only `illustrative-` cases may exist, and their keys may start with `illustrative_` |
| Exposure | A netting set's exposure value and effective maturity are supplied (M5), never derived in a case: they are inputs, not expected outputs |
| Currencies | `calculation_currency_code` is the currency of results. An object whose `inputs` hold an `_amount` key also holds `currency_code`, the currency of all its amounts, so a currency mismatch is always visible |
| Signs | Amounts are unsigned unless the input contract defines a signed field |

The rules above and the unit suffixes below hold for the calculation inputs
of every category except `invalid`, whose inputs may break them
([invalid inputs](#invalid-inputs)).

**Unit suffixes.** A key without one of these suffixes is rejected:

| Suffix | Value |
| --- | --- |
| `_amount` | Number in the object's `currency_code`, unscaled |
| `_rate`, `_weight`, `_factor` | Decimal number: `0.05`, never `5` meaning 5 % |
| `_years` | Number of years |
| `_count` | Whole number, at least 0 |
| `_date` | Text, ISO `YYYY-MM-DD` |
| `_flag` | `true` or `false` |
| `_code` | Text code; one ending `currency_code` is three upper-case letters (ISO 4217) |
| `_id` | Text identifier |

`null` means not applicable. Files are strict JSON and numbers are finite, in
every category: `NaN`, `Infinity` and a number that overflows to infinity
(such as `1e400`) are rejected. A non-finite input is tested in a VBA test
module instead. A file holding only `null`, or anything other than an object,
is rejected, never skipped.

<a id="expected-format"></a>

## Expected-result format

```json
{
  "schema_version": 1,
  "kind": "cva-expected",
  "fixture": "illustrative-format-example",
  "regime": "CRR",
  "outputs": [
    {
      "quantity": "illustrative_total_exposure_value_amount",
      "counterparty": null,
      "netting_set": null,
      "rule": null,
      "value": 1000000,
      "unit": "EUR",
      "tolerance": {"absolute": 0.000001, "relative": 0.000000001},
      "reference": {
        "class": "illustrative",
        "source": null,
        "locator": null,
        "derivation": "Why the value exists and how it was obtained",
        "script": null,
        "derived_by": "Name",
        "reviewed_by": null,
        "date": "2026-10-24"
      }
    }
  ]
}
```

| Rule | Detail |
| --- | --- |
| Envelope | `schema_version` (1), `kind` (`cva-expected`), `fixture` (an existing case ID), `regime` (`CRR`, matching the lower-case file-name suffix) and a non-empty `outputs` list are required |
| Calculation date | The fixture's `valuation_date` selects the version of the controlling text: it must fall within the dates of a row of the [version applicability](README.md#version-applicability) table for the file's regime. A case dated before 1 January 2025 is rejected, because the pre-CRR3 text is not registered |
| Output scope | A portfolio output, such as `BACVA^total`, has `counterparty: null` and `netting_set: null`. A counterparty output, such as `SCVA_c`, names a counterparty of the fixture. A netting-set output names a netting set and its counterparty |
| Quantity | Lower snake case. The quantity names of real cases are fixed with the output contract (M7); an `illustrative-` case may use a name that starts with `illustrative_` for a format-only value |
| Number | `value`, `unit` and `tolerance`. `unit` is a currency code for an amount, `1` for a rate, weight or factor, or `years` |
| Text | `text`, compared exactly, with no `unit` or `tolerance`. A rejection is a text output whose quantity ends in `_status` |
| Rule | A rule ID under the [traceability](README.md#traceability) convention, `CRR.<article>[.<paragraph>]`, such as `CRR.384.3`. It may be `null` only for an `illustrative` value |
| Reference | One per output; see [reference classes](#reference-classes) |

<a id="reference-classes"></a>

## Reference classes

Every expected value carries exactly one class. Only the first two are
numerical-validation references.

| Class | Meaning | Required fields |
| --- | --- | --- |
| `published` | Printed in a registered source, for example a worked example | `source` (a register ID) and an exact `locator` (article, paragraph, table, printed page) |
| `independent` | Computed by an external implementation by another author, registered as a source with an ID starting `IMPL-` | `source` (`IMPL-…`), `locator`, `derivation`, `derived_by` (the implementation and its version) |
| `illustrative` | Shows the format or a behaviour; **not** a validated CVA figure | `derivation` saying why it exists and how the value was obtained |

- A `published` value never cites an `IMPL-` source, and an `independent`
  value always does. A value derived within the project, even from a
  registered text, stays `illustrative`, including one computed by a script
  under `tests/derivations/`.
- `script`, when not `null`, names a file under `tests/derivations/` that
  computed the value; it must exist.
- `reviewed_by` may be `null`: the code under test and its expected values
  come from the same maintainer, and no independent reviewer is required.
- **Examples are never benchmarks** unless their source is registered and the
  value is printed there. Test output reports `illustrative` results
  separately and never as validation.

<a id="tolerance"></a>

## Tolerance

An actual result `a` matches the expected value `e` when

```text
|a − e| ≤ max(absolute, relative × |e|)
```

Both bounds are stated on every numeric output, as finite numbers of at least
0; there is no hidden default. Both 0 means an exact comparison, for whole
numbers only. The bounds below were accepted by the maintainer on 2026-10-24
in [#8](https://github.com/danielep71/K-CVA/issues/8) (M7).

| Reference | `absolute` | `relative` |
| --- | --- | --- |
| `independent` or `illustrative`, full precision | `1e-6` currency units (`1e-9` for a rate, weight or factor, `1e-9` years for a maturity) | `1e-9` |
| `published`, rounded | Half a unit of the last printed digit: printed in thousands → `500` | `0` |

- **Near zero** the absolute bound governs: as `|e|` shrinks, the relative
  term vanishes, so an expected `0` is matched within `absolute` only. An
  `absolute` of 0 with an expected 0 therefore demands an exact zero.
- **Domain rules apply before tolerance:** a quantity that must not be
  negative, such as an own funds requirement, fails if it is negative,
  however small.
- Results are compared unrounded; the engine does not round intermediate
  values.

<a id="categories"></a>

## Case categories

Each fixture declares one `category`:

| Category | Covers |
| --- | --- |
| `nominal` | Typical inputs within the domain |
| `boundary` | Values on a domain edge: a zero exposure value, a single counterparty or netting set, a maturity at a cap, a result that must be exactly zero |
| `invalid` | Inputs that must be rejected: missing or unknown fields, a negative exposure value, a hedge for an unknown counterparty, hedges under `ba_cva_reduced`, an unknown approach or currency |

<a id="invalid-inputs"></a>

### Invalid inputs

- An `invalid` case is expected to be **rejected**, never calculated: each of
  its expected files holds at least one `_status` text output, and no numeric
  output for what it rejects.
- An `invalid` case separates the harness metadata, which must always be
  valid, from the calculation inputs, which may break any input rule, because
  that is what the case tests:
  - **Always valid:** `schema_version`, `kind`, `id`, `synthetic`,
    `description`, `category` and `valuation_date`, and the case's expected
    files.
  - **May be invalid, missing or unknown:** `approach`,
    `calculation_currency_code`, `counterparties`, `netting_sets` and
    `hedges`, with their identifiers, links between items, keys, unit
    suffixes and values. A hedge for an unknown counterparty, a missing or
    unknown field, a duplicate identifier, a wrong type for a suffix or an
    amount without `currency_code` all reach the implementation, which must
    reject them.
  - The `description` names the input rule the case breaks.
- The status texts are fixed with the output contract. A rejection never
  substitutes a default value
  ([VBA_HOUSE_STYLE.md](../VBA_HOUSE_STYLE.md#contracts-units-and-errors)).
- Inputs JSON cannot express (non-finite numbers, wrong VBA types) are tested
  in a VBA test module instead of a fixture.

<a id="completeness-policy"></a>

## Completeness policy

- A rule in the [traceability](README.md#traceability) table is **validated**
  only when at least one `published` or `independent` case passes for it.
  `illustrative` cases never count.
- Each implemented rule also needs at least one `boundary` case, and each
  public input domain at least one `invalid` case, as a fixture or a VBA test.
- A harness run that does not execute every expected case and assertion is
  **incomplete, not a pass**
  ([#10](https://github.com/danielep71/K-CVA/issues/10)).
- A release states which rules are validated, under which version of the
  controlling text, and lists every rule that is implemented but not
  validated.

<a id="checking"></a>

## Checking

`tools/check_test_cases.py` runs as gate `test-cases` of
`python tools/check_repository.py` and checks the files under
`tests/fixtures/` and `tests/expected/`:

- strict JSON, with no duplicate key and only finite numbers, in every
  category;
- the harness metadata of every fixture, and, outside an `invalid` case, its
  calculation inputs: the approach and its hedges, identifiers and the links
  between counterparties, netting sets and hedges, keys, unit suffixes and
  value types, and currencies;
- each expected file's name, envelope and outputs: their scope against the
  fixture, form, unit, tolerance and rule ID; the reference class, its source
  against the [register](README.md#source-register) and its script; the
  calculation date against the
  [version applicability](README.md#version-applicability) table; the
  `illustrative-` naming rule; and a `_status` text output in every expected
  file of an `invalid` case.

It does not check:

- whether an input key or a quantity name belongs to the input and output
  contract, which does not exist yet;
- that an `invalid` case has no numeric output for what it rejects, or any
  link between its outputs and its inputs;
- any value: nothing is computed or compared. Running cases in Excel belongs
  to the VBA harness ([tests/README.md](../../tests/README.md#vba-harness)).
