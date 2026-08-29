import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy._exceptions import ValidationError


def extension_data():
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
        condition = 0 if i <= 4 else 1
        for pos, state in enumerate(path, 1):
            rows.append(
                {
                    "participant_id": f"p{i}",
                    "sequence_id": sid,
                    "sequence_order": pos,
                    "state": state,
                    "group": group,
                    "condition_numeric": condition,
                    "time_scaled": -1 + (pos - 1) * 0.5,
                    "channel_context": ["x", "x", "y", "y", "z"][pos - 1],
                }
            )
    return pd.DataFrame(rows)


def panel_data():
    first = extension_data().copy()
    first["sequence_id"] = first.sequence_id + "_w1"
    first["occasion"] = 1
    second = extension_data().copy()
    second["sequence_id"] = second.sequence_id + "_w2"
    second["occasion"] = 2
    mask = second.sequence_order == 2
    second.loc[mask & (second.group == "g1"), "state"] = "C"
    second.loc[mask & (second.group == "g2"), "state"] = "B"
    return pd.concat([first, second], ignore_index=True)


def motif_vis_data():
    return pd.DataFrame(
        {
            "id": ["s1"] * 5 + ["s2"] * 4 + ["s3"] * 3,
            "position": [1, 2, 3, 4, 5, 1, 2, 3, 4, 1, 2, 3],
            "state": list("ABABC") + list("ABCB") + list("BAB"),
            "group": ["g1"] * 9 + ["g2"] * 3,
        }
    )


def motif_extraction(min_length=2, max_length=3):
    return g.extract_sequence_ngrams(
        motif_vis_data(),
        "id",
        "position",
        "state",
        metadata_cols=["group"],
        min_length=min_length,
        max_length=max_length,
        overlap="allow",
    )


# analysis audit / capabilities / adapters


def test_r_analysis_audit_native_distance():
    audit = g.audit_sequence_analysis(
        g.compute_sequence_distance(extension_data(), method="levenshtein")
    )
    assert audit.contract["family"] == "distance" and audit.status == "pass"
    assert audit.summary.iloc[0].n_sequence_ids == 8 and audit.summary.iloc[0].n_state_levels >= 4


def test_r_analysis_result_comparison_structure_vs_values():
    data = extension_data()
    d1 = g.compute_sequence_distance(data, method="levenshtein")
    d2 = g.compute_sequence_distance(data, method="levenshtein")
    d3 = g.compute_sequence_distance(data, method="lcs")
    same = g.compare_sequence_analysis_results(d1, d2, compare_values=True)
    different = g.compare_sequence_analysis_results(d1, d3)
    assert same.all_equal and not different.all_equal
    assert not bool(
        different.comparisons.loc[different.comparisons.field == "method", "equal"].iloc[0]
    )


def test_r_capabilities_roles_and_native_filter():
    caps = g.sequence_capabilities()
    assert (
        any(caps.role == "native")
        and any(caps.role == "reference")
        and caps.available.isin([True, False]).all()
    )
    native = g.sequence_capabilities(include_optional=False)
    assert len(native) > 0 and (native.role == "native").all() and native.native.all()


def test_r_adapters_deterministic_semantic_translations():
    data = extension_data()
    a = g.as_grpstring_data(data)
    b = g.as_grpstring_data(data)
    assert (
        a.strings == b.strings
        and len(a.strings) == 8
        and len(a.key) == 4
        and all(len(v) == 5 for v in a.strings.values())
    )
    tr = g.as_traminer_sequences(data)
    sh = g.as_seqhmm_sequences(data)
    ar = g.as_arules_sequences(data)
    assert (
        tr.data.shape == (8, 5) and sh.backend == "seqHMM" and len(ar.transaction_info) == len(data)
    )


# panel/subsequence


def test_r_panel_prepare_and_summary_contract():
    panel = g.prepare_sequence_panel(panel_data(), "participant_id", "occasion")
    assert (
        len(panel.index) == 16
        and panel.index.panel_id.nunique() == 8
        and sorted(panel.index.occasion_rank.unique()) == [1, 2]
    )
    summary = g.summarise_sequence_panel(panel)
    assert (
        summary["n_panels"] == 8
        and summary["n_occasions"] == 2
        and {"occasions", "states"} <= set(summary)
    )


def test_r_panel_changes_deterministic_and_plot():
    panel = g.prepare_sequence_panel(panel_data(), "participant_id", "occasion")
    changes = g.compare_sequence_panel_changes(panel, method="lcs")
    assert len(changes) == 8 and (changes.distance >= 0).all()
    plotted = g.plot_sequence_panel_changes(changes, type="summary")
    pd.testing.assert_frame_equal(plotted, changes)
    plt.close(plt.gcf())
    altered = changes.copy()
    altered["distance"] = 1
    plotted = g.plot_sequence_panel_changes(altered, metric="distance", type="summary")
    pd.testing.assert_frame_equal(plotted, altered)
    plt.close(plt.gcf())


def test_r_panel_duplicate_occasion_fails():
    data = panel_data()
    data.loc[data.sequence_id == "s01_w2", "occasion"] = 1
    with pytest.raises(ValidationError, match="More than one sequence"):
        g.prepare_sequence_panel(data, "participant_id", "occasion")


def test_r_subsequence_bounded_extraction():
    out = g.extract_sequence_subsequences(
        extension_data(), metadata_cols="group", min_length=2, max_length=3, max_gap=2, max_span=4
    )
    assert (
        len(out) > 0
        and out.subsequence_length.isin([2, 3]).all()
        and (out.max_observed_gap <= 2).all()
        and (out.span <= 4).all()
    )


def test_r_subsequence_summary_filter_plot():
    out = g.extract_sequence_subsequences(
        extension_data(), metadata_cols="group", min_length=2, max_length=3
    )
    summary = g.summarise_sequence_subsequences(out)
    assert summary.sequence_prevalence.between(0, 1).all()
    filtered = g.filter_sequence_subsequences(summary, min_sequences=2, top_n=5, ties="exclude")
    assert len(filtered) <= 5
    plotted = g.plot_sequence_subsequences(summary, top_n=3)
    assert len(plotted) <= 3


def test_r_subsequence_group_comparison_adjusts_multiple_tests():
    out = g.extract_sequence_subsequences(
        extension_data(), metadata_cols="group", min_length=2, max_length=2
    )
    comparison = g.compare_sequence_subsequences(out, "group")
    assert {"p_value", "p_adjusted"} <= set(comparison.columns) and (
        comparison.p_adjusted >= comparison.p_value - 1e-12
    ).all()


def test_r_subsequence_search_space_limit():
    with pytest.raises(ValidationError, match="exceeds"):
        g.extract_sequence_subsequences(
            extension_data(), max_length=5, max_combinations_per_sequence=2
        )


# motif visualisation


def test_r_motif_positions_absolute_exact():
    extracted = motif_extraction()
    result = g.summarise_sequence_motif_positions(extracted, position="start", scale="absolute")
    assert (
        result.status == "pass"
        and result.settings["position"] == "start"
        and result.settings["scale"] == "absolute"
        and result.settings["by"] == []
    )
    assert len(result.occurrences) == len(extracted.occurrences)
    ab = result.summary.loc[result.summary.motif == "A > B"].iloc[0]
    assert (
        ab.n_occurrences == 4
        and ab.n_sequences == 3
        and ab.min_position == 1
        and ab.max_position == 3
    )
    assert ab.mean_position == pytest.approx(1.75) and ab.median_position == pytest.approx(1.5)
    assert np.allclose(result.occurrences.position_value, result.occurrences.absolute_position)


def test_r_motif_positions_relative_bounded_basis():
    extracted = motif_extraction()
    start = g.summarise_sequence_motif_positions(extracted, "start", "relative")
    centre = g.summarise_sequence_motif_positions(extracted, "centre", "relative")
    end = g.summarise_sequence_motif_positions(extracted, "end", "relative")
    for x in [start, centre, end]:
        assert x.occurrences.position_value.between(0, 1).all()
    assert start.summary.loc[start.summary.motif == "A > B", "mean_position"].iloc[
        0
    ] == pytest.approx(0.25)
    assert centre.summary.loc[centre.summary.motif == "A > B", "mean_position"].iloc[
        0
    ] == pytest.approx(5 / 12)
    assert end.summary.loc[end.summary.motif == "A > B", "mean_position"].iloc[0] == pytest.approx(
        7 / 12
    )


def test_r_motif_positions_grouped_deterministic():
    result = g.summarise_sequence_motif_positions(
        motif_extraction(), position="start", scale="absolute", by="group"
    )
    ab = result.summary.loc[result.summary.motif == "A > B"]
    assert (
        ab.group.tolist() == ["g1", "g2"]
        and ab.n_occurrences.tolist() == [3, 1]
        and ab.n_sequences.tolist() == [2, 1]
    )
    assert (
        np.allclose(ab.mean_position, [5 / 3, 2])
        and result.n_groups == 2
        and result.settings["by"] == ["group"]
    )


def test_r_motif_positions_empty_schema():
    result = g.summarise_sequence_motif_positions(
        motif_extraction(8, 8), position="centre", scale="relative", by="group"
    )
    expected = [
        "group",
        "motif_id",
        "motif_key",
        "motif",
        "motif_length",
        "position_basis",
        "position_scale",
        "n_occurrences",
        "n_sequences",
        "min_position",
        "max_position",
        "mean_position",
        "median_position",
    ]
    assert (
        result.summary.empty
        and result.occurrences.empty
        and list(result.summary.columns) == expected
    )
    assert result.n_occurrences == 0 and result.n_motifs == 0 and result.n_groups == 0


def test_r_motif_position_formatting_display_only():
    positions = g.summarise_sequence_motif_positions(
        motif_extraction(), position="start", scale="relative", by="group"
    )
    original = positions.summary.copy(deep=True)
    formatted = g.format_sequence_motif_positions(
        positions, digits=1, position_units="percent", include_rank=True
    )
    pd.testing.assert_frame_equal(positions.summary, original)
    assert (
        "rank" in formatted["table"]
        and "position_unit" in formatted["table"]
        and set(formatted["table"].position_unit) == {"percent"}
    )
    assert formatted["settings"]["applied_position_units"] == "percent"
    ab = formatted["table"].query("group=='g1' and motif=='A > B'").iloc[0]
    assert ab.mean_position == pytest.approx(16.7)


def test_r_motif_absolute_formatting_stays_index_units():
    positions = g.summarise_sequence_motif_positions(
        motif_extraction(), position="centre", scale="absolute"
    )
    formatted = g.format_sequence_motif_positions(
        positions, digits=2, position_units="percent", include_rank=False
    )
    assert "rank" not in formatted["table"] and set(formatted["table"].position_unit) == {"index"}
    assert formatted["settings"]["applied_position_units"] == "index"
    assert np.allclose(formatted["table"].mean_position, positions.summary.mean_position.round(2))


def test_r_motif_bar_and_empty_plot_contracts():
    summary = g.summarise_sequence_motifs(motif_extraction())
    ax = g.plot_sequence_motifs(
        summary, metric="n_occurrences", top_n=3, ties="first", horizontal=True
    )
    assert len(ax.gp3_data) == 3
    plt.close(ax.figure)
    ax = g.plot_sequence_motifs(
        summary, metric="occurrence_share", top_n=3, ties="first", horizontal=False
    )
    assert len(ax.gp3_data) == 3
    plt.close(ax.figure)
    empty = g.filter_sequence_motifs(summary, min_occurrences=100)
    ax = g.plot_sequence_motifs(empty, top_n=5)
    assert ax.gp3_data.empty
    plt.close(ax.figure)


def test_r_motif_position_plots_filters_and_bounds():
    extracted = motif_extraction()
    ax = g.plot_sequence_motif_positions(
        extracted, position="centre", scale="relative", top_n=2, display="strip"
    )
    assert (
        len(ax.gp3_motif_table) == 2
        and ax.gp3_data.position_value.between(0, 1).all()
        and np.isfinite(ax.gp3_data.plot_y).all()
    )
    motif_id = ax.gp3_motif_table.motif_id.iloc[0]
    plt.close(ax.figure)
    positions = g.summarise_sequence_motif_positions(extracted, position="start", scale="absolute")
    ax = g.plot_sequence_motif_positions(
        positions, motifs="A > B", position="end", scale="absolute", display="distribution"
    )
    assert set(ax.gp3_data.motif) == {"A > B"}
    plt.close(ax.figure)
    ax = g.plot_sequence_motif_positions(
        extracted, motifs=motif_id, position="start", scale="relative", display="strip"
    )
    assert set(ax.gp3_data.motif_id) == {motif_id}
    plt.close(ax.figure)


def test_r_motif_visualisation_invalid_settings():
    extracted = motif_extraction()
    with pytest.raises(ValidationError, match="position"):
        g.summarise_sequence_motif_positions(extracted, position="middle")
    with pytest.raises(ValidationError, match="not preserved"):
        g.summarise_sequence_motif_positions(extracted, by="missing_group")
    positions = g.summarise_sequence_motif_positions(extracted)
    with pytest.raises(ValidationError, match="must not exceed"):
        g.format_sequence_motif_positions(positions, digits=16)
    with pytest.raises(ValidationError, match="top_n"):
        g.plot_sequence_motifs(extracted, top_n=0)
    with pytest.raises(ValidationError, match="not found"):
        g.plot_sequence_motif_positions(extracted, motifs="not-a-motif")
    with pytest.raises(ValidationError, match="display"):
        g.plot_sequence_motif_positions(extracted, display="heatmap")


def test_r_extended_visualisations_accept_core_objects():
    data = extension_data()
    distance = g.compute_sequence_distance(data)
    clustering = g.cluster_sequences(distance, 2)
    network = g.create_transition_network(data)
    axes = [
        g.plot_sequence_index(data),
        g.plot_sequence_state_distribution(data),
        g.plot_sequence_entropy(data),
        g.plot_sequence_distance_heatmap(distance),
        g.plot_transition_network(network),
        g.plot_sequence_cluster_silhouette(clustering, distance),
    ]
    assert all(hasattr(ax, "gp3_data") for ax in axes)
    for ax in axes:
        plt.close(ax.figure)


# inference


def test_r_sequence_inference_design_resampling_contract():
    design = g.declare_sequence_comparison_design("group", "participant_id", design="observational")
    inf = g.test_sequence_group_difference(
        extension_data(),
        design,
        metric="state_prevalence",
        target_state="A",
        n_permutations=49,
        seed=4,
    )
    assert (
        len(inf.unit_data) == 8
        and 0 <= inf.estimate.p_value.iloc[0] <= 1
        and "Associational" in inf.interpretation
    )
    inf = g.bootstrap_sequence_group_difference(inf, n_boot=49, seed=5)
    assert len(inf.bootstrap["interval"]) == 1
    summary = g.summarise_sequence_group_inference(inf)
    assert {"estimate", "bootstrap_interval", "design", "interpretation"} <= set(summary)
    plotted = g.plot_sequence_group_inference(inf, type="group_means")
    assert plotted is inf
    plt.close(plt.gcf())


# latent HMM family


def test_r_single_hmm_deterministic_normalised():
    data = extension_data()
    a = g.fit_sequence_hmm(data, 2, max_iter=40, tolerance=1e-7, seed=11)
    b = g.fit_sequence_hmm(data, 2, max_iter=40, tolerance=1e-7, seed=11)
    assert (
        np.allclose(a.initial_probs, b.initial_probs)
        and np.allclose(a.transition_probs, b.transition_probs)
        and np.allclose(a.emission_probs, b.emission_probs)
    )
    assert (
        a.initial_probs.sum() == pytest.approx(1, abs=1e-10)
        and np.allclose(a.transition_probs.sum(axis=1), 1, atol=1e-10)
        and np.allclose(a.emission_probs.sum(axis=1), 1, atol=1e-10)
    )
    assert np.isfinite(a.log_likelihood)


def test_r_hmm_decoding_one_state_per_observation():
    data = extension_data()
    model = g.fit_sequence_hmm(data, 2, max_iter=30, seed=5)
    for method in ["viterbi", "posterior"]:
        dec = g.decode_sequence_states(model, method=method)
        assert len(dec) == len(data) and dec.posterior_probability.between(0, 1).all()


def test_r_hmm_summary_and_comparison_structured():
    data = extension_data()
    m2 = g.fit_sequence_hmm(data, 2, max_iter=25, seed=3)
    m3 = g.fit_sequence_hmm(data, 3, max_iter=25, seed=4)
    assert {"fit", "initial", "transition", "emission"} <= set(g.summarise_sequence_hmm(m2))
    cmp = g.compare_sequence_hmms(m2, m3)
    assert len(cmp) == 2 and {"delta_aic", "delta_bic", "converged"} <= set(cmp.columns)


def test_r_hmm_mixture_responsibilities_normalised_deterministic():
    data = extension_data()
    a = g.fit_sequence_hmm_mixture(data, 2, 2, max_iter=30, inner_initial_iter=5, seed=21)
    b = g.fit_sequence_hmm_mixture(data, 2, 2, max_iter=30, inner_initial_iter=5, seed=21)
    cols = [c for c in a.responsibilities.columns if c.startswith("component_")]
    assert np.allclose(a.responsibilities[cols].sum(axis=1), 1, atol=1e-10)
    assert np.allclose(a.mixture_weights, b.mixture_weights)
    pd.testing.assert_frame_equal(a.responsibilities, b.responsibilities)
    dec = g.decode_sequence_states(a)
    assert len(dec) == len(data) and set(dec.component).issubset({1, 2})


def test_r_hmm_invalid_symbols_and_probabilities_rejected():
    data = extension_data()
    with pytest.raises(ValidationError, match="does not cover"):
        g.fit_sequence_hmm(data, 2, symbol_levels=["A", "B"])
    with pytest.raises(ValidationError, match="Invalid"):
        g.fit_sequence_hmm(data, 2, initial_probs=[-1, 2])
    with pytest.raises(ValidationError, match="Invalid `initial_probs`"):
        g.fit_sequence_hmm(data, 2, initial_probs=[np.inf, 1])
    with pytest.raises(ValidationError, match="Invalid `transition_probs`"):
        g.fit_sequence_hmm(data, 2, transition_probs=np.array([[1, 0], [np.nan, 1]]))


def test_r_hmm_global_rng_unchanged():
    np.random.seed(321)
    before = np.random.get_state()
    g.fit_sequence_hmm(extension_data(), 2, max_iter=3, seed=2)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]


def test_r_hmm_comparison_common_observation_basis_required():
    data = extension_data()
    full = g.fit_sequence_hmm(data, 2, max_iter=3, seed=1)
    reduced = g.fit_sequence_hmm(data.loc[data.sequence_id != "s08"], 2, max_iter=3, seed=1)
    with pytest.raises(ValidationError, match="same number of observations"):
        g.compare_sequence_hmms(full, reduced)


def test_r_hmm_symbol_levels_unique_unused_excluded():
    data = extension_data()
    with pytest.raises(ValidationError, match="unique"):
        g.fit_sequence_hmm(data, 2, symbol_levels=["A", "A", "B", "C", "D"], max_iter=2)
    data = data.copy()
    data["state"] = pd.Categorical(data.state, categories=["A", "B", "C", "D", "UNUSED"])
    model = g.fit_sequence_hmm(data, 2, max_iter=2, seed=5)
    assert "UNUSED" not in model.symbol_names


def test_r_hmm_comparison_sequence_ids_identical():
    data = extension_data()
    first = g.fit_sequence_hmm(data, 2, max_iter=2, seed=1)
    renamed = data.copy()
    renamed["sequence_id"] = "renamed_" + renamed.sequence_id
    second = g.fit_sequence_hmm(renamed, 2, max_iter=2, seed=1)
    with pytest.raises(ValidationError, match="identical training sequences"):
        g.compare_sequence_hmms(first, second)


def test_r_hmm_seed_boundary_and_state_count_validation():
    data = extension_data()
    with pytest.raises(ValidationError, match="seed"):
        g.fit_sequence_hmm(data, 2, max_iter=1, seed=-1)
    model = g.fit_sequence_hmm_mixture(data, 2, 1, max_iter=1, inner_initial_iter=1, seed=2**31 - 1)
    assert model is not None
    with pytest.raises(ValidationError):
        g.fit_sequence_hmm_mixture(data, 2, [1, 2**31], max_iter=1, inner_initial_iter=1)


# multichannel / covariate / time


def test_r_multichannel_hmm_fit_decode_summary_plot():
    data = extension_data()
    fit = g.fit_multichannel_sequence_hmm(
        data, 2, ["state", "channel_context"], max_iter=4, seed=11
    )
    assert (
        fit.transition_probs.shape == (2, 2)
        and len(fit.emission_probs) == 2
        and np.isfinite(fit.log_likelihood)
    )
    dec = g.decode_multichannel_sequence_states(fit)
    assert len(dec) == len(data) and {"sequence_id", "sequence_order", "latent_state"} <= set(
        dec.columns
    )
    assert {"fit", "initial", "transition", "emission"} <= set(
        g.summarise_multichannel_sequence_hmm(fit)
    )
    plotted = g.plot_multichannel_sequence_hmm(fit, channel="state")
    assert plotted.shape == fit.emission_probs["state"].shape
    plt.close(plt.gcf())


def test_r_covariate_hmm_explicit_design_contract():
    data = extension_data()
    fit = g.fit_covariate_sequence_hmm(
        data,
        2,
        initial_covariate_cols=["condition_numeric"],
        transition_covariate_cols=["condition_numeric"],
        max_iter=3,
        inner_maxit=10,
        seed=12,
    )
    assert fit.emission_probs.shape == (2, 4) and np.isfinite(fit.log_likelihood)
    pred = g.predict_covariate_transition_probabilities(
        fit, pd.DataFrame({"condition_numeric": [0, 1]})
    )
    assert len(pred) == 8 and {"row", "from_state", "to_state", "probability"} <= set(pred.columns)
    assert len(g.decode_covariate_sequence_states(fit)) == len(data) and {
        "fit",
        "initial_coefficients",
        "transition_coefficients",
        "emission",
    } <= set(g.summarise_covariate_sequence_hmm(fit))


def test_r_time_model_auditable_python_translation():
    rng = np.random.default_rng(101)
    rows = []
    for i in range(24):
        group = "g1" if i < 12 else "g2"
        for time in range(1, 13):
            lp = -0.4 + 0.06 * time + 0.35 * (group == "g2") * np.sin(time / 3)
            rows.append(
                {
                    "participant_id": f"p{i + 1}",
                    "sequence_id": f"p{i + 1}",
                    "sequence_order": time,
                    "state": "A" if rng.random() < 1 / (1 + np.exp(-lp)) else "B",
                    "group": group,
                }
            )
    data = pd.DataFrame(rows)
    fit = g.fit_time_varying_sequence_model(
        data, "group", "participant_id", target_state="A", k=3, include_random_effect=False
    )
    assert fit.outcome == "state" and fit.group_levels == ["g1", "g2"]
    pred = g.predict_time_varying_sequence_model(fit)
    assert {"time", "group", "estimate", "lower", "upper"} <= set(
        pred.columns
    ) and pred.estimate.between(0, 1).all()
    summary = g.summarise_time_varying_sequence_model(fit)
    assert {"metadata", "smooth_terms", "converged"} <= set(summary)
    ax = g.plot_time_varying_sequence_model(fit)
    plt.close(ax.figure)
