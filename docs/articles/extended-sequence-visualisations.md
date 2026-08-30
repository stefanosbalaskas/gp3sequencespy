# Extended Sequence Visualisations

`gp3sequencespy` provides Matplotlib plotting helpers for package-native
sequence objects. Plots are intended to make structural results inspectable and
reportable; they do not change the underlying estimand or interpretation.

```python
import pandas as pd
import gp3sequencespy as g
```

## Synthetic data

```python
paths = {
    "s1": ["A", "B", "C", "B", "D", "A"],
    "s2": ["A", "C", "C", "D", "B", "A"],
    "s3": ["A", "B", "C", "B", "D", "A"],
    "s4": ["A", "C", "C", "D", "B", "A"],
    "s5": ["A", "B", "C", "B", "D", "A"],
    "s6": ["A", "C", "C", "D", "B", "A"],
}

rows = []
for sequence_id, states in paths.items():
    for sequence_order, state in enumerate(states, start=1):
        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_order": sequence_order,
                "state": state,
            }
        )

sequence_data = pd.DataFrame(rows)
```

## Sequence index

```python
ax = g.plot_sequence_index(sequence_data)
```

A sequence-index view preserves the observed order of states for each sequence
and is useful for inspecting heterogeneity before aggregating.

## State distribution and entropy

```python
ax = g.plot_sequence_state_distribution(sequence_data)
```

```python
ax = g.plot_sequence_entropy(sequence_data)
```

Entropy is a structural diversity summary at aligned positions. It is not a
measure of participant uncertainty, cognitive load, or confidence.

## Distance heatmap and cluster silhouette

```python
distance = g.compute_sequence_distance(sequence_data, method="lcs")
ax = g.plot_sequence_distance_heatmap(distance)
```

```python
clustering = g.cluster_sequences(distance, k=2)
ax = g.plot_sequence_cluster_silhouette(clustering, distance)
```

## Transition network

```python
network = g.create_transition_network(sequence_data, normalise="from")
ax = g.plot_transition_network(network)
```

## Plotting contract

The frozen plotting signatures are retained, with the documented Python-native
keyword-only `ax=` extension for composition into an existing Matplotlib axes.
Rendering is Matplotlib-native rather than pixel-identical to base R.

See the [full plot gallery](../plots.md) for all 15 plotting helpers, figure
families, code templates, and reporting guidance.
