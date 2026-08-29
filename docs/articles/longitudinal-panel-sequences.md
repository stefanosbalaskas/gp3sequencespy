# Longitudinal and Panel Sequence Workflows

```python
import pandas as pd
import gp3sequencespypy as g
```

## Scope

Panel sequences are repeated ordered-state records from the same independent
unit. The workflow preserves the panel identifier, occasion, sequence identity,
and preprocessing decisions. Distance between occasions is a structural change
measure; it is not evidence of learning, adaptation, or causality by itself.

## Synthetic data

```python
rows = []
for p in range(1, 5):
    for occasion in (1, 2):
        states = ["A", "B", "C", "D"] if occasion == 1 else ["A", "C", "C", "D"]
        sid = f"p{p}_t{occasion}"
        for order, state in enumerate(states, 1):
            rows.append({"participant_id": f"p{p}", "occasion": occasion, "sequence_id": sid, "sequence_order": order, "state": state})
base = pd.DataFrame(rows)
```

## Prepare and audit the panel

```python
panel = g.prepare_sequence_panel(
    base, panel_id_col="participant_id", occasion_col="occasion",
    sequence_id_col="sequence_id", order_col="sequence_order", state_col="state"
)
print(panel.audit.head())
```

A unique panel/occasion combination is required by default. This prevents two
sequences from being silently treated as the same repeated observation.

## Summarise occasions and states

```python
panel_summary = g.summarise_sequence_panel(panel)
print(panel_summary["occasions"])
print(panel_summary["states"].head())
```

## Quantify within-panel change

```python
changes = g.compare_sequence_panel_changes(panel, method="levenshtein", normalise="max_length")
changes.head()
```

Alternative distance methods use the same explicit arguments as
`compute_sequence_distance()`. The result compares consecutive occasions within
each panel only.

```python
g.plot_sequence_panel_changes(changes, metric="distance", type="individual")
g.plot_sequence_panel_changes(changes, metric="distance", type="summary")
```

## Reporting

Report the panel unit, occasion ordering, distance method, normalisation,
sequence counts at each occasion, and any missing occasions. Treat change as a
structural description unless a separate design supports stronger inference.
