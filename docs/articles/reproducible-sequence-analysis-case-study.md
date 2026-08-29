# Reproducible Sequence Analysis: A Synthetic Case Study

```python
import pandas as pd
import gp3sequencespypy as g
```

## Study objective

This synthetic example examines navigation-path structure under two assigned
interface conditions. It demonstrates an auditable workflow rather than a
claim that sequence structure reveals hidden attention, preference, cognition,
emotion, intention, or causality.

## Synthetic study data

The data contain 12 independent participant-level sequences of equal maximum
length. Interface condition is assigned as sequence-level metadata and all
state labels are directly observed navigation locations.

```python
paths = {'s01': ['home', 'search', 'product', 'cart', 'checkout', 'confirmation'], 's02': ['home', 'search', 'product', 'reviews', 'cart', 'checkout'], 's03': ['home', 'category', 'product', 'cart', 'checkout', 'confirmation'], 's04': ['home', 'search', 'product', 'cart', 'checkout', 'home'], 's05': ['home', 'category', 'search', 'product', 'cart', 'checkout'], 's06': ['home', 'search', 'category', 'product', 'checkout', 'confirmation'], 's07': ['home', 'category', 'product', 'reviews', 'cart', 'checkout'], 's08': ['home', 'search', 'product', 'reviews', 'checkout', 'confirmation'], 's09': ['home', 'category', 'product', 'cart', 'home', 'search'], 's10': ['home', 'search', 'product', 'cart', 'checkout', 'confirmation'], 's11': ['home', 'category', 'search', 'product', 'checkout', 'confirmation'], 's12': ['home', 'search', 'category', 'product', 'cart', 'checkout']}
groups = {'s01': 'interface_a', 's02': 'interface_a', 's03': 'interface_a', 's04': 'interface_a', 's05': 'interface_a', 's06': 'interface_a', 's07': 'interface_b', 's08': 'interface_b', 's09': 'interface_b', 's10': 'interface_b', 's11': 'interface_b', 's12': 'interface_b'}
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
    if groups is not None:
        row["group"] = groups[sid]
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## Prespecified preparation

The synthetic input is expected to be complete and uniquely ordered. Policies
therefore refuse missing states and duplicate positions while preserving
repeated states and positive durations.

```python
case_audit = g.audit_sequence_data(sequence_data, "sequence_id", "sequence_order", "state", metadata_cols=["group"])
case_prepared = g.prepare_sequence_data(sequence_data, "sequence_id", "sequence_order", "state", metadata_cols=["group"])
print(case_prepared.status)
```

## Structural summaries

```python
state_summary = g.summarise_sequence_states(case_prepared.data, "sequence_id", "sequence_order", "state", metadata_cols=["group"])
paths_table = g.format_sequence_paths(case_prepared.data, "sequence_id", "sequence_order", "state", metadata_cols=["group"])
print(state_summary.overall)
print(paths_table.paths.head())
```

## Recurring contiguous motifs

```python
case_motifs = g.extract_sequence_ngrams(case_prepared.data, "sequence_id", "sequence_order", "state", metadata_cols=["group"], min_length=2, max_length=3)
case_motif_summary = g.summarise_sequence_motifs(case_motifs)
case_motif_filter = g.filter_sequence_motifs(case_motif_summary, min_sequences=2, top_n=12)
```

## Consensus and condition contrasts

```python
case_consensus = g.create_consensus_sequence(case_prepared.data, group_cols="group")
case_group_comparison = g.compare_sequence_groups(case_prepared.data, group_col="group")
print(case_consensus.head())
print(case_group_comparison.state.head())
```

## Distance, clustering, and representatives

The clustering layer is declared in advance as normalised LCS distance,
two-cluster average-linkage hierarchical clustering, and standard structural
validation summaries.

```python
case_distance = g.compute_sequence_distance(case_prepared.data, method="lcs", normalise="max_length")
case_clusters = g.cluster_sequences(case_distance, k=2, linkage="average")
case_representatives = g.extract_representative_sequences(case_clusters)
print(g.validate_sequence_clusters(case_clusters)["overall"])
print(case_representatives)
```

## Transition network and recent-context model

```python
case_network = g.create_transition_network(case_prepared.data, normalise="from")
case_context = g.fit_higher_order_transition_model(case_prepared.data, order=2, smoothing=0.5)
print(case_network.head())
print(g.predict_next_state(case_context, ["home", "search"], top_n=3))
```

## Compact categorical HMM sensitivity description

The native HMM is included as a compact statistical summary, not as a source of
substantive state labels. A one-state and two-state model are compared
descriptively using the same observations and symbol coding.

```python
one_state = g.fit_sequence_hmm(case_prepared.data, n_states=1, max_iter=50, seed=7)
two_state = g.fit_sequence_hmm(case_prepared.data, n_states=2, max_iter=50, seed=7)
g.compare_sequence_hmms(one_state, two_state)
```

## Assemble report-ready evidence

```python
case_evidence = {
    "preparation_status": case_prepared.status,
    "state_summary": state_summary.overall,
    "motifs": case_motif_filter.table,
    "cluster_validation": g.validate_sequence_clusters(case_clusters)["overall"],
    "network": case_network,
}
case_evidence.keys()
```

## Interpretation boundary

The workflow documents recurring paths, aligned-position support, descriptive
condition contrasts, dissimilarity, clustering reproducibility, transition
structure, recent-context probabilities, and latent statistical summaries.
None of these outputs independently identifies attention, preference,
comprehension, emotion, cognition, intention, diagnosis, deception, or causal
mechanisms. Such interpretation requires an appropriate design, external
measurement, and independent validation.
