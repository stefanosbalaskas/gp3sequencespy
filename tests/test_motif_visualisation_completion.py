from __future__ import annotations

import importlib.metadata

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gp3sequencespy as g
from gp3sequencespy import motif_visualisation
from gp3sequencespy._exceptions import ValidationError


@pytest.fixture(autouse=True)
def _close_figures_between_tests():
    plt.close("all")
    yield
    plt.close("all")


def _data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["s1"] * 5 + ["s2"] * 4 + ["s3"] * 3,
            "position": [1, 2, 3, 4, 5, 1, 2, 3, 4, 1, 2, 3],
            "state": list("ABABC") + list("ABCB") + list("BAB"),
            "group": ["g1"] * 9 + ["g2"] * 3,
        }
    )


def _extraction(min_length: int = 2, max_length: int = 3):
    return g.extract_sequence_ngrams(
        _data(),
        "id",
        "position",
        "state",
        metadata_cols=["group"],
        min_length=min_length,
        max_length=max_length,
        overlap="allow",
    )


def test_position_summary_validation_and_reserved_group_guards():
    with pytest.raises(ValidationError, match="extract_sequence_ngrams"):
        motif_visualisation.summarise_sequence_motif_positions(object())
    with pytest.raises(ValidationError, match="position"):
        motif_visualisation.summarise_sequence_motif_positions(_extraction(), position="bad")
    with pytest.raises(ValidationError, match="scale"):
        motif_visualisation.summarise_sequence_motif_positions(_extraction(), scale="bad")
    with pytest.raises(ValidationError, match="reserved motif columns"):
        motif_visualisation.summarise_sequence_motif_positions(
            _extraction(), by="motif_id"
        )


def test_position_format_validation_empty_and_ungrouped_rank_paths():
    with pytest.raises(ValidationError, match="summarise_sequence_motif_positions"):
        motif_visualisation.format_sequence_motif_positions(object())

    positions = motif_visualisation.summarise_sequence_motif_positions(_extraction())
    with pytest.raises(ValidationError, match="include_rank"):
        motif_visualisation.format_sequence_motif_positions(positions, include_rank=1)
    with pytest.raises(ValidationError, match="position_units"):
        motif_visualisation.format_sequence_motif_positions(
            positions, position_units="index"
        )

    formatted = motif_visualisation.format_sequence_motif_positions(
        positions, include_rank=True
    )
    assert formatted["table"].rank.min() == 1
    assert formatted["table"].rank.dtype.kind in "iu"

    empty_positions = motif_visualisation.summarise_sequence_motif_positions(
        _extraction(8, 8)
    )
    empty = motif_visualisation.format_sequence_motif_positions(
        empty_positions, include_rank=True
    )
    assert empty["table"].empty
    assert "rank" in empty["table"]


def test_motif_bar_validation_length_filter_and_orientation_guards():
    summary = g.summarise_sequence_motifs(_extraction())
    with pytest.raises(ValidationError, match="metric"):
        motif_visualisation.plot_sequence_motifs(summary, metric="bad")
    with pytest.raises(ValidationError, match="ties"):
        motif_visualisation.plot_sequence_motifs(summary, ties="bad")
    with pytest.raises(ValidationError, match="horizontal"):
        motif_visualisation.plot_sequence_motifs(summary, horizontal=1)

    ax = motif_visualisation.plot_sequence_motifs(
        summary,
        motif_lengths=[2],
        top_n=100,
        ties="include",
    )
    assert not ax.gp3_data.empty
    assert set(ax.gp3_data.motif_length) == {2}


def test_position_plot_validation_empty_and_recomputed_centre_path():
    extracted = _extraction()
    with pytest.raises(ValidationError, match="Invalid position"):
        motif_visualisation.plot_sequence_motif_positions(extracted, position="bad")
    with pytest.raises(ValidationError, match="Invalid scale"):
        motif_visualisation.plot_sequence_motif_positions(extracted, scale="bad")

    empty_ax = motif_visualisation.plot_sequence_motif_positions(_extraction(8, 8))
    assert empty_ax.gp3_data.empty
    assert "plot_y" in empty_ax.gp3_data
    assert len(empty_ax.texts) == 1

    start = motif_visualisation.summarise_sequence_motif_positions(
        extracted, position="start", scale="absolute"
    )
    centre_ax = motif_visualisation.plot_sequence_motif_positions(
        start,
        position="centre",
        scale="relative",
        top_n=2,
        display="strip",
    )
    expected = (
        centre_ax.gp3_data.start_index.astype(float)
        + centre_ax.gp3_data.end_index.astype(float)
    ) / 2
    expected = np.where(
        centre_ax.gp3_data.n_states.to_numpy() <= 1,
        0,
        (expected.to_numpy() - 1)
        / (centre_ax.gp3_data.n_states.to_numpy() - 1),
    )
    assert np.allclose(centre_ax.gp3_data.position_value, np.clip(expected, 0, 1))


def test_position_distribution_matplotlib_compatibility_branches(monkeypatch):
    extracted = _extraction()

    monkeypatch.setattr(importlib.metadata, "version", lambda name: "3.9.9")
    ax39 = motif_visualisation.plot_sequence_motif_positions(
        extracted,
        position="start",
        scale="absolute",
        top_n=2,
        display="distribution",
    )
    assert not ax39.gp3_data.empty

    plt.close("all")
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "3.8.4")
    with pytest.warns((DeprecationWarning, PendingDeprecationWarning)):
        ax38 = motif_visualisation.plot_sequence_motif_positions(
            extracted,
            position="start",
            scale="absolute",
            top_n=2,
            display="distribution",
        )
    assert not ax38.gp3_data.empty
