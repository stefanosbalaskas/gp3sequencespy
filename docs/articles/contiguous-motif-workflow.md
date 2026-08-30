# Contiguous Motif Workflow

```python
import pandas as pd
import gp3sequencespy as g
```

## Scope

This article demonstrates the restricted contiguous-motif workflow in
`gp3sequencespy`. The workflow accepts ordinary long-format data frames and does
not require Gazepoint software, hardware, exports, or `gp3tools`.

The functions describe recurring state windows and their locations. They do not
infer attention, cognition, emotion, intention, psychological state, or causal
mechanisms.

## Synthetic ordered-state data

The example contains three sequences and one preserved grouping variable.

```python
paths = {'s1': ['A', 'B', 'C', 'A', 'B'], 's2': ['A', 'B', 'D', 'A', 'B'], 's3': ['A', 'B', 'C', 'B', 'C'], 's4': ['B', 'C', 'A', 'B', 'C'], 's5': ['A', 'C', 'A', 'B', 'C'], 's6': ['B', 'C', 'B', 'C', 'A']}
groups = {'s1': 'g1', 's2': 'g1', 's3': 'g1', 's4': 'g2', 's5': 'g2', 's6': 'g2'}
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
    if groups is not None:
        row["group"] = groups[sid]
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## Extract contiguous motifs

`extract_sequence_ngrams()` enumerates contiguous state windows only. Minimum
and maximum motif lengths and the overlapping-occurrence policy are explicit.

```python
extracted = g.extract_sequence_ngrams(
    sequence_data, "sequence_id", "sequence_order", "state",
    metadata_cols=["group"], min_length=2, max_length=3, overlap="allow"
)
extracted.occurrences.head()
```

## Summarise, filter, and format motifs

Sequence prevalence uses every validated sequence as its denominator. Filtering
is deterministic and retains explicit thresholds and tie handling.

```python
motif_summary = g.summarise_sequence_motifs(extracted)
motif_filter = g.filter_sequence_motifs(
    motif_summary, min_occurrences=2, min_sequences=2, min_prevalence=0.2,
    motif_lengths=[2, 3], top_n=10, rank_by="sequence_prevalence"
)
formatted = g.format_sequence_motifs(motif_filter, prevalence="percent", digits=1)
formatted.table
```

## Summarise motif positions

Positions may represent the start, centre, or end of each motif occurrence.
Absolute positions use one-based state indices. Relative positions range from 0
to 1 across each sequence.

```python
position_summary = g.summarise_sequence_motif_positions(
    extracted, position="centre", scale="relative", by="group"
)
position_summary.summary.head()
```

`format_sequence_motif_positions()` changes display precision and units without
modifying the underlying analytical object.

```python
position_table = g.format_sequence_motif_positions(position_summary, digits=1)
position_table["table"].head()
```

## Plot motif prevalence

`plot_sequence_motifs()` uses base R graphics. The returned data frame contains
the exact motifs and values used in the plot.

```python
ax = g.plot_sequence_motifs(motif_summary, metric="sequence_prevalence", top_n=10)
```

## Plot motif locations

The strip display shows individual occurrence positions with deterministic
stacking. No random jitter is used.

```python
ax = g.plot_sequence_motif_positions(
    extracted, position="centre", scale="relative", top_n=8, display="strip"
)
```

The distribution display provides a compact base-R summary for the same
structural positions.

```python
ax = g.plot_sequence_motif_positions(
    extracted, position="centre", scale="relative", top_n=8, display="boxplot"
)
```

## Interpretation boundary

The reported counts, prevalence values, and positions describe the supplied
ordered states under the declared preparation, motif-length, overlap, filtering,
and position rules. Any substantive interpretation belongs to the research
design and cannot be inferred automatically from motif structure alone.
