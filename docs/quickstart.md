# Quickstart

This page gives the shortest complete path from long-format categorical data to
validated sequence summaries, distances, clusters, networks, and plots.

!!! tip "Recommended data shape"
    Keep one row per observed state occurrence, one sequence identifier, one
    explicit order variable, one state column, and optional duration / metadata
    columns. Do not rely on row order alone.

## Install

=== "pip"

    ```bash
    pip install gp3sequencespy==0.1.1
    ```

=== "uv"

    ```bash
    uv add gp3sequencespy==0.1.1
    ```

=== "Development"

    ```bash
    uv sync --extra time
    ```

## 1. Create a small sequence table

```python
import pandas as pd
import gp3sequencespy as g

paths = {
    "s1": ["home", "search", "product", "cart", "checkout"],
    "s2": ["home", "search", "product", "cart", "home"],
    "s3": ["home", "category", "product", "cart", "checkout"],
    "s4": ["home", "category", "search", "product", "checkout"],
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

data = pd.DataFrame(rows)
```

## 2. Audit and validate before modelling

```python
audit = g.audit_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
)

validation = g.validate_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
)

print(validation.status)
```

Use `audit_sequence_data()` when you want the issue table without modifying the
data. Use `validate_sequence_data()` for a compact validation contract. Use
`prepare_sequence_data()` when explicit data-cleaning policies are required.

```python
prepared = g.prepare_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
    missing_state_policy="error",
    duplicate_position_policy="error",
    repeated_state_policy="preserve",
    zero_duration_policy="preserve",
    unknown_state_policy="preserve",
    unused_state_levels="preserve",
)
```

## 3. Describe states, transitions, and paths

```python
states = g.summarise_sequence_states(prepared.data)
transitions = g.summarise_sequence_transitions(prepared.data)
paths_table = g.format_sequence_paths(prepared.data)

print(states.overall)
print(transitions.overall.head())
print(paths_table.paths)
```

## 4. Mine recurring contiguous motifs

```python
occurrences = g.extract_sequence_ngrams(
    prepared.data,
    min_length=2,
    max_length=3,
    overlap="allow",
)

motifs = g.summarise_sequence_motifs(occurrences)
selected = g.filter_sequence_motifs(
    motifs,
    min_occurrences=2,
    top_n=10,
)
```

## 5. Compare whole sequences

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

cluster_validation = g.validate_sequence_clusters(clusters)
representatives = g.extract_representative_sequences(clusters)
```

Distance choice is part of the analysis specification. Use the
[method map](method-map.md) before treating a clustering solution as
substantively meaningful.

## 6. Summarise transition structure

```python
network = g.create_transition_network(
    prepared.data,
    normalise="from",
)

centrality = g.summarise_transition_centrality(network)
```

## 7. Plot the sequence structure

```python
ax = g.plot_sequence_index(prepared.data)
```

```python
ax = g.plot_sequence_state_distribution(prepared.data)
```

```python
ax = g.plot_sequence_distance_heatmap(distance)
```

```python
ax = g.plot_transition_network(network)
```

See the [plot gallery](plots.md) for all supported visual families.

## 8. Record the analysis contract

```python
analysis_audit = g.audit_sequence_analysis(distance)
print(analysis_audit.status)
print(analysis_audit.provenance)
```

`audit_sequence_analysis()` audits an analysis object and recovers its method,
identifiers, states, settings, seed, and structural validity where available.
It does not replace the study protocol, preregistration, or scientific
interpretation.

## Where to go next

<div class="gp3-card-grid gp3-card-grid--compact">
<div class="gp3-card"><h3>Need a method?</h3><p><a href="../method-map/">Choose by research question →</a></p></div>
<div class="gp3-card"><h3>Need recipes?</h3><p><a href="../examples/">Copy complete examples →</a></p></div>
<div class="gp3-card"><h3>Need figures?</h3><p><a href="../plots/">Browse plot families →</a></p></div>
<div class="gp3-card"><h3>Need full methods?</h3><p><a href="../articles/">Read the 15 articles →</a></p></div>
</div>
