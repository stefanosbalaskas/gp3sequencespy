# Design-Aware Sequence Group Inference

```python
import pandas as pd
import gp3sequencespy as g
```

## Why declare the design?

Sequence rows are rarely independent. The comparison API requires the group
column and independent unit, and can additionally record pairs or assignment
clusters. It aggregates the selected metric before permutation or bootstrap
resampling.

## Synthetic randomized groups

```python
import numpy as np
rng = np.random.default_rng(42)
rows=[]
for i in range(20):
    group = "control" if i < 10 else "treatment"
    states = rng.choice(["A","B","C"], size=6, replace=True)
    for order,state in enumerate(states,1):
        rows.append({"participant_id":f"p{i+1:02d}","sequence_id":f"s{i+1:02d}","sequence_order":order,"state":state,"group":group})
data=pd.DataFrame(rows)
```

## Declare and test

```python
design = g.declare_sequence_comparison_design(
    group_col="group", unit_col="participant_id", design="randomized"
)
result = g.test_sequence_group_difference(
    data, design, metric="sequence_length", n_permutations=999, seed=11
)
g.summarise_sequence_group_inference(result)
```

Supported metrics are deliberately limited to transparent quantities:
sequence length, transition count, state prevalence, and declared subsequence
presence.

## Bootstrap interval

```python
result = g.bootstrap_sequence_group_difference(result, n_boot=999, level=0.95, seed=11)
g.summarise_sequence_group_inference(result)
```

```python
g.plot_sequence_group_inference(result, type="permutation")
g.plot_sequence_group_inference(result, type="group_means")
```

## Causal language

For `design = "randomized"`, causal interpretation still depends on valid
assignment, implementation, attrition handling, and an estimand consistent with
the design. For `design = "observational"`, the output explicitly describes an
associational exchangeability-based contrast and does not license causal claims.
