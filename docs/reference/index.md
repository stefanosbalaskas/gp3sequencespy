# API reference

The API reference documents the **81 frozen public-function counterparts** of
`gp3sequences 0.3.0`. Signatures and docstrings are rendered from the installed
Python package at documentation-build time using `mkdocstrings`.

<div class="gp3-stats gp3-stats--small">
  <div><strong>81</strong><span>frozen functions</span></div>
  <div><strong>15</strong><span>plot helpers</span></div>
  <div><strong>0</strong><span>unexplained signature drift</span></div>
</div>

## Browse by task

| Task | Core functions |
|---|---|
| Audit / preparation | `audit_sequence_data`, `validate_sequence_data`, `prepare_sequence_data`, `prepare_sequence_panel` |
| Basic summaries | `summarise_sequence_states`, `summarise_sequence_transitions`, `format_sequence_paths` |
| Motifs / subsequences | `extract_sequence_ngrams`, `summarise_sequence_motifs`, `extract_sequence_subsequences` |
| Consensus / groups | `create_consensus_sequence`, `compare_sequence_groups`, `summarise_consensus_agreement` |
| Distance / clustering | `compute_sequence_distance`, `cluster_sequences`, `validate_sequence_clusters`, `bootstrap_sequence_clusters` |
| Transition graphs | `create_transition_network`, `summarise_transition_centrality`, `detect_transition_communities` |
| Higher-order transitions | `fit_higher_order_transition_model`, `predict_next_state` |
| HMMs | `fit_sequence_hmm`, `fit_sequence_hmm_mixture`, `fit_multichannel_sequence_hmm`, `fit_covariate_sequence_hmm` |
| Design-aware inference | `declare_sequence_comparison_design`, `test_sequence_group_difference` |
| Time-varying models | `fit_time_varying_sequence_model`, `predict_time_varying_sequence_model` |
| Audit / capabilities | `audit_sequence_analysis`, `compare_sequence_analysis_results`, `sequence_capabilities` |
| Plotting | `plot_sequence_index`, `plot_sequence_state_distribution`, `plot_transition_network`, and 12 more |

## Full reference

[Open the complete 81-function API →](api.md){ .md-button .md-button--primary }

## Before looking up a function

If you do not yet know which method is appropriate, use the
[method map](../method-map.md). If you know the method but want copyable code,
use [examples](../examples.md).

## Compatibility notes

A small set of functions are deliberate semantic translations of R ecosystem
objects. Python returns native structured objects or NetworkX graphs rather than
pretending to provide R S3/S4 object identity. See
[Parity & validation](../parity.md).
