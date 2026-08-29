import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy._exceptions import ValidationError


def advanced_data():
    paths = {
        "s01": ["A", "B", "C", "D", "D"],
        "s02": ["A", "B", "C", "D", "C"],
        "s03": ["A", "B", "B", "C", "D"],
        "s04": ["A", "C", "C", "D", "D"],
        "s05": ["D", "C", "B", "A", "A"],
        "s06": ["D", "C", "B", "A", "B"],
        "s07": ["D", "C", "C", "B", "A"],
        "s08": ["D", "B", "B", "A", "A"],
    }
    rows = []
    for i, (sid, path) in enumerate(paths.items(), 1):
        group = "g1" if i <= 4 else "g2"
        for pos, state in enumerate(path, 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": pos,
                    "state": state,
                    "group": group,
                    "participant_id": f"p{i}",
                    "weight": 1.0,
                }
            )
    return pd.DataFrame(rows)


# ---- consensus/group comparisons ----------------------------------------


def test_r_consensus_creation_deterministic_support():
    data = advanced_data()
    first = g.create_consensus_sequence(data, group_cols="group", tie_method="first")
    second = g.create_consensus_sequence(data, group_cols="group", tie_method="first")
    assert {"consensus_state", "support_n", "agreement", "tie_n"}.issubset(first.columns)
    assert (
        len(first) == 10 and (first.support_n == 4).all() and first.agreement.between(0.5, 1).all()
    )
    pd.testing.assert_frame_equal(first, second)


def test_r_consensus_tie_and_missing_state_policies():
    data = pd.DataFrame(
        {"sequence_id": ["s1", "s2"], "sequence_order": [1, 1], "state": ["B", "A"]}
    )
    assert (
        g.create_consensus_sequence(data, tie_method="first", state_levels=["A", "B"])
        .iloc[0]
        .consensus_state
        == "A"
    )
    assert (
        g.create_consensus_sequence(data, tie_method="last", state_levels=["A", "B"])
        .iloc[0]
        .consensus_state
        == "B"
    )
    assert pd.isna(
        g.create_consensus_sequence(data, tie_method="missing", state_levels=["A", "B"])
        .iloc[0]
        .consensus_state
    )
    assert (
        g.create_consensus_sequence(data, tie_method="all", state_levels=["A", "B"])
        .iloc[0]
        .consensus_state
        == "A | B"
    )
    data.loc[1, "state"] = None
    with pytest.raises(ValidationError):
        g.create_consensus_sequence(data, missing_state_policy="error")
    assert g.create_consensus_sequence(data, missing_state_policy="exclude").iloc[0].support_n == 1


def test_r_consensus_summaries_formatting_and_plotting():
    consensus = g.create_consensus_sequence(advanced_data(), group_cols="group")
    assert len(g.summarise_consensus_agreement(consensus, by="overall")) == 1
    assert len(g.summarise_consensus_agreement(consensus, by="group")) == 2
    assert len(g.format_consensus_sequence(consensus, include_agreement=True)) == 2
    ax = g.plot_consensus_sequence(consensus, group="g1")
    assert len(ax.gp3_data) == 5
    plt.close(ax.figure)


def test_r_group_comparison_expected_components():
    comparison = g.compare_sequence_groups(advanced_data(), "group")
    assert comparison.groups.n_sequences.tolist() == [4, 4]
    assert {"state", "event_share", "sequence_prevalence"}.issubset(
        comparison.state_summary.columns
    )
    assert {"transition", "occurrence_share"}.issubset(comparison.transition_summary.columns)
    assert len(comparison.length_summary) == 2
    assert not any(("p_value" in c or "statistic" in c) for c in comparison.state_contrasts.columns)


def test_r_group_comparison_plotting_data():
    comparison = g.compare_sequence_groups(advanced_data(), "group")
    ax = g.plot_sequence_group_comparison(comparison, "state", top_n=4)
    assert len(ax.gp3_data) > 0
    plt.close(ax.figure)
    ax = g.plot_sequence_group_comparison(comparison, "length")
    assert len(ax.gp3_data) == 2
    plt.close(ax.figure)


def test_r_grouped_consensus_requires_selection():
    consensus = g.create_consensus_sequence(advanced_data(), group_cols="group")
    with pytest.raises(ValidationError, match="Select one consensus group"):
        g.plot_consensus_sequence(consensus)
    ungrouped = g.create_consensus_sequence(advanced_data())
    with pytest.raises(ValidationError, match="requires a consensus"):
        g.summarise_consensus_agreement(ungrouped, by="group")


def test_r_group_comparison_rejects_incomplete_metadata():
    data = advanced_data()
    data.loc[data.sequence_id == "s01", "group"] = None
    with pytest.raises(ValidationError, match="non-missing and non-blank"):
        g.compare_sequence_groups(data, "group")


def test_r_advanced_metadata_cannot_duplicate_core_columns():
    with pytest.raises(ValidationError, match="must not repeat core sequence columns"):
        g.create_consensus_sequence(advanced_data(), group_cols="sequence_id")


def test_r_zero_weight_does_not_inflate_support():
    data = pd.DataFrame(
        {
            "sequence_id": ["s1", "s2"],
            "sequence_order": [1, 1],
            "state": ["A", "B"],
            "weight": [1, 0],
        }
    )
    row = g.create_consensus_sequence(data, weight_col="weight").iloc[0]
    assert row.consensus_state == "A" and row.support_n == 1 and row.support_weight == 1


def test_r_group_transition_separator_guard():
    data = advanced_data()
    data.loc[data.state == "A", "state"] = "A -> embedded"
    with pytest.raises(ValidationError, match="must not occur inside"):
        g.compare_sequence_groups(data, "group")


def test_r_reference_group_is_denominator():
    comparison = g.compare_sequence_groups(advanced_data(), "group", reference="g1")
    assert (comparison.state_contrasts.group_2 == "g1").all()
    assert (comparison.transition_contrasts.group_2 == "g1").all()
    assert (comparison.length_contrasts.group_2 == "g1").all()


def test_r_state_plot_preserves_unresolved_tie():
    data = pd.DataFrame(
        {"sequence_id": ["s1", "s2"], "sequence_order": [1, 1], "state": ["A", "B"]}
    )
    consensus = g.create_consensus_sequence(data, tie_method="missing")
    ax = g.plot_consensus_sequence(consensus, type="states")
    assert pd.isna(ax.gp3_data.consensus_state.iloc[0])
    plt.close(ax.figure)


def test_r_empty_transition_comparison_plot_fails_clearly():
    data = pd.DataFrame(
        {
            "sequence_id": ["s1", "s2"],
            "sequence_order": [1, 1],
            "state": ["A", "B"],
            "group": ["g1", "g2"],
        }
    )
    comparison = g.compare_sequence_groups(data, "group")
    with pytest.raises(ValidationError, match="No comparison rows"):
        g.plot_sequence_group_comparison(comparison, component="transition")


# ---- distances/clustering -----------------------------------------------


def test_r_all_core_distances_symmetric_deterministic():
    data = advanced_data()
    for method in ["levenshtein", "lcs", "optimal_matching", "transition"]:
        first = g.compute_sequence_distance(data, method=method)
        second = g.compute_sequence_distance(data, method=method)
        assert np.allclose(first.matrix, first.matrix.T, atol=1e-12)
        assert np.allclose(np.diag(first.matrix), 0)
        assert (first.matrix >= 0).all()
        assert np.array_equal(first.matrix, second.matrix)
        assert first.labels == second.labels


def test_r_distance_normalisation_and_substitution_matrix_guard():
    data = advanced_data()
    states = sorted(data.state.unique())
    costs = pd.DataFrame(2.0, index=states, columns=states)
    for state in states:
        costs.loc[state, state] = 0.0
    raw = g.compute_sequence_distance(
        data, method="optimal_matching", substitution_matrix=costs, normalise="none"
    )
    norm = g.compute_sequence_distance(
        data, method="optimal_matching", substitution_matrix=costs, normalise="max_length"
    )
    assert (norm.matrix <= raw.matrix + 1e-12).all()
    with pytest.raises(ValidationError):
        g.compute_sequence_distance(
            data, method="optimal_matching", substitution_matrix=np.ones((2, 3))
        )


def test_r_distance_summary_overall_and_per_sequence():
    summary = g.summarise_sequence_distance(g.compute_sequence_distance(advanced_data()))
    assert summary["overall"].iloc[0].n_sequences == 8
    assert summary["overall"].iloc[0].n_pairs == 28
    assert len(summary["per_sequence"]) == 8


def test_r_hierarchical_cluster_validation_and_representatives():
    distance = g.compute_sequence_distance(advanced_data(), method="lcs")
    fit = g.cluster_sequences(distance, k=2, method="hierarchical")
    assert len(fit.assignments) == 8 and len(set(fit.assignments.tolist())) == 2
    validation = g.validate_sequence_clusters(fit)
    overall = validation["overall"].iloc[0]
    assert overall.n_sequences == 8 and -1 <= overall.average_silhouette <= 1
    reps = g.extract_representative_sequences(fit, n_per_cluster=2)
    assert len(reps) == 4


def test_r_pam_native_backend_available():
    fit = g.cluster_sequences(g.compute_sequence_distance(advanced_data()), 2, method="pam")
    assert len(fit.assignments) == 8


def test_r_bootstrap_cluster_stability_reproducible():
    distance = g.compute_sequence_distance(advanced_data(), method="lcs")
    a = g.bootstrap_sequence_clusters(distance, 2, n_boot=8, sample_fraction=0.75, seed=41)
    b = g.bootstrap_sequence_clusters(distance, 2, n_boot=8, sample_fraction=0.75, seed=41)
    pd.testing.assert_frame_equal(a.pairwise_stability, b.pairwise_stability)
    summary = g.summarise_sequence_cluster_stability(a)
    assert len(summary["clusters"]) == 2
    value = summary["overall"].iloc[0].mean_pairwise_stability
    assert 0 <= value <= 1


def test_r_cluster_ensemble_coassociation_contract():
    d1 = g.compute_sequence_distance(advanced_data(), method="lcs")
    d2 = g.compute_sequence_distance(advanced_data(), method="transition")
    c1 = g.cluster_sequences(d1, 2)
    c2 = g.cluster_sequences(d2, 2)
    ensemble = g.create_sequence_cluster_ensemble(c1, c2, k=2)
    assert np.allclose(np.diag(ensemble.coassociation), 1)
    assert ((ensemble.coassociation >= 0) & (ensemble.coassociation <= 1)).to_numpy().all()
    assert len(set(ensemble.assignments.tolist())) == 2


def test_r_distance_and_substitution_metric_guards():
    data = advanced_data()
    states = sorted(data.state.unique())
    asymmetric = pd.DataFrame(1.0, index=states, columns=states)
    for state in states:
        asymmetric.loc[state, state] = 0.0
    asymmetric.iloc[0, 1] = 2
    with pytest.raises(ValidationError, match="symmetric"):
        g.compute_sequence_distance(data, method="optimal_matching", substitution_matrix=asymmetric)
    bad_diag = pd.DataFrame(1.0, index=states, columns=states)
    with pytest.raises(ValidationError, match="diagonal"):
        g.compute_sequence_distance(data, method="optimal_matching", substitution_matrix=bad_diag)
    bad_distance = np.array([[0, 1], [2, 0]], dtype=float)
    with pytest.raises(ValidationError, match="symmetric"):
        g.validate_sequence_clusters(pd.Series([1, 2], index=["a", "b"]), bad_distance)


def test_r_clara_preserves_sequence_identifiers():
    distance = g.compute_sequence_distance(advanced_data())
    fit = g.cluster_sequences(distance, 2, method="clara", seed=19, samples=3)
    assert set(fit.assignments.index.astype(str)) == set(distance.labels)


def test_r_stochastic_cluster_helpers_do_not_mutate_global_numpy_rng():
    distance = g.compute_sequence_distance(advanced_data())
    np.random.seed(777)
    before = np.random.get_state()
    g.bootstrap_sequence_clusters(distance, 2, n_boot=3, sample_fraction=0.75, seed=9)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]


def test_r_character_cluster_assignments_supported():
    distance = g.compute_sequence_distance(advanced_data())
    assignments = pd.Series(["left"] * 4 + ["right"] * 4, index=distance.labels)
    validation = g.validate_sequence_clusters(assignments, distance)
    assert validation["overall"].iloc[0].n_clusters == 2
    assert set(validation["cluster_sizes"].cluster.astype(str)) == {"left", "right"}


def test_r_unused_categorical_levels_not_observed_distance_states():
    data = advanced_data()
    data["state"] = pd.Categorical(data.state, categories=["A", "B", "C", "D", "UNUSED"])
    states = ["A", "B", "C", "D"]
    costs = pd.DataFrame(1.0, index=states, columns=states)
    for state in states:
        costs.loc[state, state] = 0.0
    distance = g.compute_sequence_distance(
        data, method="optimal_matching", substitution_matrix=costs
    )
    assert "UNUSED" not in set(distance.sequences.state.astype(str))


def test_r_ensemble_linkage_and_stability_validation():
    data = advanced_data()
    d1 = g.compute_sequence_distance(data, method="lcs")
    d2 = g.compute_sequence_distance(data, method="transition")
    c1 = g.cluster_sequences(d1, 2)
    c2 = g.cluster_sequences(d2, 2)
    with pytest.raises(ValidationError, match="not a supported"):
        g.create_sequence_cluster_ensemble(c1, c2, k=2, linkage="unknown")
    boot = g.bootstrap_sequence_clusters(d1, 2, n_boot=2, sample_fraction=0.5, seed=4)
    summary = g.summarise_sequence_cluster_stability(boot)
    assert "n_evaluated_pairs" in summary["clusters"].columns
    assert (summary["clusters"].n_evaluated_pairs >= 0).all()


def test_r_clara_repeatable_and_global_rng_safe():
    distance = g.compute_sequence_distance(advanced_data(), method="lcs")
    np.random.seed(321)
    before = np.random.get_state()
    first = g.cluster_sequences(distance, 2, method="clara", seed=12, samples=4, sampsize=6)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]
    second = g.cluster_sequences(distance, 2, method="clara", seed=12, samples=4, sampsize=6)
    pd.testing.assert_series_equal(first.assignments, second.assignments)


def test_r_integer_seed_controls_reject_invalid_values_and_boundary_safe():
    distance = g.compute_sequence_distance(advanced_data())
    with pytest.raises(ValidationError):
        g.cluster_sequences(distance, 2, seed=2**31)
    with pytest.raises(ValidationError, match="seed"):
        g.cluster_sequences(distance, 2, seed=-1)
    result = g.bootstrap_sequence_clusters(
        distance, 2, n_boot=1, sample_fraction=0.75, seed=2**31 - 1
    )
    assert result is not None


def test_r_additional_clustering_positional_arguments_rejected_by_python_signature():
    distance = g.compute_sequence_distance(advanced_data())
    with pytest.raises(TypeError):
        g.cluster_sequences(distance, 2, "hierarchical", "average", 1, 1)


# ---- networks -----------------------------------------------------------


def test_r_first_order_network_edge_measures():
    data = advanced_data()
    network = g.create_transition_network(data, normalise="from")
    assert {
        "from_state",
        "to_state",
        "count",
        "weight",
        "sequence_count",
        "sequence_prevalence",
    }.issubset(network.columns)
    assert np.allclose(network.groupby("context").weight.sum().to_numpy(), 1, atol=1e-12)
    no_self = g.create_transition_network(data, include_self=False)
    assert not (no_self.from_state == no_self.to_state).any()


def test_r_higher_order_network_and_model_contexts():
    data = advanced_data()
    network = g.create_transition_network(data, order=2, normalise="from")
    assert (
        network.from_state.isna().all() and network.context.str.contains(" > ", regex=False).all()
    )
    model = g.fit_higher_order_transition_model(data, order=3, smoothing=0.5, backoff=True)
    pred = g.predict_next_state(model, ["A", "B", "C"])
    assert pred.probability.sum() == pytest.approx(1) and pred.used_order.iloc[0] <= 3
    unseen = g.predict_next_state(model, ["Z"])
    assert unseen.used_order.iloc[0] == 0


def test_r_network_centrality_and_communities_deterministic():
    network = g.create_transition_network(advanced_data(), normalise="count")
    centrality = g.summarise_transition_centrality(network)
    assert {
        "state",
        "total_degree",
        "total_strength",
        "closeness",
        "betweenness",
        "pagerank",
    }.issubset(centrality.columns)
    assert centrality.pagerank.sum() == pytest.approx(1, abs=1e-8)
    a = g.detect_transition_communities(network, seed=9)
    b = g.detect_transition_communities(network, seed=9)
    pd.testing.assert_frame_equal(a, b)
    components = g.detect_transition_communities(network, method="components")
    assert len(components) == len(set(network.from_state) | set(network.to_state))


def test_r_network_bootstrap_reproducible_bounded():
    data = advanced_data()
    a = g.bootstrap_transition_network(data, n_boot=10, seed=17)
    b = g.bootstrap_transition_network(data, n_boot=10, seed=17)
    pd.testing.assert_frame_equal(a, b)
    assert (a.conf_low <= a.conf_high).all() and a.bootstrap_mean.between(0, 1).all()


def test_r_networkx_adapter_contract():
    graph = g.as_igraph_transition_network(g.create_transition_network(advanced_data()))
    assert graph.is_directed() and set(graph.nodes) == set(advanced_data().state.unique())


def test_r_grouped_graph_summaries_require_selection():
    grouped = g.create_transition_network(advanced_data(), group_cols="group")
    with pytest.raises(ValidationError, match="Filter a grouped transition network"):
        g.summarise_transition_centrality(grouped)
    with pytest.raises(ValidationError, match="Filter a grouped transition network"):
        g.detect_transition_communities(grouped)


def test_r_unseen_context_probability_schema():
    model = g.fit_higher_order_transition_model(advanced_data(), order=2)
    unseen = g.predict_next_state(model, "UNSEEN", top_n=2)
    assert {
        "order",
        "context",
        "next_state",
        "count",
        "probability",
        "used_order",
        "used_context",
    }.issubset(unseen.columns)
    assert (unseen.used_order == 0).all() and len(unseen) == 2


def test_r_network_bootstrap_global_rng_safe():
    np.random.seed(901)
    before = np.random.get_state()
    g.bootstrap_transition_network(advanced_data(), n_boot=3, seed=8)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]


def test_r_next_state_blank_history_rejected():
    model = g.fit_higher_order_transition_model(advanced_data(), order=2)
    with pytest.raises(ValidationError, match="non-blank"):
        g.predict_next_state(model, ["A", ""])


def test_r_network_context_separator_guard():
    data = advanced_data()
    data.loc[data.state == "A", "state"] = "A > embedded"
    with pytest.raises(ValidationError, match="must not occur inside"):
        g.create_transition_network(data)
    with pytest.raises(ValidationError, match="must not occur inside"):
        g.fit_higher_order_transition_model(data)
