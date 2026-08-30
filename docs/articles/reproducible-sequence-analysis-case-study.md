# Reproducible Sequence Analysis: A Synthetic Case Study

This worked example combines the package layers into one auditable analysis.
The scenario is synthetic: two assigned interface conditions with observed
navigation-state sequences.

```python
import pandas as pd
import gp3sequencespy as g
```

## 1. Build the study table

```python
paths = {
    "s01": ["home", "search", "product", "cart", "checkout", "confirmation"],
    "s02": ["home", "search", "product", "reviews", "cart", "checkout"],
    "s03": ["home", "category", "product", "cart", "checkout", "confirmation"],
    "s04": ["home", "search", "product", "cart", "checkout", "home"],
    "s05": ["home", "category", "search", "product", "cart", "checkout"],
    "s06": ["home", "search", "category", "product", "checkout", "confirmation"],
    "s07": ["home", "category", "product", "reviews", "cart", "checkout"],
    "s08": ["home", "search", "product", "reviews", "checkout", "confirmation"],
    "s09": ["home", "category", "product", "cart", "home", "search"],
    "s10": ["home", "search", "product", "cart", "checkout", "confirmation"],
    "s11": ["home", "category", "search", "product", "checkout", "confirmation"],
    "s12": ["home", "search", "category", "product", "cart", "checkout"],
}
groups = {
    sequence_id: "interface_a" if int(sequence_id[1:]) <= 6 else "interface_b"
    for sequence_id in paths
}

rows = []
for sequence_id, states in paths.items():
    for sequence_order, state in enumerate(states, start=1):
        rows.append(
            {
                "participant_id": f"p{int(sequence_id[1:]):02d}",
                "sequence_id": sequence_id,
                "sequence_order": sequence_order,
                "state": state,
                "group": groups[sequence_id],
            }
        )

sequence_data = pd.DataFrame(rows)
```

## 2. Prespecify preparation

```python
audit = g.audit_sequence_data(
    sequence_data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["participant_id", "group"],
)
prepared = g.prepare_sequence_data(
    sequence_data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["participant_id", "group"],
    missing_state_policy="error",
    duplicate_position_policy="error",
)
print(prepared.status)
```

## 3. Structural summaries

```python
state_summary = g.summarise_sequence_states(
    prepared.data,
    metadata_cols=["group"],
)
paths_table = g.format_sequence_paths(
    prepared.data,
    metadata_cols=["group"],
)
print(state_summary.overall)
print(paths_table.paths.head())
```

## 4. Motifs

```python
motifs = g.extract_sequence_ngrams(
    prepared.data,
    metadata_cols=["group"],
    min_length=2,
    max_length=3,
)
motif_summary = g.summarise_sequence_motifs(motifs)
frequent_motifs = g.filter_sequence_motifs(
    motif_summary,
    min_sequences=2,
    top_n=12,
)
```

## 5. Consensus and group descriptions

```python
consensus = g.create_consensus_sequence(prepared.data, group_cols="group")
comparison = g.compare_sequence_groups(prepared.data, group_col="group")
print(g.summarise_consensus_agreement(consensus))
print(comparison.state.head())
```

## 6. Distance, clustering, and stability

```python
distance = g.compute_sequence_distance(
    prepared.data,
    method="lcs",
    normalise="max_length",
)
clusters = g.cluster_sequences(
    distance,
    k=2,
    linkage="average",
)
stability = g.bootstrap_sequence_clusters(
    distance,
    k=2,
    n_boot=100,
    sample_fraction=0.8,
    seed=11,
)

print(g.validate_sequence_clusters(clusters)["overall"])
print(g.summarise_sequence_cluster_stability(stability)["overall"])
print(g.extract_representative_sequences(clusters))
```

## 7. Transition structure and recent context

```python
network = g.create_transition_network(prepared.data, normalise="from")
context_model = g.fit_higher_order_transition_model(
    prepared.data,
    order=2,
    smoothing=0.5,
)
print(g.summarise_transition_centrality(network).head())
print(g.predict_next_state(context_model, ["home", "search"], top_n=3))
```

## 8. Optional latent-model sensitivity

```python
one_state = g.fit_sequence_hmm(prepared.data, n_states=1, max_iter=50, seed=7)
two_state = g.fit_sequence_hmm(prepared.data, n_states=2, max_iter=50, seed=7)
print(g.compare_sequence_hmms(one_state, two_state))
```

## 9. Design-aware contrast

Because the scenario declares assigned conditions, the analysis can state the
randomization contract explicitly. The validity of causal language would still
depend on actual assignment and implementation in a real study.

```python
design = g.declare_sequence_comparison_design(
    group_col="group",
    unit_col="participant_id",
    design="randomized",
)
inference = g.test_sequence_group_difference(
    prepared.data,
    design,
    metric="sequence_length",
    n_permutations=999,
    seed=11,
)
print(g.summarise_sequence_group_inference(inference))
```

## 10. Assemble an auditable evidence object

```python
evidence = {
    "preparation_status": prepared.status,
    "state_summary": state_summary.overall,
    "motifs": frequent_motifs.table,
    "cluster_validation": g.validate_sequence_clusters(clusters)["overall"],
    "network": network,
    "distance_audit": g.audit_sequence_analysis(distance).summary,
}
print(evidence.keys())
```

## Interpretation boundary

This workflow documents observed paths, motif recurrence, descriptive condition
contrasts, distance geometry, cluster stability, transition structure,
recent-context probabilities, and latent statistical summaries. None of these
outputs independently identifies attention, preference, comprehension, emotion,
cognition, intention, diagnosis, deception, or a causal mechanism.

For a manuscript-ready checklist, continue to the [reporting guide](../reporting.md).
