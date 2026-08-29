# Frozen signature parity

This report audits the 81 frozen `gp3sequences 0.3.0` public formals against the current Python call signatures.

- Functions audited: **81 / 81**
- Structural matches: **37**
- Semantic R→Python translations: **29**
- Keyword-only Python plotting extensions: **0**
- Translation + plotting extension: **15**
- Unexplained drift: **0**

## Translation rules

- R `NULL`, logicals, integer `L` suffixes, `Inf`, and `NA` are translated to their Python-native equivalents.
- R `c(...)` defaults are distinguished between full vector defaults and `match.arg()`-style first-choice defaults based on the Python contract.
- R `...` maps to Python `*args`, `**kwargs`, or both when the R variadic contract permits named and unnamed objects.
- Plot functions may expose keyword-only `ax=` so callers can target a Matplotlib axis without changing the frozen positional argument contract.
- R and Matplotlib are different rendering engines; pixel-identical plots are not claimed.

## Result

**PASS — all 81 public signatures are structurally compatible or have an explicit semantic/Python-native translation.**

## Explicit Python plotting extensions

- `plot_consensus_sequence`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_multichannel_sequence_hmm`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_cluster_silhouette`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_distance_heatmap`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_entropy`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_group_comparison`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_group_inference`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_index`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_motif_positions`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_motifs`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_panel_changes`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_state_distribution`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_sequence_subsequences`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_time_varying_sequence_model`: keyword-only ax= Matplotlib target; Python plotting extension
- `plot_transition_network`: keyword-only ax= Matplotlib target; Python plotting extension
