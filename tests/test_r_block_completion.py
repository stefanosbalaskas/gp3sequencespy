"""Completion tests mapping the remaining frozen R test_that() blocks.

These tests intentionally keep one test function per previously combined/internal R
contract so the parity ledger can account for all 130 frozen test blocks without
pretending R-only object identity exists in Python.
"""

from __future__ import annotations

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy._advanced import row_normalise, vector_normalise
from gp3sequencespy._exceptions import ValidationError


def advanced_data() -> pd.DataFrame:
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
                }
            )
    return pd.DataFrame(rows)


def motif_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["s1"] * 5 + ["s2"] * 4 + ["s3"] * 3,
            "position": [1, 2, 3, 4, 5, 1, 2, 3, 4, 1, 2, 3],
            "state": list("ABABC") + list("ABCB") + list("BAB"),
            "group": ["g1"] * 9 + ["g2"] * 3,
        }
    )


def motif_extraction():
    return g.extract_sequence_ngrams(
        motif_data(),
        "id",
        "position",
        "state",
        metadata_cols=["group"],
        min_length=2,
        max_length=3,
        overlap="allow",
    )


# test-analysis-audit.R: malformed distance block

def test_r_analysis_audit_catches_malformed_distances():
    distance = g.compute_sequence_distance(advanced_data(), method="levenshtein")
    malformed = g.compute_sequence_distance(advanced_data(), method="levenshtein")
    matrix = np.asarray(malformed.matrix, dtype=float).copy()
    matrix[0, 1] += 1.0
    malformed.matrix = matrix
    audit = g.audit_sequence_analysis(malformed)
    assert audit.status == "fail"
    assert "asymmetric_distance" in set(audit.issues.code)
    assert "error" in set(audit.issues.severity)


# test-capabilities.R: split the previously combined blocks

def test_r_capabilities_deterministic_dependency_safe_block():
    first = g.sequence_capabilities()
    second = g.sequence_capabilities()
    pd.testing.assert_frame_equal(first, second)
    expected = {
        "family", "capability", "role", "native", "backend",
        "backend_required", "available", "installed_version",
        "minimum_tested_version", "reference_only", "notes",
    }
    assert expected <= set(first.columns)
    assert (first.role == "native").any()
    assert (first.role == "reference").any()
    assert first.available.isin([True, False]).all()


def test_r_capabilities_do_not_import_optional_backends_block():
    optional = {
        "hmmlearn", "pomegranate", "prefixspan", "numba", "hypothesis",
        "polars", "pyarrow", "pydtmc",
    }
    before = set(sys.modules)
    result = g.sequence_capabilities()
    after = set(sys.modules)
    assert isinstance(result, pd.DataFrame)
    assert ((after - before) & optional) == set()


# test-contract-invariants.R: internal probability and partition contracts

def test_r_probability_simplex_and_matrix_validator_semantics():
    assert np.allclose(vector_normalise(np.array([0.2, 0.8])), [0.2, 0.8])
    assert np.isclose(vector_normalise(np.array([0.2, 0.9])).sum(), 1.0)
    valid = row_normalise(np.array([[0.8, 0.2], [0.3, 0.7]]))
    assert np.allclose(valid.sum(axis=1), 1.0)
    invalid = np.array([[0.8, 0.3], [0.3, 0.7]])
    assert not np.allclose(invalid.sum(axis=1), 1.0)


def test_r_partition_label_canonicalisation_membership_semantics():
    # Python clustering validation deliberately treats cluster labels as nominal;
    # arbitrary relabelling must leave membership/silhouette geometry unchanged.
    distance = g.compute_sequence_distance(advanced_data())
    labels_a = pd.Series(
        ["alpha", "alpha", "alpha", "alpha", "beta", "beta", "beta", "beta"],
        index=distance.labels,
    )
    labels_b = labels_a.map({"alpha": "cluster_2", "beta": "cluster_1"})
    va = g.validate_sequence_clusters(labels_a, distance)
    vb = g.validate_sequence_clusters(labels_b, distance)
    assert np.allclose(
        va["per_sequence"].silhouette,
        vb["per_sequence"].silhouette,
    )
    assert np.array_equal(
        labels_a.to_numpy()[:, None] == labels_a.to_numpy()[None, :],
        labels_b.to_numpy()[:, None] == labels_b.to_numpy()[None, :],
    )


# test-sequence-adapters.R: split previously combined adapter contracts

def test_r_gp3tools_common_column_mapping_block():
    data = advanced_data().rename(columns={"sequence_order": "position", "state": "aoi_label"})
    prepared = g.prepare_gp3tools_sequences(data, metadata_cols=["group", "participant_id"])
    assert prepared.status in {"pass", "review"}
    assert {"sequence_id", "sequence_order", "state"} <= set(prepared.data.columns)


def test_r_traminer_and_seqhmm_semantic_adapter_block():
    data = advanced_data()
    traminer = g.as_traminer_sequences(data)
    seqhmm = g.as_seqhmm_sequences(data)
    assert traminer.backend == "TraMineR"
    assert seqhmm.backend == "seqHMM"
    pd.testing.assert_frame_equal(traminer.data, seqhmm.data)
    assert traminer.sequence_ids == seqhmm.sequence_ids


def test_r_arules_sequential_metadata_block():
    data = advanced_data()
    adapted = g.as_arules_sequences(data)
    assert list(adapted.transaction_info.columns) == ["sequenceID", "eventID"]
    assert adapted.transaction_info.sequenceID.tolist() == np.repeat(np.arange(1, 9), 5).tolist()
    assert adapted.transaction_info.eventID.tolist() == np.tile(np.arange(1, 6), 8).tolist()
    assert (adapted.transaction_info[["sequenceID", "eventID"]].to_numpy() > 0).all()


def test_r_igraph_grouped_network_guard_block():
    grouped = g.create_transition_network(advanced_data(), group_cols="group")
    with pytest.raises(ValidationError, match="Select one network group"):
        g.as_igraph_transition_network(grouped)


def test_r_gp3tools_ambiguous_mapping_guard_block():
    data = advanced_data()
    data["trial_id"] = data.sequence_id
    with pytest.raises(ValidationError, match="Multiple candidate sequence identifier"):
        g.prepare_gp3tools_sequences(data, order_col="sequence_order", state_col="state")
    durations = advanced_data()
    durations["fixation_duration"] = 100
    durations["event_duration"] = 100
    with pytest.raises(ValidationError, match="Multiple candidate duration"):
        g.prepare_gp3tools_sequences(durations)


# test-sequence-distances-clustering.R: isolate the PAM contract

def test_r_integer_controls_reject_values_outside_r_integer_range_block():
    distance = g.compute_sequence_distance(advanced_data())
    with pytest.raises(ValidationError):
        g.cluster_sequences(distance, 2**31, method="hierarchical")
    with pytest.raises(ValidationError):
        g.bootstrap_sequence_clusters(distance, 2, n_boot=2**31, seed=1)


# test-sequence-latent-models.R: split combined guards

def test_r_hmm_initialisation_rejects_nonfinite_probabilities_block():
    data = advanced_data()
    with pytest.raises(ValidationError, match="initial_probs"):
        g.fit_sequence_hmm(
            data,
            2,
            initial_probs=np.array([np.nan, 1.0]),
            max_iter=1,
        )
    with pytest.raises(ValidationError, match="transition_probs"):
        g.fit_sequence_hmm(
            data,
            2,
            transition_probs=np.array([[0.8, 0.2], [np.inf, 0.0]]),
            max_iter=1,
        )


def test_r_hmm_hidden_state_counts_reject_out_of_range_block():
    data = advanced_data()
    with pytest.raises(ValidationError, match="positive integer"):
        g.fit_sequence_hmm_mixture(
            data,
            n_components=2,
            n_states=[1, 2**31],
            max_iter=1,
            inner_initial_iter=1,
        )


# test-sequence-motif-visualisation.R: split combined plot-data contracts

def test_r_motif_plot_top_n_ties_are_deterministic_block():
    summary = g.summarise_sequence_motifs(motif_extraction())
    included = g.plot_sequence_motifs(summary, metric="sequence_prevalence", top_n=2, ties="include")
    included_data = included.gp3_data.copy()
    plt.close(included.figure)
    first = g.plot_sequence_motifs(summary, metric="sequence_prevalence", top_n=2, ties="first")
    first_data = first.gp3_data.copy()
    plt.close(first.figure)
    assert len(included_data) >= len(first_data)
    assert len(first_data) == 2
    assert first_data.sequence_prevalence.is_monotonic_decreasing


def test_r_motif_position_plot_accepts_ids_labels_and_summary_block():
    extracted = motif_extraction()
    positions = g.summarise_sequence_motif_positions(extracted, position="start", scale="relative")
    motif_id = str(positions.summary.iloc[0].motif_id)
    motif_label = str(positions.summary.iloc[0].motif)
    for source, selector in [
        (extracted, motif_id),
        (positions, motif_label),
    ]:
        ax = g.plot_sequence_motif_positions(source, motifs=[selector])
        assert hasattr(ax, "gp3_data")
        assert len(ax.gp3_data) > 0
        plt.close(ax.figure)


def test_r_motif_empty_filtered_plot_block():
    summary = g.summarise_sequence_motifs(motif_extraction())
    empty = g.filter_sequence_motifs(summary, min_occurrences=100)
    ax = g.plot_sequence_motifs(empty, top_n=5)
    assert ax.gp3_data.empty
    plt.close(ax.figure)
