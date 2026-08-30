# Plot gallery

`gp3sequencespy` exposes a compact family of Matplotlib plotting helpers for
sequence structure, model diagnostics, group comparisons, and transition
networks.

The SVG thumbnails below are **documentation illustrations** of the visual
families. The adjacent Python snippets are the package calls to reproduce the
corresponding plot type from real analysis objects.

## Shared setup

```python
import pandas as pd
import gp3sequencespy as g

paths = {
    "s1": ["A", "A", "B", "C", "D", "D"],
    "s2": ["A", "B", "B", "C", "C", "D"],
    "s3": ["A", "A", "C", "C", "B", "D"],
    "s4": ["A", "B", "C", "D", "D", "D"],
    "s5": ["D", "C", "C", "B", "B", "A"],
    "s6": ["D", "C", "B", "B", "A", "D"],
}

rows = []
for sequence_id, states in paths.items():
    for sequence_order, state in enumerate(states, 1):
        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_order": sequence_order,
                "state": state,
            }
        )

data = pd.DataFrame(rows)
distance = g.compute_sequence_distance(data, method="lcs")
network = g.create_transition_network(data, normalise="from")
```

## Sequence index

![Illustrative sequence index](assets/figures/sequence-index.svg)

Use sequence-index views when the ordering of states within individual
sequences is itself informative.

```python
ax = g.plot_sequence_index(data)
```

**Read it as:** a compact view of ordered categorical paths.

**Do not read it as:** evidence that one path is inherently better, more
attentive, more efficient, or more cognitive than another.

## State distribution

![Illustrative state distribution](assets/figures/state-distribution.svg)

Position-wise distributions are useful when aligned positions are meaningfully
comparable across sequences.

```python
ax = g.plot_sequence_state_distribution(data)
```

Use `plot_sequence_entropy()` to display structural diversity across aligned
positions:

```python
ax = g.plot_sequence_entropy(data)
```

## Distance heatmap

![Illustrative distance heatmap](assets/figures/distance-heatmap.svg)

The heatmap is a diagnostic view of the pairwise geometry implied by the
declared distance method.

```python
ax = g.plot_sequence_distance_heatmap(distance)
```

Report the distance family, normalisation, and any edit / substitution costs
with the figure.

## Cluster silhouette

```python
clusters = g.cluster_sequences(
    distance,
    k=2,
    method="hierarchical",
    linkage="average",
)

ax = g.plot_sequence_cluster_silhouette(
    clusters,
    distance,
)
```

Silhouette structure is conditional on the distance representation and supplied
clustering solution.

## Transition network

![Illustrative transition network](assets/figures/transition-network.svg)

```python
ax = g.plot_transition_network(network)
```

Graph nodes are categorical states and directed edges summarise observed
transition structure. Centrality is a graph descriptor, not a direct measure of
attention, influence, preference, or importance.

## Consensus sequence

```python
consensus = g.create_consensus_sequence(data)
ax = g.plot_consensus_sequence(consensus)
```

A consensus plot is an aligned structural summary, not a normative trajectory.

## Group comparison

```python
comparison = g.compare_sequence_groups(
    data.assign(group=["a"] * 18 + ["b"] * 18),
    group_col="group",
)

ax = g.plot_sequence_group_comparison(comparison)
```

For inferential output:

```python
group_map = {
    "s1": "a",
    "s2": "a",
    "s3": "a",
    "s4": "b",
    "s5": "b",
    "s6": "b",
}
participant_map = {
    sequence_id: f"p{i:02d}"
    for i, sequence_id in enumerate(paths, start=1)
}

grouped = data.assign(
    group=data["sequence_id"].map(group_map),
    participant_id=data["sequence_id"].map(participant_map),
)

design = g.declare_sequence_comparison_design(
    group_col="group",
    unit_col="participant_id",
    design="randomized",
)

inference = g.test_sequence_group_difference(
    grouped,
    design=design,
    metric="sequence_length",
    n_permutations=199,
    seed=7,
)

ax = g.plot_sequence_group_inference(inference)
```

## Motifs and motif positions

```python
occurrences = g.extract_sequence_ngrams(
    data,
    min_length=2,
    max_length=3,
)

motifs = g.summarise_sequence_motifs(occurrences)

ax = g.plot_sequence_motifs(motifs)
ax_positions = g.plot_sequence_motif_positions(occurrences)
```

## Non-contiguous subsequences

```python
subsequences = g.extract_sequence_subsequences(
    data,
    min_length=2,
    max_length=3,
)

summary = g.summarise_sequence_subsequences(subsequences)
ax = g.plot_sequence_subsequences(summary)
```

## Longitudinal / panel changes

```python
# `panel` is the object returned by prepare_sequence_panel(...)
# ax = g.plot_sequence_panel_changes(panel_comparison)
```

Use the [longitudinal article](articles/longitudinal-panel-sequences.md) for a
complete panel-data example.

## Latent-model plots

Multichannel HMM:

```python
# model = g.fit_multichannel_sequence_hmm(...)
# ax = g.plot_multichannel_sequence_hmm(model)
```

Time-varying transition model:

```python
# model = g.fit_time_varying_sequence_model(...)
# ax = g.plot_time_varying_sequence_model(model)
```

The commented calls are templates because those model families require
additional input structure beyond the compact shared example above.

## Complete plotting API

The frozen plotting surface contains:

- `plot_consensus_sequence()`
- `plot_multichannel_sequence_hmm()`
- `plot_sequence_cluster_silhouette()`
- `plot_sequence_distance_heatmap()`
- `plot_sequence_entropy()`
- `plot_sequence_group_comparison()`
- `plot_sequence_group_inference()`
- `plot_sequence_index()`
- `plot_sequence_motif_positions()`
- `plot_sequence_motifs()`
- `plot_sequence_panel_changes()`
- `plot_sequence_state_distribution()`
- `plot_sequence_subsequences()`
- `plot_time_varying_sequence_model()`
- `plot_transition_network()`

Each helper accepts a Python-only keyword-only `ax=` extension where documented,
so plots can be composed into a larger Matplotlib figure without changing the
frozen R-facing scientific semantics.

## Figure reporting checklist

- state the exact analysis object plotted;
- report distance / normalisation / clustering settings where relevant;
- explain grouping and weighting;
- state whether positions are aligned;
- report randomization / bootstrap settings for inferential or stability plots;
- treat colors and layouts as visual encodings, not substantive categories;
- keep the structural interpretation separate from psychological or causal
  claims.
