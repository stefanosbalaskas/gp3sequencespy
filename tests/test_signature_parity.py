from __future__ import annotations

import inspect
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import gp3sequencespy as g

ROOT = Path(__file__).resolve().parents[1]


PLOT_AX_FUNCTIONS = [
    "plot_consensus_sequence",
    "plot_multichannel_sequence_hmm",
    "plot_sequence_cluster_silhouette",
    "plot_sequence_distance_heatmap",
    "plot_sequence_entropy",
    "plot_sequence_group_comparison",
    "plot_sequence_group_inference",
    "plot_sequence_index",
    "plot_sequence_motif_positions",
    "plot_sequence_motifs",
    "plot_sequence_panel_changes",
    "plot_sequence_state_distribution",
    "plot_sequence_subsequences",
    "plot_time_varying_sequence_model",
    "plot_transition_network",
]


def _minimal_sequences() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1"] * 3 + ["s2"] * 3 + ["s3"] * 3,
            "sequence_order": [1, 2, 3] * 3,
            "state": ["A", "B", "C", "A", "C", "C", "B", "B", "C"],
        }
    )


def test_frozen_signature_matrix_has_zero_unexplained_drift_and_matches_runtime():
    matrix = json.loads(
        (ROOT / "reference" / "signature_parity_matrix.json").read_text(encoding="utf-8")
    )
    assert matrix["functions"] == 81
    assert matrix["unexplained_drift"] == []
    assert len(matrix["rows"]) == 81

    for row in matrix["rows"]:
        assert str(inspect.signature(getattr(g, row["name"]))) == row["python_signature"]


def test_matplotlib_ax_extension_is_keyword_only():
    for name in PLOT_AX_FUNCTIONS:
        param = inspect.signature(getattr(g, name)).parameters["ax"]
        assert param.kind is inspect.Parameter.KEYWORD_ONLY
        assert param.default is None


def test_repaired_frozen_defaults_and_variadic_semantics():
    groups_sig = inspect.signature(g.compare_sequence_groups)
    assert groups_sig.parameters["metrics"].default == (
        "state",
        "transition",
        "length",
    )

    hmms = list(inspect.signature(g.compare_sequence_hmms).parameters.values())
    assert hmms[0].kind is inspect.Parameter.VAR_POSITIONAL
    assert hmms[1].kind is inspect.Parameter.VAR_KEYWORD

    assert (
        inspect.signature(g.plot_sequence_motif_positions).parameters["scale"].default == "absolute"
    )
    assert (
        inspect.signature(g.plot_sequence_distance_heatmap).parameters["palette"].default
        == "Viridis"
    )
    assert inspect.signature(g.plot_sequence_index).parameters["palette"].default == "Dark 3"
    assert (
        inspect.signature(g.plot_sequence_state_distribution).parameters["palette"].default
        == "Dark 3"
    )


def test_repaired_palette_arguments_are_operational():
    data = _minimal_sequences()
    distance = g.compute_sequence_distance(data, method="levenshtein")

    heat = g.plot_sequence_distance_heatmap(distance)
    assert heat.images[0].get_cmap().name == "viridis"
    plt.close(heat.figure)

    index = g.plot_sequence_index(data)
    assert index.images[0].get_cmap().name == "tab10"
    plt.close(index.figure)

    dist = g.plot_sequence_state_distribution(data)
    colors = [tuple(line.get_color()) for line in dist.lines]
    assert len(colors) >= 2
    assert len(set(colors)) > 1
    plt.close(dist.figure)
