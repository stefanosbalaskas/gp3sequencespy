# Getting Started with gp3sequencespy

This article walks through the core structural workflow with ordinary
long-format categorical data: audit, validation, preparation, summaries,
motifs, distances, clustering, consensus, groups, transitions, and plots.

```python
import pandas as pd
import gp3sequencespy as g
```

!!! warning "Interpret structure as structure"
    The package describes and models ordered categorical structure. Outputs do
    not independently establish attention, cognition, emotion, comprehension,
    intention, diagnosis, or causality.

## Build a small long-format data set

Each row represents one observed state occurrence. Sequence identity and order
are explicit columns rather than assumptions about row order.

```python
paths = {
    "s1": ["home", "search", "product", "cart", "checkout"],
    "s2": ["home", "search", "product", "cart", "home"],
    "s3": ["home", "category", "product", "cart", "checkout"],
    "s4": ["home", "category", "search", "product", "checkout"],
}
groups = {"s1": "A", "s2": "A", "s3": "B", "s4": "B"}

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

data = pd.DataFrame(rows)
```

## Audit, validate, and prepare

Use the non-modifying audit first. `prepare_sequence_data()` then makes any
repair policy explicit and returns both canonical data and a decision log.

```python
audit = g.audit_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["group"],
)
validation = g.validate_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["group"],
)
prepared = g.prepare_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["group"],
)

print(validation.status)
print(prepared.decisions)
```

## Describe observed states, transitions, and paths

```python
states = g.summarise_sequence_states(prepared.data)
transitions = g.summarise_sequence_transitions(prepared.data)
paths_table = g.format_sequence_paths(prepared.data)

print(states.overall)
print(transitions.overall.head())
print(paths_table.paths)
```

## Find recurring contiguous motifs

```python
occurrences = g.extract_sequence_ngrams(
    prepared.data,
    min_length=2,
    max_length=3,
    metadata_cols=["group"],
)
summary = g.summarise_sequence_motifs(occurrences)
frequent = g.filter_sequence_motifs(
    summary,
    min_sequences=2,
    top_n=10,
)
print(g.format_sequence_motifs(frequent).table)
```

## Compare whole sequences

The distance choice is part of the analysis specification. Here the example
uses longest-common-subsequence distance and an average-linkage two-cluster
solution.

```python
distance = g.compute_sequence_distance(
    prepared.data,
    method="lcs",
    normalise="max_length",
)
clusters = g.cluster_sequences(
    distance,
    k=2,
    method="hierarchical",
    linkage="average",
)

print(g.summarise_sequence_distance(distance)["overall"])
print(g.validate_sequence_clusters(clusters)["overall"])
print(g.extract_representative_sequences(clusters))
```

## Consensus and descriptive group structure

```python
consensus = g.create_consensus_sequence(prepared.data, group_cols="group")
comparison = g.compare_sequence_groups(prepared.data, group_col="group")

print(g.summarise_consensus_agreement(consensus))
print(comparison.state.head())
```

A consensus is a modal aligned-position summary, not an ideal or normative path.
Descriptive group differences do not become causal merely because groups have
labels.

## Transition networks

```python
network = g.create_transition_network(prepared.data, normalise="from")
centrality = g.summarise_transition_centrality(network)
communities = g.detect_transition_communities(network)

print(network.head())
print(centrality.head())
print(communities.head())
```

## Plot the structure

```python
ax = g.plot_sequence_index(prepared.data)
```

```python
ax = g.plot_sequence_state_distribution(prepared.data)
```

```python
ax = g.plot_sequence_distance_heatmap(distance)
```

See the [plot gallery](../plots.md) for the full visualisation family.

## Audit the analysis object

Analysis audits retain structural provenance for supported package-native
objects.

```python
analysis_audit = g.audit_sequence_analysis(distance)
print(analysis_audit.summary)
```

## Continue

- [Choose a sequence-analysis method](choosing-a-sequence-analysis-method.md)
- [Practical examples](../examples.md)
- [Plot gallery](../plots.md)
- [Reporting guide](../reporting.md)
- [Frozen public API](../reference/api.md)
