# Getting Started with gp3sequencespy

```python
import pandas as pd
import gp3sequencespypy as g
```

## Purpose

`gp3sequencespypy` accepts ordinary long-format ordered categorical data. This
article introduces the complete structural workflow: audit, preparation,
encoding, descriptive summaries, contiguous motifs, distances, clustering,
consensus, group comparison, and transition structure.

All outputs are structural or statistical. They do not independently establish
attention, cognition, emotion, comprehension, intention, diagnosis, causality,
or other psychological attributes.

## Synthetic long-format data

Each sequence has an identifier, an explicit order, a categorical state, a
positive duration, participant metadata, and an assigned interface group.

```python
paths = {'s1': ['home', 'search', 'product', 'cart', 'checkout'], 's2': ['home', 'search', 'product', 'cart', 'home'], 's3': ['home', 'category', 'product', 'cart', 'checkout'], 's4': ['home', 'category', 'product', 'search', 'checkout'], 's5': ['home', 'category', 'search', 'product', 'checkout'], 's6': ['home', 'search', 'category', 'product', 'home'], 's7': ['home', 'category', 'product', 'cart', 'home'], 's8': ['home', 'search', 'product', 'checkout', 'home']}
groups = {'s1': 'interface_a', 's2': 'interface_a', 's3': 'interface_a', 's4': 'interface_a', 's5': 'interface_b', 's6': 'interface_b', 's7': 'interface_b', 's8': 'interface_b'}
rows = []
for i, (sid, states) in enumerate(paths.items(), start=1):
    for order, state in enumerate(states, start=1):
        rows.append({
            "sequence_id": sid, "sequence_order": order, "state": state,
            "duration": 80 + 10 * order + i, "participant_id": f"p{i:02d}",
            "group": groups[sid],
        })
raw_sequences = pd.DataFrame(rows)
raw_sequences.head()
```

## Audit, validate, and prepare

`audit_sequence_data()` returns a machine-readable issue table without
modifying the input. `validate_sequence_data()` adds a compact status contract.
`prepare_sequence_data()` applies explicit policies and returns canonical data,
an audit trail, and a decision log.

```python
audit = g.audit_sequence_data(
    raw_sequences, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant_id", "group"]
)
validation = g.validate_sequence_data(
    raw_sequences, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant_id", "group"]
)
prepared = g.prepare_sequence_data(
    raw_sequences, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant_id", "group"],
    missing_state_policy="error", duplicate_position_policy="error",
    repeated_state_policy="preserve", zero_duration_policy="preserve",
    unknown_state_policy="preserve", unused_state_levels="preserve",
)
print(validation.status, prepared.status)
prepared.data.head()
```

## Encode states and inspect basic structure

State codes are transparent identifiers derived from a deterministic state
ordering. The state, transition, and path helpers describe the observed
structure without assigning substantive meaning to the labels.

```python
encoded = g.encode_sequence_data(
    prepared.data, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant_id", "group"]
)
state_summary = g.summarise_sequence_states(
    prepared.data, "sequence_id", "sequence_order", "state",
    duration_col="duration", metadata_cols=["participant_id", "group"]
)
transition_summary = g.summarise_sequence_transitions(
    prepared.data, "sequence_id", "sequence_order", "state",
    metadata_cols=["participant_id", "group"], include_self=True
)
paths_table = g.format_sequence_paths(
    prepared.data, "sequence_id", "sequence_order", "state",
    metadata_cols=["participant_id", "group"]
)
print(encoded.dictionary)
print(state_summary.overall)
print(transition_summary.overall.head())
print(paths_table.paths)
```

## Discover contiguous motifs

Motifs are exact contiguous state windows. Their lengths, overlap rule,
prevalence denominator, filtering thresholds, and tie policy remain explicit.

```python
motif_occurrences = g.extract_sequence_ngrams(
    prepared.data, "sequence_id", "sequence_order", "state",
    metadata_cols=["group"], min_length=2, max_length=3, overlap="allow"
)
motif_summary = g.summarise_sequence_motifs(motif_occurrences)
motif_filter = g.filter_sequence_motifs(
    motif_summary, min_occurrences=2, min_sequences=2, min_prevalence=0.2,
    motif_lengths=[2, 3], top_n=10, rank_by="sequence_prevalence"
)
g.format_sequence_motifs(motif_filter, prevalence="percent", digits=1).table
```

## Compare sequences through distances and clustering

Distance choice is part of the analysis specification. This example uses LCS
distance followed by average-linkage hierarchical clustering. Validation
summaries describe the supplied solution; they do not prove that the clusters
are natural or substantively meaningful.

```python
lcs_distance = g.compute_sequence_distance(prepared.data, method="lcs", normalise="max_length")
cluster_fit = g.cluster_sequences(lcs_distance, k=2, method="hierarchical", linkage="average")
print(g.summarise_sequence_distance(lcs_distance)["overall"])
print(cluster_fit.assignments)
print(g.validate_sequence_clusters(cluster_fit)["overall"])
print(g.extract_representative_sequences(cluster_fit))
```

## Consensus and descriptive group comparison

Aligned-position consensus and group contrasts remain descriptive. The
consensus is not a behavioural norm, and contrasts do not establish a causal
mechanism.

```python
consensus = g.create_consensus_sequence(prepared.data, group_cols="group")
comparison = g.compare_sequence_groups(prepared.data, group_col="group")
print(g.summarise_consensus_agreement(consensus))
print(comparison.state.head())
```

## Transition structure

A first-order transition network summarises observed state-to-state movement.
Centrality and community outputs are graph descriptors, not measures of
attention, influence, preference, or intention.

```python
network = g.create_transition_network(prepared.data, normalise="from")
centrality = g.summarise_transition_centrality(network)
print(network.head())
print(centrality.head())
```

## Continue with focused articles

The package website contains focused articles for motif positions, consensus
and groups, distances and clustering, transition networks, latent models, and
optional ecosystem adapters. The method-selection article provides a compact
guide to choosing among them.
