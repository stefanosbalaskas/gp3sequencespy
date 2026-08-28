import gp3sequencespy as g


EXPECTED_R_COUNTERPARTS = {
    "audit_sequence_data",
    "validate_sequence_data",
    "prepare_sequence_data",
    "encode_sequence_data",
    "summarise_sequence_states",
    "summarise_sequence_transitions",
    "format_sequence_paths",
    "extract_sequence_ngrams",
    "summarise_sequence_motifs",
    "filter_sequence_motifs",
    "format_sequence_motifs",
    "summarise_sequence_motif_positions",
    "format_sequence_motif_positions",
    "plot_sequence_motifs",
    "plot_sequence_motif_positions",
    "create_consensus_sequence",
    "summarise_consensus_agreement",
    "format_consensus_sequence",
    "compare_sequence_groups",
    "compute_sequence_distance",
    "summarise_sequence_distance",
    "cluster_sequences",
    "validate_sequence_clusters",
    "extract_representative_sequences",
    "bootstrap_sequence_clusters",
    "summarise_sequence_cluster_stability",
    "create_sequence_cluster_ensemble",
    "create_transition_network",
    "summarise_transition_centrality",
    "detect_transition_communities",
    "fit_higher_order_transition_model",
    "predict_next_state",
    "bootstrap_transition_network",
    "prepare_sequence_panel",
    "summarise_sequence_panel",
    "compare_sequence_panel_changes",
    "plot_sequence_panel_changes",
    "extract_sequence_subsequences",
    "summarise_sequence_subsequences",
    "filter_sequence_subsequences",
    "compare_sequence_subsequences",
    "plot_sequence_subsequences",
    "fit_sequence_hmm",
    "fit_sequence_hmm_mixture",
    "decode_sequence_states",
    "summarise_sequence_hmm",
    "compare_sequence_hmms",
    "declare_sequence_comparison_design",
    "test_sequence_group_difference",
    "bootstrap_sequence_group_difference",
    "summarise_sequence_group_inference",
    "plot_sequence_group_inference",
    "fit_multichannel_sequence_hmm",
    "decode_multichannel_sequence_states",
    "summarise_multichannel_sequence_hmm",
    "plot_multichannel_sequence_hmm",
    "fit_covariate_sequence_hmm",
    "predict_covariate_transition_probabilities",
    "decode_covariate_sequence_states",
    "summarise_covariate_sequence_hmm",
    "fit_time_varying_sequence_model",
    "predict_time_varying_sequence_model",
    "summarise_time_varying_sequence_model",
    "plot_time_varying_sequence_model",
}


def test_all_implemented_r_counterparts_are_public():
    exported = set(g.__all__)
    assert EXPECTED_R_COUNTERPARTS <= exported
    for name in EXPECTED_R_COUNTERPARTS:
        assert hasattr(g, name), name


def test_current_public_r_counterpart_count():
    assert len(EXPECTED_R_COUNTERPARTS) == 64
