# Transition Networks and Higher-Order Models

```python
import pandas as pd
import gp3sequencespy as g
```

## Synthetic navigation sequences

```python
paths = {'s1': ['home', 'search', 'product', 'checkout'], 's2': ['home', 'search', 'product', 'home'], 's3': ['home', 'category', 'product', 'checkout'], 's4': ['home', 'category', 'search', 'checkout'], 's5': ['home', 'search', 'product', 'checkout'], 's6': ['home', 'category', 'product', 'home']}
groups = None
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## First-order transition network

```python
network = g.create_transition_network(sequence_data, normalise="from")
print(network.head())
print(g.summarise_transition_centrality(network).head())
print(g.detect_transition_communities(network).head())
```

Centrality values are graph-structural descriptors. They do not independently
measure attention, importance, intent, or influence.

## Higher-order transition model

```python
model = g.fit_higher_order_transition_model(sequence_data, order=2, smoothing=0.5, backoff=True)
g.predict_next_state(model, ["home", "search"], top_n=3)
```

## Whole-sequence bootstrap

```python
boot = g.bootstrap_transition_network(sequence_data, n_boot=100, level=0.95, seed=11)
boot.head()
```

Bootstrap samples are drawn at the sequence level, preserving within-sequence
transition dependence.
