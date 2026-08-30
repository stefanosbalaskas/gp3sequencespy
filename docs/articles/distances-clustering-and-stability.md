# Sequence Distances, Clustering, and Stability

```python
import pandas as pd
import gp3sequencespy as g
```

## Synthetic paths

```python
paths = {'s1': ['A', 'B', 'C', 'D'], 's2': ['A', 'B', 'C', 'C'], 's3': ['A', 'C', 'C', 'D'], 's4': ['D', 'C', 'B', 'A'], 's5': ['D', 'C', 'C', 'A'], 's6': ['D', 'B', 'C', 'A']}
groups = None
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## Transparent distance families

```python
levenshtein = g.compute_sequence_distance(sequence_data, method="levenshtein")
lcs = g.compute_sequence_distance(sequence_data, method="lcs")
om = g.compute_sequence_distance(sequence_data, method="optimal_matching")
transition = g.compute_sequence_distance(sequence_data, method="transition")
```

The distance method and all costs are retained as object attributes. The
transition method compares first-order transition-probability profiles; it is
not a general stochastic-process model.

## Clustering and validation

```python
fit = g.cluster_sequences(lcs, k=2, method="hierarchical", linkage="average")
print(fit.assignments)
print(g.validate_sequence_clusters(fit)["overall"])
print(g.extract_representative_sequences(fit, n_per_cluster=1))
```

## Subsampling stability

```python
stability = g.bootstrap_sequence_clusters(lcs, k=2, n_boot=100, sample_fraction=0.8, seed=11)
g.summarise_sequence_cluster_stability(stability)["overall"]
```

Cluster stability describes reproducibility under the selected resampling and
clustering settings. It does not establish that the clusters are natural,
causal, or substantively meaningful.

## Co-association ensemble

```python
transition_fit = g.cluster_sequences(transition, k=2)
ensemble = g.create_sequence_cluster_ensemble(fit, transition_fit, k=2)
ensemble.assignments
```

The ensemble records how often pairs are assigned together across supplied
solutions. It does not automatically validate the number or meaning of
clusters.

## Optional PAM and CLARA interfaces

```python
pam_fit = g.cluster_sequences(lcs, k=2, method="pam", seed=11)
clara_fit = g.cluster_sequences(lcs, k=2, method="clara", seed=11, samples=5)
```

PAM uses the supplied dissimilarities directly. CLARA uses a documented
classical multidimensional-scaling embedding because `cluster::clara()`
expects observations rather than a dissimilarity object.
