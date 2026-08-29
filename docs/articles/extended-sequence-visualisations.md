# Extended Sequence Visualisations

```python
import pandas as pd
import gp3sequencespypy as g
```

## Synthetic data

```python
paths = {'s1': ['A', 'B', 'C', 'B', 'D', 'A'], 's2': ['A', 'C', 'C', 'D', 'B', 'A'], 's3': ['A', 'B', 'C', 'B', 'D', 'A'], 's4': ['A', 'C', 'C', 'D', 'B', 'A'], 's5': ['A', 'B', 'C', 'B', 'D', 'A'], 's6': ['A', 'C', 'C', 'D', 'B', 'A'], 's7': ['A', 'B', 'C', 'B', 'D', 'A'], 's8': ['A', 'C', 'C', 'D', 'B', 'A']}
groups = None
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## Sequence index

```python
ax = g.plot_sequence_index(sequence_data)
```

## State distribution and entropy

```python
ax = g.plot_sequence_state_distribution(sequence_data)
```

```python
ax = g.plot_sequence_entropy(sequence_data)
```

Entropy is a structural diversity summary at each aligned position. It is not a
measure of participant uncertainty or cognition.

## Distance and clustering diagnostics

```python
distance = g.compute_sequence_distance(sequence_data)
ax = g.plot_sequence_distance_heatmap(distance)
```

```python
clustering = g.cluster_sequences(distance, 2)
ax = g.plot_sequence_cluster_silhouette(clustering, distance)
```

## Transition network

```python
network = g.create_transition_network(sequence_data, normalise="from")
ax = g.plot_transition_network(network)
```

These base-R plots are intentionally focused on package-native audited objects.
They complement, rather than replace, specialist visualisation ecosystems.
