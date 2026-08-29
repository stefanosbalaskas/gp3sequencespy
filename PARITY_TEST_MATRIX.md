# Frozen R test parity matrix

This ledger maps every frozen `gp3sequences 0.3.0` `test_that()` block to one dedicated Python translation test. It records behavioral-contract coverage, not proof of cross-language numerical identity.

## Freeze summary

- Frozen R test files: **22**
- Frozen R `test_that()` blocks: **130**
- Dedicated Python translated tests mapped below: **130 / 130**
- Total current Python tests (including bootstrap/public-API/compatibility, documentation, release, and hclust-oracle regression tests): **182**
- Current validated result after the frozen-signature/default repair: **182 passed**.
- Executable R oracle: **validated under R 4.6.1**; six deterministic core contracts and the extended hierarchical/PAM clustering oracle pass.

Status meanings: `exact_semantic_translation` means the Python test directly exercises the same public behavioral invariant; `backend_translation` records a deliberate Python ecosystem object translation; `internal_semantic_translation` exercises the invariant through Python internals/public behavior rather than reproducing an R-only private helper; `*_oracle_pending` means the behavioral contract is covered but exact R↔Python numerical equivalence still requires the executable R oracle.

## File-level coverage

| Frozen R test file | Blocks | Mapped |
|---|---:|---:|
| `test-adversarial-inputs.R` | 2 | 2 |
| `test-analysis-audit.R` | 3 | 3 |
| `test-capabilities.R` | 3 | 3 |
| `test-contract-invariants.R` | 3 | 3 |
| `test-metamorphic-invariants.R` | 3 | 3 |
| `test-package.R` | 1 | 1 |
| `test-sequence-adapters.R` | 6 | 6 |
| `test-sequence-consensus-groups.R` | 13 | 13 |
| `test-sequence-covariate-hmm.R` | 1 | 1 |
| `test-sequence-data.R` | 10 | 10 |
| `test-sequence-distances-clustering.R` | 17 | 17 |
| `test-sequence-encoding-summaries.R` | 11 | 11 |
| `test-sequence-inference.R` | 1 | 1 |
| `test-sequence-latent-models.R` | 12 | 12 |
| `test-sequence-motif-visualisation.R` | 12 | 12 |
| `test-sequence-motifs.R` | 12 | 12 |
| `test-sequence-multichannel-hmm.R` | 1 | 1 |
| `test-sequence-networks.R` | 10 | 10 |
| `test-sequence-panel.R` | 3 | 3 |
| `test-sequence-subsequences.R` | 4 | 4 |
| `test-sequence-time-models.R` | 1 | 1 |
| `test-sequence-visualisations-extended.R` | 1 | 1 |
| **Total** | **130** | **130** |

## Block-level mapping

| # | Frozen R block | Python translation | Status |
|---:|---|---|---|
| 1 | `test-adversarial-inputs.R #1: torture corpus exposes expected validation failures` | `tests/test_r_deterministic_contracts.py::test_r_adversarial_failures_are_explicit` | `exact_semantic_translation` |
| 2 | `test-adversarial-inputs.R #2: torture corpus exposes review rather than silent destruction` | `tests/test_r_deterministic_contracts.py::test_r_adversarial_review_cases_not_silently_destroyed` | `exact_semantic_translation` |
| 3 | `test-analysis-audit.R #1: analysis audit recognises a native distance object` | `tests/test_r_remaining_contracts.py::test_r_analysis_audit_native_distance` | `exact_semantic_translation` |
| 4 | `test-analysis-audit.R #2: analysis audit catches malformed distances` | `tests/test_r_block_completion.py::test_r_analysis_audit_catches_malformed_distances` | `exact_semantic_translation` |
| 5 | `test-analysis-audit.R #3: analysis-result comparison separates structure from values` | `tests/test_r_remaining_contracts.py::test_r_analysis_result_comparison_structure_vs_values` | `exact_semantic_translation` |
| 6 | `test-capabilities.R #1: sequence_capabilities is deterministic and dependency-safe` | `tests/test_r_block_completion.py::test_r_capabilities_deterministic_dependency_safe_block` | `exact_semantic_translation` |
| 7 | `test-capabilities.R #2: sequence_capabilities can report native capabilities only` | `tests/test_r_remaining_contracts.py::test_r_capabilities_roles_and_native_filter` | `exact_semantic_translation` |
| 8 | `test-capabilities.R #3: sequence_capabilities does not load optional backend namespaces` | `tests/test_r_block_completion.py::test_r_capabilities_do_not_import_optional_backends_block` | `exact_semantic_translation` |
| 9 | `test-contract-invariants.R #1: distance contract enforces core mathematical invariants` | `tests/test_r_deterministic_contracts.py::test_r_distance_core_mathematical_invariants` | `exact_semantic_translation` |
| 10 | `test-contract-invariants.R #2: probability simplex and matrix validators work` | `tests/test_r_block_completion.py::test_r_probability_simplex_and_matrix_validator_semantics` | `internal_semantic_translation` |
| 11 | `test-contract-invariants.R #3: partition labels canonicalise without changing membership` | `tests/test_r_block_completion.py::test_r_partition_label_canonicalisation_membership_semantics` | `internal_semantic_translation` |
| 12 | `test-metamorphic-invariants.R #1: distance is invariant to input row order with explicit order` | `tests/test_r_deterministic_contracts.py::test_r_metamorphic_distance_invariant_to_row_order` | `exact_semantic_translation` |
| 13 | `test-metamorphic-invariants.R #2: irrelevant metadata does not change sequence distance` | `tests/test_r_deterministic_contracts.py::test_r_metamorphic_irrelevant_metadata_no_distance_change` | `exact_semantic_translation` |
| 14 | `test-metamorphic-invariants.R #3: state relabelling preserves Levenshtein geometry` | `tests/test_r_deterministic_contracts.py::test_r_metamorphic_state_relabelling_preserves_levenshtein_geometry` | `exact_semantic_translation` |
| 15 | `test-package.R #1: package namespace is available` | `tests/test_r_deterministic_contracts.py::test_r_package_namespace_available` | `exact_semantic_translation` |
| 16 | `test-sequence-adapters.R #1: GrpString adapter creates deterministic strings and key` | `tests/test_r_remaining_contracts.py::test_r_adapters_deterministic_semantic_translations` | `exact_semantic_translation` |
| 17 | `test-sequence-adapters.R #2: gp3tools compatibility helper maps common columns` | `tests/test_r_block_completion.py::test_r_gp3tools_common_column_mapping_block` | `exact_semantic_translation` |
| 18 | `test-sequence-adapters.R #3: TraMineR and seqHMM adapters are guarded` | `tests/test_r_block_completion.py::test_r_traminer_and_seqhmm_semantic_adapter_block` | `backend_translation` |
| 19 | `test-sequence-adapters.R #4: arules adapter is guarded or returns sequential metadata` | `tests/test_r_block_completion.py::test_r_arules_sequential_metadata_block` | `backend_translation` |
| 20 | `test-sequence-adapters.R #5: igraph adapter refuses unresolved grouped networks` | `tests/test_r_block_completion.py::test_r_igraph_grouped_network_guard_block` | `backend_translation` |
| 21 | `test-sequence-adapters.R #6: gp3tools compatibility helper refuses ambiguous inferred mappings` | `tests/test_r_block_completion.py::test_r_gp3tools_ambiguous_mapping_guard_block` | `exact_semantic_translation` |
| 22 | `test-sequence-consensus-groups.R #1: consensus creation is deterministic and reports support` | `tests/test_r_advanced_deterministic_contracts.py::test_r_consensus_creation_deterministic_support` | `exact_semantic_translation` |
| 23 | `test-sequence-consensus-groups.R #2: consensus tie policies and missing-state policies are explicit` | `tests/test_r_advanced_deterministic_contracts.py::test_r_consensus_tie_and_missing_state_policies` | `exact_semantic_translation` |
| 24 | `test-sequence-consensus-groups.R #3: consensus summaries, formatting and plotting work` | `tests/test_r_advanced_deterministic_contracts.py::test_r_consensus_summaries_formatting_and_plotting` | `exact_semantic_translation` |
| 25 | `test-sequence-consensus-groups.R #4: descriptive group comparisons return expected components` | `tests/test_r_advanced_deterministic_contracts.py::test_r_group_comparison_expected_components` | `exact_semantic_translation` |
| 26 | `test-sequence-consensus-groups.R #5: group comparison plotting returns plotted data` | `tests/test_r_advanced_deterministic_contracts.py::test_r_group_comparison_plotting_data` | `exact_semantic_translation` |
| 27 | `test-sequence-consensus-groups.R #6: grouped consensus requires explicit plot selection` | `tests/test_r_advanced_deterministic_contracts.py::test_r_grouped_consensus_requires_selection` | `exact_semantic_translation` |
| 28 | `test-sequence-consensus-groups.R #7: group comparison rejects incomplete grouping metadata` | `tests/test_r_advanced_deterministic_contracts.py::test_r_group_comparison_rejects_incomplete_metadata` | `exact_semantic_translation` |
| 29 | `test-sequence-consensus-groups.R #8: advanced metadata mappings cannot duplicate core sequence columns` | `tests/test_r_advanced_deterministic_contracts.py::test_r_advanced_metadata_cannot_duplicate_core_columns` | `exact_semantic_translation` |
| 30 | `test-sequence-consensus-groups.R #9: zero-weight rows do not inflate consensus support` | `tests/test_r_advanced_deterministic_contracts.py::test_r_zero_weight_does_not_inflate_support` | `exact_semantic_translation` |
| 31 | `test-sequence-consensus-groups.R #10: group comparison transition labels require an unambiguous separator` | `tests/test_r_advanced_deterministic_contracts.py::test_r_group_transition_separator_guard` | `exact_semantic_translation` |
| 32 | `test-sequence-consensus-groups.R #11: reference-group contrasts use the reference as denominator` | `tests/test_r_advanced_deterministic_contracts.py::test_r_reference_group_is_denominator` | `exact_semantic_translation` |
| 33 | `test-sequence-consensus-groups.R #12: state plotting represents an unresolved consensus tie explicitly` | `tests/test_r_advanced_deterministic_contracts.py::test_r_state_plot_preserves_unresolved_tie` | `exact_semantic_translation` |
| 34 | `test-sequence-consensus-groups.R #13: empty transition comparisons fail clearly when plotted` | `tests/test_r_advanced_deterministic_contracts.py::test_r_empty_transition_comparison_plot_fails_clearly` | `exact_semantic_translation` |
| 35 | `test-sequence-covariate-hmm.R #1: covariate HMM fits with explicit design matrices` | `tests/test_r_remaining_contracts.py::test_r_covariate_hmm_explicit_design_contract` | `semantic_contract; numerical_oracle_pending` |
| 36 | `test-sequence-data.R #1: audit output has a stable empty contract` | `tests/test_r_deterministic_contracts.py::test_r_data_audit_empty_contract` | `exact_semantic_translation` |
| 37 | `test-sequence-data.R #2: validation reports normal and empty inputs` | `tests/test_r_deterministic_contracts.py::test_r_data_validation_normal_and_empty` | `exact_semantic_translation` |
| 38 | `test-sequence-data.R #3: missing columns and states are explicit errors` | `tests/test_r_deterministic_contracts.py::test_r_data_missing_columns_and_states` | `exact_semantic_translation` |
| 39 | `test-sequence-data.R #4: ordering, gaps, and duplicated positions are audited` | `tests/test_r_deterministic_contracts.py::test_r_data_order_gaps_and_duplicate_positions_audited` | `exact_semantic_translation` |
| 40 | `test-sequence-data.R #5: duration and metadata errors are detected` | `tests/test_r_deterministic_contracts.py::test_r_data_duration_and_metadata_errors` | `exact_semantic_translation` |
| 41 | `test-sequence-data.R #6: preparation sorts deterministically and preserves identifiers` | `tests/test_r_deterministic_contracts.py::test_r_data_preparation_sort_and_identifiers` | `exact_semantic_translation` |
| 42 | `test-sequence-data.R #7: explicit policies drop missing and unknown states` | `tests/test_r_deterministic_contracts.py::test_r_data_explicit_drop_policies` | `exact_semantic_translation` |
| 43 | `test-sequence-data.R #8: duplicate and repeated-state policies are deterministic` | `tests/test_r_deterministic_contracts.py::test_r_data_duplicate_and_repeat_policies` | `exact_semantic_translation` |
| 44 | `test-sequence-data.R #9: unresolved policy errors suppress prepared data` | `tests/test_r_deterministic_contracts.py::test_r_data_unresolved_errors_suppress_output` | `exact_semantic_translation` |
| 45 | `test-sequence-data.R #10: single-state and unused levels remain reviewable` | `tests/test_r_deterministic_contracts.py::test_r_data_single_state_and_unused_levels_reviewable` | `exact_semantic_translation` |
| 46 | `test-sequence-distances-clustering.R #1: all core sequence distances are symmetric and deterministic` | `tests/test_r_advanced_deterministic_contracts.py::test_r_all_core_distances_symmetric_deterministic` | `exact_semantic_translation` |
| 47 | `test-sequence-distances-clustering.R #2: distance normalisation and substitution matrices are explicit` | `tests/test_r_advanced_deterministic_contracts.py::test_r_distance_normalisation_and_substitution_matrix_guard` | `exact_semantic_translation` |
| 48 | `test-sequence-distances-clustering.R #3: distance summaries include overall and per-sequence results` | `tests/test_r_advanced_deterministic_contracts.py::test_r_distance_summary_overall_and_per_sequence` | `exact_semantic_translation` |
| 49 | `test-sequence-distances-clustering.R #4: hierarchical clustering and validation are auditable` | `tests/test_r_advanced_deterministic_contracts.py::test_r_hierarchical_cluster_validation_and_representatives` | `semantic_contract; R_clustering_oracle_validated` |
| 50 | `test-sequence-distances-clustering.R #5: PAM is guarded by the optional cluster package` | `tests/test_r_advanced_deterministic_contracts.py::test_r_pam_native_backend_available` | `semantic_contract; R_clustering_oracle_validated` |
| 51 | `test-sequence-distances-clustering.R #6: bootstrap stability is reproducible` | `tests/test_r_advanced_deterministic_contracts.py::test_r_bootstrap_cluster_stability_reproducible` | `semantic_contract; R_clustering_oracle_validated` |
| 52 | `test-sequence-distances-clustering.R #7: cluster ensembles use transparent co-association` | `tests/test_r_advanced_deterministic_contracts.py::test_r_cluster_ensemble_coassociation_contract` | `semantic_contract; R_clustering_oracle_validated` |
| 53 | `test-sequence-distances-clustering.R #8: distance and substitution matrices enforce metric structure` | `tests/test_r_advanced_deterministic_contracts.py::test_r_distance_and_substitution_metric_guards` | `exact_semantic_translation` |
| 54 | `test-sequence-distances-clustering.R #9: CLARA is guarded and preserves sequence identifiers` | `tests/test_r_advanced_deterministic_contracts.py::test_r_clara_preserves_sequence_identifiers` | `semantic_contract; R_clustering_oracle_validated` |
| 55 | `test-sequence-distances-clustering.R #10: stochastic helpers restore the caller random-number state` | `tests/test_r_advanced_deterministic_contracts.py::test_r_stochastic_cluster_helpers_do_not_mutate_global_numpy_rng` | `exact_semantic_translation` |
| 56 | `test-sequence-distances-clustering.R #11: character cluster assignments are supported` | `tests/test_r_advanced_deterministic_contracts.py::test_r_character_cluster_assignments_supported` | `exact_semantic_translation` |
| 57 | `test-sequence-distances-clustering.R #12: unused factor levels do not become observed distance states` | `tests/test_r_advanced_deterministic_contracts.py::test_r_unused_categorical_levels_not_observed_distance_states` | `exact_semantic_translation` |
| 58 | `test-sequence-distances-clustering.R #13: ensemble linkage and stability summaries are validated` | `tests/test_r_advanced_deterministic_contracts.py::test_r_ensemble_linkage_and_stability_validation` | `semantic_contract; R_clustering_oracle_validated` |
| 59 | `test-sequence-distances-clustering.R #14: optional CLARA clustering restores the caller RNG and is repeatable` | `tests/test_r_advanced_deterministic_contracts.py::test_r_clara_repeatable_and_global_rng_safe` | `semantic_contract; R_clustering_oracle_validated` |
| 60 | `test-sequence-distances-clustering.R #15: integer controls reject values outside the R integer range` | `tests/test_r_block_completion.py::test_r_integer_controls_reject_values_outside_r_integer_range_block` | `exact_semantic_translation` |
| 61 | `test-sequence-distances-clustering.R #16: seed validation and bootstrap offsets are safe` | `tests/test_r_advanced_deterministic_contracts.py::test_r_integer_seed_controls_reject_invalid_values_and_boundary_safe` | `exact_semantic_translation` |
| 62 | `test-sequence-distances-clustering.R #17: additional clustering arguments must be named` | `tests/test_r_advanced_deterministic_contracts.py::test_r_additional_clustering_positional_arguments_rejected_by_python_signature` | `exact_semantic_translation` |
| 63 | `test-sequence-encoding-summaries.R #1: state encoding is deterministic across row order` | `tests/test_r_deterministic_contracts.py::test_r_encoding_deterministic_across_row_order` | `exact_semantic_translation` |
| 64 | `test-sequence-encoding-summaries.R #2: custom encoding levels and labels are respected` | `tests/test_r_deterministic_contracts.py::test_r_encoding_custom_levels_and_labels` | `exact_semantic_translation` |
| 65 | `test-sequence-encoding-summaries.R #3: factor levels define the default encoding order` | `tests/test_r_deterministic_contracts.py::test_r_encoding_categorical_levels_define_order` | `exact_semantic_translation` |
| 66 | `test-sequence-encoding-summaries.R #4: state summaries return exact counts and proportions` | `tests/test_r_deterministic_contracts.py::test_r_state_summary_exact_counts_and_proportions` | `exact_semantic_translation` |
| 67 | `test-sequence-encoding-summaries.R #5: state summaries are deterministic across input order` | `tests/test_r_deterministic_contracts.py::test_r_state_summary_deterministic_across_input_order` | `exact_semantic_translation` |
| 68 | `test-sequence-encoding-summaries.R #6: transition summaries return exact adjacent counts` | `tests/test_r_deterministic_contracts.py::test_r_transition_summary_exact_adjacent_counts` | `exact_semantic_translation` |
| 69 | `test-sequence-encoding-summaries.R #7: self-transition filtering is explicit` | `tests/test_r_deterministic_contracts.py::test_r_transition_self_filtering_explicit` | `exact_semantic_translation` |
| 70 | `test-sequence-encoding-summaries.R #8: single-state sequences produce stable empty transitions` | `tests/test_r_deterministic_contracts.py::test_r_transition_single_state_empty_schema` | `exact_semantic_translation` |
| 71 | `test-sequence-encoding-summaries.R #9: formatted paths are ordered and retain metadata` | `tests/test_r_deterministic_contracts.py::test_r_paths_ordered_and_metadata_retained` | `exact_semantic_translation` |
| 72 | `test-sequence-encoding-summaries.R #10: path formatting can collapse consecutive repeats` | `tests/test_r_deterministic_contracts.py::test_r_paths_collapse_consecutive_repeats` | `exact_semantic_translation` |
| 73 | `test-sequence-encoding-summaries.R #11: summary functions reject unresolved validation errors` | `tests/test_r_deterministic_contracts.py::test_r_summary_functions_reject_unresolved_validation_errors` | `exact_semantic_translation` |
| 74 | `test-sequence-inference.R #1: sequence inference records the design and resamples independent units` | `tests/test_r_remaining_contracts.py::test_r_sequence_inference_design_resampling_contract` | `exact_semantic_translation` |
| 75 | `test-sequence-latent-models.R #1: single HMM fitting is deterministic and normalised` | `tests/test_r_remaining_contracts.py::test_r_single_hmm_deterministic_normalised` | `semantic_contract; numerical_oracle_pending` |
| 76 | `test-sequence-latent-models.R #2: HMM decoding returns one latent state per observation` | `tests/test_r_remaining_contracts.py::test_r_hmm_decoding_one_state_per_observation` | `semantic_contract; numerical_oracle_pending` |
| 77 | `test-sequence-latent-models.R #3: HMM summaries and model comparisons are structured` | `tests/test_r_remaining_contracts.py::test_r_hmm_summary_and_comparison_structured` | `semantic_contract; numerical_oracle_pending` |
| 78 | `test-sequence-latent-models.R #4: mixture HMM responsibilities are normalised and deterministic` | `tests/test_r_remaining_contracts.py::test_r_hmm_mixture_responsibilities_normalised_deterministic` | `semantic_contract; numerical_oracle_pending` |
| 79 | `test-sequence-latent-models.R #5: HMM inputs reject unsupported symbols and invalid probabilities` | `tests/test_r_remaining_contracts.py::test_r_hmm_invalid_symbols_and_probabilities_rejected` | `semantic_contract; numerical_oracle_pending` |
| 80 | `test-sequence-latent-models.R #6: HMM initialisation rejects non-finite probabilities` | `tests/test_r_block_completion.py::test_r_hmm_initialisation_rejects_nonfinite_probabilities_block` | `semantic_contract; numerical_oracle_pending` |
| 81 | `test-sequence-latent-models.R #7: HMM fitting restores the caller random-number state` | `tests/test_r_remaining_contracts.py::test_r_hmm_global_rng_unchanged` | `semantic_contract; numerical_oracle_pending` |
| 82 | `test-sequence-latent-models.R #8: HMM fit criteria require a common observation basis` | `tests/test_r_remaining_contracts.py::test_r_hmm_comparison_common_observation_basis_required` | `semantic_contract; numerical_oracle_pending` |
| 83 | `test-sequence-latent-models.R #9: HMM symbol levels are unique and exclude unused factor levels` | `tests/test_r_remaining_contracts.py::test_r_hmm_symbol_levels_unique_unused_excluded` | `semantic_contract; numerical_oracle_pending` |
| 84 | `test-sequence-latent-models.R #10: HMM comparison requires identical sequence identifiers` | `tests/test_r_remaining_contracts.py::test_r_hmm_comparison_sequence_ids_identical` | `semantic_contract; numerical_oracle_pending` |
| 85 | `test-sequence-latent-models.R #11: mixture seed offsets remain valid at the integer boundary` | `tests/test_r_remaining_contracts.py::test_r_hmm_seed_boundary_and_state_count_validation` | `semantic_contract; numerical_oracle_pending` |
| 86 | `test-sequence-latent-models.R #12: mixture hidden-state counts reject values outside R integer range` | `tests/test_r_block_completion.py::test_r_hmm_hidden_state_counts_reject_out_of_range_block` | `semantic_contract; numerical_oracle_pending` |
| 87 | `test-sequence-motif-visualisation.R #1: absolute motif positions are summarised exactly` | `tests/test_r_remaining_contracts.py::test_r_motif_positions_absolute_exact` | `exact_semantic_translation` |
| 88 | `test-sequence-motif-visualisation.R #2: relative positions are bounded and use the requested basis` | `tests/test_r_remaining_contracts.py::test_r_motif_positions_relative_bounded_basis` | `exact_semantic_translation` |
| 89 | `test-sequence-motif-visualisation.R #3: metadata grouping produces separate deterministic summaries` | `tests/test_r_remaining_contracts.py::test_r_motif_positions_grouped_deterministic` | `exact_semantic_translation` |
| 90 | `test-sequence-motif-visualisation.R #4: position summaries retain stable empty schemas` | `tests/test_r_remaining_contracts.py::test_r_motif_positions_empty_schema` | `exact_semantic_translation` |
| 91 | `test-sequence-motif-visualisation.R #5: position formatting changes display only` | `tests/test_r_remaining_contracts.py::test_r_motif_position_formatting_display_only` | `exact_semantic_translation` |
| 92 | `test-sequence-motif-visualisation.R #6: absolute positions remain indices during formatting` | `tests/test_r_remaining_contracts.py::test_r_motif_absolute_formatting_stays_index_units` | `exact_semantic_translation` |
| 93 | `test-sequence-motif-visualisation.R #7: motif plot data applies deterministic top-n ties` | `tests/test_r_block_completion.py::test_r_motif_plot_top_n_ties_are_deterministic_block` | `exact_semantic_translation` |
| 94 | `test-sequence-motif-visualisation.R #8: motif bar plots return the exact plotted table` | `tests/test_r_remaining_contracts.py::test_r_motif_bar_and_empty_plot_contracts` | `exact_semantic_translation` |
| 95 | `test-sequence-motif-visualisation.R #9: motif plots handle empty filtered inputs` | `tests/test_r_block_completion.py::test_r_motif_empty_filtered_plot_block` | `exact_semantic_translation` |
| 96 | `test-sequence-motif-visualisation.R #10: strip position plots are deterministic and bounded` | `tests/test_r_remaining_contracts.py::test_r_motif_position_plots_filters_and_bounds` | `exact_semantic_translation` |
| 97 | `test-sequence-motif-visualisation.R #11: position plots accept motif identifiers labels and summaries` | `tests/test_r_block_completion.py::test_r_motif_position_plot_accepts_ids_labels_and_summary_block` | `exact_semantic_translation` |
| 98 | `test-sequence-motif-visualisation.R #12: invalid positional and plotting settings are rejected` | `tests/test_r_remaining_contracts.py::test_r_motif_visualisation_invalid_settings` | `exact_semantic_translation` |
| 99 | `test-sequence-motifs.R #1: contiguous n-grams are enumerated with stable positions` | `tests/test_r_deterministic_contracts.py::test_r_motifs_contiguous_stable_positions` | `exact_semantic_translation` |
| 100 | `test-sequence-motifs.R #2: overlap policy is explicit and deterministic` | `tests/test_r_deterministic_contracts.py::test_r_motifs_overlap_policy_deterministic` | `exact_semantic_translation` |
| 101 | `test-sequence-motifs.R #3: row order is corrected while review diagnostics are retained` | `tests/test_r_deterministic_contracts.py::test_r_motifs_row_order_corrected_with_review` | `exact_semantic_translation` |
| 102 | `test-sequence-motifs.R #4: motif identity remains stable when labels contain separators` | `tests/test_r_deterministic_contracts.py::test_r_motifs_separator_labels_keep_identity` | `exact_semantic_translation` |
| 103 | `test-sequence-motifs.R #5: motif summaries return exact counts and prevalence` | `tests/test_r_deterministic_contracts.py::test_r_motif_summary_exact_counts_prevalence` | `exact_semantic_translation` |
| 104 | `test-sequence-motifs.R #6: prevalence denominator includes sequences without eligible windows` | `tests/test_r_deterministic_contracts.py::test_r_motif_prevalence_denominator_includes_short_sequences` | `exact_semantic_translation` |
| 105 | `test-sequence-motifs.R #7: filters apply count prevalence and length thresholds` | `tests/test_r_deterministic_contracts.py::test_r_motif_filter_thresholds` | `exact_semantic_translation` |
| 106 | `test-sequence-motifs.R #8: top-n ties are included or resolved deterministically` | `tests/test_r_deterministic_contracts.py::test_r_motif_top_n_ties` | `exact_semantic_translation` |
| 107 | `test-sequence-motifs.R #9: formatted motif tables use explicit units and rank ties` | `tests/test_r_deterministic_contracts.py::test_r_motif_format_units_and_rank_ties` | `exact_semantic_translation` |
| 108 | `test-sequence-motifs.R #10: empty motif outputs retain stable schemas` | `tests/test_r_deterministic_contracts.py::test_r_motif_empty_outputs_stable_schemas` | `exact_semantic_translation` |
| 109 | `test-sequence-motifs.R #11: factor levels define deterministic motif codes` | `tests/test_r_deterministic_contracts.py::test_r_motif_categorical_levels_define_codes` | `exact_semantic_translation` |
| 110 | `test-sequence-motifs.R #12: invalid settings and unresolved input errors are rejected` | `tests/test_r_deterministic_contracts.py::test_r_motif_invalid_settings_rejected` | `exact_semantic_translation` |
| 111 | `test-sequence-multichannel-hmm.R #1: multichannel HMM fits, decodes, and summarises` | `tests/test_r_remaining_contracts.py::test_r_multichannel_hmm_fit_decode_summary_plot` | `semantic_contract; numerical_oracle_pending` |
| 112 | `test-sequence-networks.R #1: first-order transition networks contain auditable edge measures` | `tests/test_r_advanced_deterministic_contracts.py::test_r_first_order_network_edge_measures` | `exact_semantic_translation` |
| 113 | `test-sequence-networks.R #2: higher-order networks and models use explicit contexts` | `tests/test_r_advanced_deterministic_contracts.py::test_r_higher_order_network_and_model_contexts` | `exact_semantic_translation` |
| 114 | `test-sequence-networks.R #3: centrality and communities are deterministic` | `tests/test_r_advanced_deterministic_contracts.py::test_r_network_centrality_and_communities_deterministic` | `exact_semantic_translation` |
| 115 | `test-sequence-networks.R #4: network bootstrap is reproducible and bounded` | `tests/test_r_advanced_deterministic_contracts.py::test_r_network_bootstrap_reproducible_bounded` | `exact_semantic_translation` |
| 116 | `test-sequence-networks.R #5: igraph conversion is optional` | `tests/test_r_advanced_deterministic_contracts.py::test_r_networkx_adapter_contract` | `backend_translation` |
| 117 | `test-sequence-networks.R #6: graph summaries require one selected group` | `tests/test_r_advanced_deterministic_contracts.py::test_r_grouped_graph_summaries_require_selection` | `exact_semantic_translation` |
| 118 | `test-sequence-networks.R #7: unseen higher-order contexts return a stable probability schema` | `tests/test_r_advanced_deterministic_contracts.py::test_r_unseen_context_probability_schema` | `exact_semantic_translation` |
| 119 | `test-sequence-networks.R #8: network bootstrap restores the caller random-number state` | `tests/test_r_advanced_deterministic_contracts.py::test_r_network_bootstrap_global_rng_safe` | `exact_semantic_translation` |
| 120 | `test-sequence-networks.R #9: next-state history rejects blank states` | `tests/test_r_advanced_deterministic_contracts.py::test_r_next_state_blank_history_rejected` | `exact_semantic_translation` |
| 121 | `test-sequence-networks.R #10: network context labels require an unambiguous separator` | `tests/test_r_advanced_deterministic_contracts.py::test_r_network_context_separator_guard` | `exact_semantic_translation` |
| 122 | `test-sequence-panel.R #1: sequence panels are prepared and summarised` | `tests/test_r_remaining_contracts.py::test_r_panel_prepare_and_summary_contract` | `exact_semantic_translation` |
| 123 | `test-sequence-panel.R #2: panel changes are deterministic` | `tests/test_r_remaining_contracts.py::test_r_panel_changes_deterministic_and_plot` | `exact_semantic_translation` |
| 124 | `test-sequence-panel.R #3: duplicated panel occasions fail explicitly` | `tests/test_r_remaining_contracts.py::test_r_panel_duplicate_occasion_fails` | `exact_semantic_translation` |
| 125 | `test-sequence-subsequences.R #1: bounded non-contiguous subsequences are extracted` | `tests/test_r_remaining_contracts.py::test_r_subsequence_bounded_extraction` | `exact_semantic_translation` |
| 126 | `test-sequence-subsequences.R #2: subsequence summaries and filtering are stable` | `tests/test_r_remaining_contracts.py::test_r_subsequence_summary_filter_plot` | `exact_semantic_translation` |
| 127 | `test-sequence-subsequences.R #3: group comparisons adjust multiple tests` | `tests/test_r_remaining_contracts.py::test_r_subsequence_group_comparison_adjusts_multiple_tests` | `exact_semantic_translation` |
| 128 | `test-sequence-subsequences.R #4: search-space safety limit is enforced` | `tests/test_r_remaining_contracts.py::test_r_subsequence_search_space_limit` | `exact_semantic_translation` |
| 129 | `test-sequence-time-models.R #1: time-varying models are dependency guarded and auditable` | `tests/test_r_remaining_contracts.py::test_r_time_model_auditable_python_translation` | `functional_translation; mgcv_oracle_pending` |
| 130 | `test-sequence-visualisations-extended.R #1: extended visualisations accept core package objects` | `tests/test_r_remaining_contracts.py::test_r_extended_visualisations_accept_core_objects` | `exact_semantic_translation` |

## Numerical/object-identity limits

This matrix does **not** supersede `PARITY_EXCEPTIONS.md`. In particular, R S3/S4 adapter object identity, R-vs-NumPy RNG streams, selected clustering implementation details, and the `mgcv` time-model fit remain explicit parity exceptions until exercised against the frozen R 0.3.0 oracle.
