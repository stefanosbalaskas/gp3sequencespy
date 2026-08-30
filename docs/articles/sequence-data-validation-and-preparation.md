# Sequence Data Validation and Preparation

Ordered categorical data can contain missing states, duplicated positions,
unsorted rows, repeated states, zero durations, unknown levels, and metadata
inconsistencies. Silent repair can change the analytical object, so
`gp3sequencespy` separates audit, validation, and policy-driven preparation.

```python
import pandas as pd
import gp3sequencespy as g
```

## A deliberately problematic input

```python
problem_data = pd.DataFrame(
    {
        "sequence_id": ["s2", "s1", "s1", "s1", "s1", "s2", "s2", "s2"],
        "sequence_order": [2, 2, 1, 2, 3, 1, 3, 4],
        "state": ["B", "B", "A", "B", None, "A", "B", "C"],
        "duration": [100, 120, 110, 125, 90, 100, 0, 130],
        "participant": ["p2", "p1", "p1", "p1", "p1", "p2", "p2", "p2"],
    }
)
```

The table includes a duplicated position in `s1`, a missing state, unsorted
input, and a zero-duration event.

## Audit without modification

```python
audit = g.audit_sequence_data(
    problem_data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant"],
)
print(audit)
```

The audit uses stable issue codes and severity classes and does not modify the
input.

## Compact validation contract

```python
validation = g.validate_sequence_data(
    problem_data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant"],
)
print(validation.status)
print(validation.audit)
```

Review-level issues do not automatically invalidate a data set. Error-level
issues require source correction or a supported explicit preparation policy.

## Apply explicit policies

Here we choose to drop missing states, retain the first duplicated position,
collapse consecutive repeats, and drop zero-duration rows. These are analysis
choicesβ€”not universal defaults.

```python
prepared = g.prepare_sequence_data(
    problem_data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant"],
    missing_state_policy="drop",
    duplicate_position_policy="first",
    repeated_state_policy="collapse",
    zero_duration_policy="drop",
)

print(prepared.status)
print(prepared.decisions)
print(prepared.data)
```

`prepare_sequence_data()` sorts deterministically and records original-row
provenance. When repeated states are collapsed and durations are available,
available run durations are summed according to the package contract.

## Unknown states and declared state sets

If the study has a prespecified state set, pass `expected_states=` and choose an
explicit `unknown_state_policy` (`preserve`, `drop`, or `error`). Categorical
unused levels can likewise be preserved or dropped explicitly.

## Revalidate the prepared result

```python
revalidation = g.validate_sequence_data(
    prepared.data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant"],
)
print(revalidation.status)
```

## Conditions that require source correction

The package intentionally refuses to silently repair several high-risk input
problems, including missing identifiers, missing/non-finite order values,
negative/non-finite durations, duplicated column names, invalid mapped column
types, and metadata that varies within a sequence.

## What to report

Retain and report:

- the original column mapping;
- expected states, if declared;
- every preparation policy;
- input audit and decision log;
- input/prepared row counts;
- final state levels;
- exclusions or source corrections made outside the package.

Continue with the [quickstart](../quickstart.md) or the
[reporting guide](../reporting.md).
