# Sequence Data Validation and Preparation

```python
import pandas as pd
import gp3sequencespypy as g
```

## Why preparation is explicit

Ordered categorical data can contain missing states, duplicated positions,
unsorted rows, consecutive repeats, zero durations, unknown states, and
inconsistent metadata. Silent repair can change the analytical object.
`gp3sequencespypy` therefore separates non-modifying audit and validation from
policy-driven preparation.

## A deliberately problematic synthetic input

The example includes an unsorted sequence, a duplicated position, a missing
state, a consecutive repeat, a zero duration, an unexpected state, and an
unused factor level. Participant and group metadata remain constant within
each sequence.

```python
problem_data = pd.DataFrame({
    "sequence_id": ["s2","s1","s1","s1","s1","s2","s2","s2","s2"],
    "sequence_order": [2,2,1,2,3,1,2,3,4],
    "state": ["B","B","A","B",None,"A","B","B","C"],
    "duration": [100,120,110,125,90,100,100,0,130],
    "participant": ["p2","p1","p1","p1","p1","p2","p2","p2","p2"],
})
```

## Audit without modification

`audit_sequence_data()` reports one row per issue using stable issue codes and
severity values. It does not repair the data.

```python
audit = g.audit_sequence_data(
    problem_data, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant"]
)
audit
```

## Compact validation contract

A review-level issue does not automatically invalidate an input. Error-level
issues must be resolved through source correction or an explicit supported
policy.

```python
validation = g.validate_sequence_data(
    problem_data, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant"]
)
print(validation.status)
print(validation.audit)
```

## Apply explicit preparation policies

This example deliberately chooses to:

- drop rows with missing states;
- retain the first row at duplicated positions;
- collapse consecutive repeated states;
- drop zero-duration rows;
- drop states absent from the declared state set;
- drop unused factor levels.

These are analytical choices, not universal defaults.

```python
prepared = g.prepare_sequence_data(
    problem_data, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant"],
    missing_state_policy="drop", duplicate_position_policy="first",
    repeated_state_policy="preserve", zero_duration_policy="preserve"
)
print(prepared.status)
print(prepared.decisions)
prepared.data
```

## Revalidate the canonical result

The prepared table uses stable canonical columns while preserving unmapped
metadata and original-row provenance.

```python
revalidation = g.validate_sequence_data(
    prepared.data, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant"]
)
revalidation.status
```

## Errors that require source correction

Some conditions are intentionally not repaired automatically. Examples include
missing sequence identifiers, missing or non-finite order values, negative or
non-finite durations, absent mapped columns, duplicated column names, invalid
column types, and metadata that varies within a sequence. These conditions
require correction or an explicit redefinition of the sequence unit.

## Reporting recommendations

A reproducible report should record the input mapping, expected states, every
preparation policy, the audit table, the decision log, original and prepared
row counts, and the final state levels. These records describe data handling;
they do not validate a substantive interpretation of the resulting sequence
patterns.
