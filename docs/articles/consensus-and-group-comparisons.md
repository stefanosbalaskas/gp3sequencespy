# Consensus Sequences and Descriptive Group Comparisons

```python
import pandas as pd
import gp3sequencespypy as g
```

## Scope

This workflow describes aligned states and differences in observed sequence
structure. A consensus is not a behavioural norm, and a between-group
difference is not evidence of a psychological or causal mechanism.

## Synthetic sequences

```python
paths = {'s1': ['home', 'search', 'product', 'checkout'], 's2': ['home', 'search', 'product', 'home'], 's3': ['home', 'category', 'product', 'checkout'], 's4': ['home', 'category', 'search', 'checkout'], 's5': ['home', 'search', 'product', 'checkout'], 's6': ['home', 'category', 'product', 'home']}
groups = {'s1': 'interface_a', 's2': 'interface_a', 's3': 'interface_a', 's4': 'interface_b', 's5': 'interface_b', 's6': 'interface_b'}
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
    if groups is not None:
        row["group"] = groups[sid]
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## Aligned-position consensus

```python
consensus = g.create_consensus_sequence(sequence_data, group_cols="group")
consensus
```

```python
ax = g.plot_consensus_sequence(consensus, type="agreement", group="interface_a")
```

## Descriptive group comparison

```python
comparison = g.compare_sequence_groups(sequence_data, group_col="group")
comparison.state.head()
```

```python
ax = g.plot_sequence_group_comparison(comparison, component="state", top_n=5)
```

The output reports counts, shares, prevalence, differences, and ratios. It does
not compute a significance test or automatically rank one group as preferable.
