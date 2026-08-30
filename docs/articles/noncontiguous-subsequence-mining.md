# Bounded Non-Contiguous Subsequence Mining

```python
import pandas as pd
import gp3sequencespy as g
```

## Why bounded subsequences?

A non-contiguous subsequence preserves order while allowing intervening states.
The implementation requires explicit motif length, maximum gap, maximum span,
and combination limits. These constraints keep enumeration auditable and avoid
silently searching an unbounded combinatorial space.

## Synthetic sequences

```python
sequences = pd.DataFrame({
    "sequence_id": [f"s{i}" for i in range(1, 7) for _ in range(5)],
    "sequence_order": list(range(1, 6)) * 6,
    "state": list("ABCDE") + list("ABCED") + list("ACBDE") + list("ABCDE") + list("BACDE") + list("ABCDE"),
    "group": ["g1"] * 15 + ["g2"] * 15,
})
```

## Enumerate occurrences

```python
occurrences = g.extract_sequence_subsequences(
    sequences, metadata_cols="group", min_length=2, max_length=3, max_gap=1, max_span=4
)
occurrences.head()
```

## Sequence-level prevalence

```python
subsequence_summary = g.summarise_sequence_subsequences(occurrences)
frequent = g.filter_sequence_subsequences(
    subsequence_summary, min_sequences=2, min_prevalence=0.2, top_n=10
)
frequent
```

## Group comparison

```python
comparison = g.compare_sequence_subsequences(occurrences, group_col="group")
comparison.head()
```

The comparison is based on sequence-level presence, not occurrence multiplicity.
Adjusted p-values do not turn an observational grouping into a causal design.

```python
ax = g.plot_sequence_subsequences(frequent, metric="sequence_prevalence")
```

## Relation to specialist packages

The bounded enumerator is intentionally narrow. Large-scale frequent sequence
mining, event-sequence constraint systems, and discriminating-subsequence
algorithms remain appropriate uses of specialist packages through explicit
adapters.
