# Examples

These recipes use small synthetic data so the analysis contract is visible.
Adapt column names, grouping variables, and tuning choices to the actual study
design.

## Shared synthetic data

```python
import pandas as pd
import gp3sequencespy as g

paths = {
    "s1": ["home", "search", "product", "cart", "checkout"],
    "s2": ["home", "search", "product", "cart", "home"],
    "s3": ["home", "category", "product", "cart", "checkout"],
    "s4": ["home", "category", "product", "search", "checkout"],
    "s5": ["home", "category", "search", "product", "checkout"],
    "s6": ["home", "search", "category", "product", "home"],
    "s7": ["home", "category", "product", "cart", "home"],
    "s8": ["home", "search", "product", "checkout", "home"],
}

groups = {
    "s1": "interface_a",
    "s2": "interface_a",
    "s3": "interface_a",
    "s4": "interface_a",
    "s5": "interface_b",
    "s6": "interface_b",
    "s7": "interface_b",
    "s8": "interface_b",
}

rows = []
for participant_number, (sequence_id, states) in enumerate(paths.items(), 1):
    for sequence_order, state in enumerate(states, 1):
        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_order": sequence_order,
                "state": state,
                "duration": 80 + 10 * sequence_order + participant_number,
                "participant_id": f"p{participant_number:02d}",
                "group": groups[sequence_id],
            }
        )

data = pd.DataFrame(rows)
```

## Recipe 1 — Validation and preparation

```python
audit = g.audit_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant_id", "group"],
)

validation = g.validate_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant_id", "group"],
)

prepared = g.prepare_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant_id", "group"],
    missing_state_policy="error",
    duplicate_position_policy="error",
    repeated_state_policy="preserve",
    zero_duration_policy="preserve",
    unknown_state_policy="preserve",
    unused_state_levels="preserve",
)

print(validation.status)
print(prepared.data.head())
```

**Report:** sequence unit, ordering field, state vocabulary, duration treatment,
and every non-default preparation policy.

## Recipe 2 — State and transition summaries

```python
state_summary = g.summarise_sequence_states(
    prepared.data,
    "sequence_id",
    "sequence_order",
    "state",
    duration_col="duration",
    metadata_cols=["participant_id", "group"],
)

transition_summary = g.summarise_sequence_transitions(
    prepared.data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["participant_id", "group"],
    include_self=True,
)

paths_table = g.format_sequence_paths(
    prepared.data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["participant_id", "group"],
)
```

## Recipe 3 — Motifs

```python
occurrences = g.extract_sequence_ngrams(
    prepared.data,
    "sequence_id",
    "sequence_order",
    "state",
    metadata_cols=["group"],
    min_length=2,
    max_length=3,
    overlap="allow",
)

motif_summary = g.summarise_sequence_motifs(occurrences)

motif_filter = g.filter_sequence_motifs(
    motif_summary,
    min_occurrences=2,
    min_sequences=2,
    min_prevalence=0.2,
    motif_lengths=[2, 3],
    top_n=10,
    rank_by="sequence_prevalence",
)

motif_table = g.format_sequence_motifs(
    motif_filter,
    prevalence="percent",
    digits=1,
)
```

**Report:** motif length range, overlap rule, prevalence denominator, filtering
thresholds, and ranking rule.

## Recipe 4 — Distances, clustering, and representatives

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

validation_table = g.validate_sequence_clusters(clusters)
representatives = g.extract_representative_sequences(clusters)

print(g.summarise_sequence_distance(distance)["overall"])
print(clusters.assignments)
print(validation_table["overall"])
print(representatives)
```

!!! note
    Clusters are conditional on the declared distance geometry and clustering
    specification. Stability can strengthen confidence in reproducibility but
    does not establish that clusters are natural psychological types.

## Recipe 5 — Cluster stability

```python
stability = g.bootstrap_sequence_clusters(
    distance,
    k=2,
    method="hierarchical",
    linkage="average",
    n_boot=100,
    seed=17,
)

summary = g.summarise_sequence_cluster_stability(stability)
```

## Recipe 6 — Consensus and group descriptions

```python
consensus = g.create_consensus_sequence(
    prepared.data,
    group_cols="group",
)

agreement = g.summarise_consensus_agreement(consensus)

group_comparison = g.compare_sequence_groups(
    prepared.data,
    group_col="group",
)
```

## Recipe 7 — Transition network

```python
network = g.create_transition_network(
    prepared.data,
    normalise="from",
)

centrality = g.summarise_transition_centrality(network)
communities = g.detect_transition_communities(network)
```

## Recipe 8 — Higher-order next-state structure

```python
higher_order = g.fit_higher_order_transition_model(
    prepared.data,
    order=2,
)

prediction = g.predict_next_state(
    higher_order,
    history=["home", "search"],
)
```

## Recipe 9 — Compact categorical HMM

```python
hmm = g.fit_sequence_hmm(
    prepared.data,
    n_states=2,
    max_iter=100,
    seed=11,
)

hmm_summary = g.summarise_sequence_hmm(hmm)
decoded = g.decode_sequence_states(hmm)
```

Hidden-state labels are exchangeable statistical labels. Do not rename them as
cognitive or emotional states without independent evidence.

## Recipe 10 — Plot a compact analysis panel

```python
ax_index = g.plot_sequence_index(prepared.data)
ax_distribution = g.plot_sequence_state_distribution(prepared.data)
ax_distance = g.plot_sequence_distance_heatmap(distance)
ax_network = g.plot_transition_network(network)
```

See [Plot gallery](plots.md) for the complete visual inventory.

## Recipe 11 — Compare declared groups

Descriptive comparison:

```python
comparison = g.compare_sequence_groups(
    prepared.data,
    group_col="group",
)
```

Design-aware inference requires an explicit design declaration:

```python
design = g.declare_sequence_comparison_design(
    group_col="group",
    unit_col="participant_id",
    design="randomized",
)

inference = g.test_sequence_group_difference(
    prepared.data,
    design=design,
    metric="sequence_length",
    n_permutations=999,
    seed=42,
)
```

Use the dedicated [design-aware inference article](articles/sequence-inference-and-randomization.md)
before adapting this recipe to confirmatory work.

## Recipe 12 — Record capability and audit information

```python
capabilities = g.sequence_capabilities()
analysis_audit = g.audit_sequence_analysis(distance)
```

For publication reporting, continue to the [reporting guide](reporting.md).
