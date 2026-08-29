import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy._exceptions import ValidationError


def data8():
    ids = [f"s{i:02d}" for i in range(1, 9)]
    paths = [
        ["A", "B", "C", "D", "A"],
        ["A", "B", "C", "C", "A"],
        ["A", "C", "C", "D", "A"],
        ["B", "B", "C", "D", "A"],
        ["D", "C", "B", "A", "A"],
        ["D", "C", "A", "A", "B"],
        ["D", "B", "B", "A", "C"],
        ["C", "C", "B", "A", "D"],
    ]
    rows = []
    for i, (sid, path) in enumerate(zip(ids, paths, strict=True)):
        group = "g1" if i < 4 else "g2"
        for pos, state in enumerate(path, 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": pos,
                    "state": state,
                    "group": group,
                    "participant_id": f"p{i + 1}",
                }
            )
    return pd.DataFrame(rows)


def test_frozen_81_function_manifest_is_present():
    manifest = json.loads(
        (Path(__file__).parents[1] / "reference" / "api_manifest.json").read_text()
    )
    names = [row["name"] for row in manifest]
    missing = [name for name in names if not hasattr(g, name)]
    assert len(names) == 81
    assert missing == []
    assert set(names).issubset(set(g.__all__))


def test_grpstring_and_transaction_adapters_are_deterministic():
    data = data8()
    a = g.as_grpstring_data(data)
    b = g.as_grpstring_data(data)
    assert a.strings == b.strings
    assert len(a.strings) == 8
    assert len(a.key) == 4
    assert all(len(v) == 5 for v in a.strings.values())
    ar = g.as_arules_sequences(data)
    assert list(ar.transaction_info.columns) == ["sequenceID", "eventID"]
    assert ar.transaction_info.sequenceID.tolist() == np.repeat(np.arange(1, 9), 5).tolist()
    assert ar.transaction_info.eventID.tolist() == np.tile(np.arange(1, 6), 8).tolist()
    wide = g.as_traminer_sequences(data)
    assert wide.data.shape == (8, 5)
    assert wide.sequence_ids == [f"s{i:02d}" for i in range(1, 9)]
    seqhmm = g.as_seqhmm_sequences(data)
    assert seqhmm.backend == "seqHMM"


def test_network_adapter_and_group_guard():
    data = data8()
    network = g.create_transition_network(data)
    graph = g.as_igraph_transition_network(network)
    assert graph.is_directed()
    assert set(graph.nodes()) == set(data.state.unique())
    grouped = g.create_transition_network(data, group_cols="group")
    with pytest.raises(ValidationError, match="Select one network group"):
        g.as_igraph_transition_network(grouped)


def test_gp3tools_mapping_and_ambiguity_guards():
    data = data8().rename(columns={"sequence_order": "position", "state": "aoi_label"})
    prepared = g.prepare_gp3tools_sequences(data, metadata_cols=["group", "participant_id"])
    assert prepared.status in {"pass", "review"}
    assert {"sequence_id", "sequence_order", "state"}.issubset(prepared.data.columns)
    ambiguous = data8()
    ambiguous["trial_id"] = ambiguous.sequence_id
    with pytest.raises(ValidationError, match="Multiple candidate sequence identifier"):
        g.prepare_gp3tools_sequences(ambiguous, order_col="sequence_order", state_col="state")
    durations = data8()
    durations["fixation_duration"] = 100
    durations["event_duration"] = 100
    with pytest.raises(ValidationError, match="Multiple candidate duration"):
        g.prepare_gp3tools_sequences(durations)


def test_analysis_audit_and_comparison_contracts():
    d1 = g.compute_sequence_distance(data8(), method="levenshtein")
    d2 = g.compute_sequence_distance(data8(), method="levenshtein")
    d3 = g.compute_sequence_distance(data8(), method="lcs")
    audit = g.audit_sequence_analysis(d1)
    assert audit.contract["family"] == "distance"
    assert audit.status == "pass"
    assert int(audit.summary.iloc[0].n_sequence_ids) == 8
    assert int(audit.summary.iloc[0].n_state_levels) == 4
    same = g.compare_sequence_analysis_results(d1, d2, compare_values=True)
    different = g.compare_sequence_analysis_results(d1, d3)
    assert same.all_equal
    assert not different.all_equal
    method_row = different.comparisons.loc[different.comparisons.field == "method"].iloc[0]
    assert not bool(method_row.equal)


def test_capabilities_are_deterministic_and_do_not_import_optional_modules():
    optional = {"hmmlearn", "pomegranate", "prefixspan", "hypothesis", "numba"}
    before = set(sys.modules)
    first = g.sequence_capabilities()
    second = g.sequence_capabilities()
    pd.testing.assert_frame_equal(first, second)
    assert {
        "family",
        "capability",
        "role",
        "native",
        "backend",
        "backend_required",
        "available",
        "installed_version",
        "minimum_tested_version",
        "reference_only",
        "notes",
    }.issubset(first.columns)
    native = g.sequence_capabilities(include_optional=False)
    assert len(native) > 0 and native.native.all() and (native.role == "native").all()
    newly = (set(sys.modules) - before) & optional
    assert newly == set()


def test_extended_plots_return_axes_with_plotted_data():
    data = data8()
    consensus = g.create_consensus_sequence(data, group_cols="group")
    with pytest.raises(ValidationError, match="Select one consensus group"):
        g.plot_consensus_sequence(consensus)
    ax = g.plot_consensus_sequence(consensus, group="g1")
    assert len(ax.gp3_data) == 5
    plt.close(ax.figure)
    ax = g.plot_consensus_sequence(g.create_consensus_sequence(data), type="states")
    assert len(ax.gp3_data) == 5
    plt.close(ax.figure)
    comparison = g.compare_sequence_groups(data, "group")
    ax = g.plot_sequence_group_comparison(comparison, "state", top_n=4)
    assert len(ax.gp3_data) > 0
    plt.close(ax.figure)
    ax = g.plot_sequence_group_comparison(comparison, "length")
    assert len(ax.gp3_data) == 2
    plt.close(ax.figure)
    ax = g.plot_sequence_index(data)
    assert ax.gp3_data.shape == (8, 5)
    plt.close(ax.figure)
    ax = g.plot_sequence_state_distribution(data)
    assert ax.gp3_data.shape == (5, 4)
    assert np.allclose(ax.gp3_data.sum(axis=1), 1)
    plt.close(ax.figure)
    ax = g.plot_sequence_entropy(data)
    assert len(ax.gp3_data) == 5
    assert ax.gp3_data.entropy.between(0, 1).all()
    plt.close(ax.figure)
    distance = g.compute_sequence_distance(data)
    clustering = g.cluster_sequences(distance, 2)
    ax = g.plot_sequence_distance_heatmap(distance, order_by=clustering)
    assert ax.gp3_data.shape == (8, 8)
    plt.close(ax.figure)
    network = g.create_transition_network(data, normalise="from")
    ax = g.plot_transition_network(network)
    assert len(ax.gp3_data) > 0
    plt.close(ax.figure)
    ax = g.plot_sequence_cluster_silhouette(clustering, distance)
    assert len(ax.gp3_data) == 8
    plt.close(ax.figure)
