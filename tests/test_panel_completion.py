from __future__ import annotations

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from gp3sequencespy import panel
from gp3sequencespy._exceptions import ValidationError


def _panel_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s2", "s2"],
            "sequence_order": [1, 2, 1, 2],
            "state": ["A", "B", "A", "C"],
            "person": ["p1", "p1", "p1", "p1"],
            "occasion": ["b", "b", "a", "a"],
        }
    )


def test_prepare_panel_missing_metadata_and_lexical_occasion_order():
    blank_panel = _panel_rows().copy()
    blank_panel["person"] = ["", "", "p1", "p1"]
    with pytest.raises(ValidationError, match="Panel identifiers"):
        panel.prepare_sequence_panel(blank_panel, "person", "occasion")

    blank_occasion = _panel_rows().copy()
    blank_occasion["occasion"] = ["", "", "a", "a"]
    with pytest.raises(ValidationError, match="Occasion values"):
        panel.prepare_sequence_panel(blank_occasion, "person", "occasion")

    prepared = panel.prepare_sequence_panel(_panel_rows(), "person", "occasion")
    ranks = prepared.index.set_index("occasion")["occasion_rank"].to_dict()
    assert ranks == {"a": 1, "b": 2}


def test_prepare_panel_ordered_categorical_occasion_dispatch(monkeypatch):
    categories = pd.Categorical(["late", "early"], categories=["early", "late"], ordered=True)
    metadata = pd.DataFrame(
        {
            "sequence_id": ["s1", "s2"],
            "person": ["p1", "p1"],
            "occasion": categories,
        }
    )
    long_data = pd.DataFrame(
        {
            "sequence_id": ["s1", "s2"],
            "sequence_order": [1, 1],
            "state": ["A", "B"],
        }
    )

    monkeypatch.setattr(
        panel,
        "adv_data",
        lambda *args, **kwargs: {
            "data": long_data,
            "metadata": metadata,
            "sequences": {"s1": ["A"], "s2": ["B"]},
            "orders": {"s1": [1], "s2": [1]},
            "sequence_ids": ["s1", "s2"],
            "state_levels": ["A", "B"],
        },
    )
    prepared = panel.prepare_sequence_panel(long_data, "person", "occasion")
    ranks = prepared.index.set_index("occasion")["occasion_rank"].to_dict()
    assert ranks == {"early": 1, "late": 2}


def test_panel_summary_compare_and_plot_validation_paths():
    with pytest.raises(ValidationError, match="prepare_sequence_panel"):
        panel.summarise_sequence_panel(object())
    with pytest.raises(ValidationError, match="prepare_sequence_panel"):
        panel.compare_sequence_panel_changes(object())

    bad = pd.DataFrame({"x": [1]})
    with pytest.raises(ValidationError, match="compare_sequence_panel_changes"):
        panel.plot_sequence_panel_changes(bad)

    changes = pd.DataFrame(
        {
            "panel_id": ["p1"],
            "from_occasion": ["a"],
            "to_occasion": ["b"],
            "from_rank": [1],
            "to_rank": [2],
            "distance": [1.0],
            "length_change": [0],
            "transition_change": [0],
        }
    )
    changes.attrs["gp3_class"] = "gp3_sequence_panel_changes"

    with pytest.raises(ValidationError, match="Invalid metric"):
        panel.plot_sequence_panel_changes(changes, metric="bad")
    with pytest.raises(ValidationError, match="Invalid type"):
        panel.plot_sequence_panel_changes(changes, type="bad")

    empty = changes.iloc[0:0].copy()
    empty.attrs["gp3_class"] = "gp3_sequence_panel_changes"
    with pytest.raises(ValidationError, match="no panel changes"):
        panel.plot_sequence_panel_changes(empty)


def test_panel_summary_and_individual_plot_paths():
    changes = pd.DataFrame(
        {
            "panel_id": ["p1", "p2", "p1"],
            "from_occasion": ["a", "a", "b"],
            "to_occasion": ["b", "b", "c"],
            "from_rank": [1, 1, 2],
            "to_rank": [2, 2, 3],
            "distance": [1.0, 3.0, 2.0],
            "length_change": [0, 1, -1],
            "transition_change": [0, 1, -1],
        }
    )
    changes.attrs["gp3_class"] = "gp3_sequence_panel_changes"
    returned = panel.plot_sequence_panel_changes(changes, type="summary")
    assert returned is changes
    returned = panel.plot_sequence_panel_changes(changes, type="individual")
    assert returned is changes
