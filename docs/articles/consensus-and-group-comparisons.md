# Consensus Sequences and Descriptive Group Comparisons

This workflow describes aligned states and observed differences between groups.
A consensus is not a behavioural norm, and descriptive group differences are
not evidence of a causal or psychological mechanism.

```python
import pandas as pd
import gp3sequencespy as g
```

## Synthetic grouped sequences

```python
paths = {
    "s1": ["home", "search", "product", "checkout"],
    "s2": ["home", "search", "product", "home"],
    "s3": ["home", "category", "product", "checkout"],
    "s4": ["home", "category", "search", "checkout"],
    "s5": ["home", "search", "product", "checkout"],
    "s6": ["home", "category", "product", "home"],
}
groups = {
    "s1": "interface_a",
    "s2": "interface_a",
    "s3": "interface_a",
    "s4": "interface_b",
    "s5": "interface_b",
    "s6": "interface_b",
}

rows = []
for sequence_id, states in paths.items():
    for sequence_order, state in enumerate(states, start=1):
        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_order": sequence_order,
                "state": state,
                "group": groups[sequence_id],
            }
        )

sequence_data = pd.DataFrame(rows)
```

## Aligned-position consensus

```python
consensus = g.create_consensus_sequence(
    sequence_data,
    group_cols="group",
)
print(g.summarise_consensus_agreement(consensus))
```

```python
ax = g.plot_consensus_sequence(
    consensus,
    type="agreement",
    group="interface_a",
)
```

Aligned-position consensus assumes the position index is comparable across
sequences. If positions do not have a defensible alignment, use path, motif, or
distance representations instead.

## Descriptive group comparison

```python
comparison = g.compare_sequence_groups(
    sequence_data,
    group_col="group",
)
print(comparison.state.head())
```

```python
ax = g.plot_sequence_group_comparison(
    comparison,
    component="state",
    top_n=5,
)
```

The comparison layer reports observed structural contrasts. If the research
question is inferential, use the separate design-aware workflow rather than
interpreting this descriptive result as a significance test.

## When inference is justified

```python
design = g.declare_sequence_comparison_design(
    group_col="group",
    unit_col="sequence_id",
    design="observational",
)
```

For observational designs, the interpretation remains associational. See
[Design-Aware Sequence Group Inference](sequence-inference-and-randomization.md)
for permutation-based testing and explicit randomization contracts.

## Reporting checklist

Report the alignment rule, grouping variable, support/weighting policy, tie
handling, missing-position policy, and whether the comparison is descriptive or
inferential.
