from __future__ import annotations

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from gp3sequencespy import visualisations
from gp3sequencespy._exceptions import ValidationError
from gp3sequencespy._types import GroupComparisonResult


@pytest.fixture(autouse=True)
def _close_figures_between_tests():
    plt.close("all")
    yield
    plt.close("all")


def _long_sequences() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s2", "s3", "s3"],
            "sequence_order": [1, 2, 1, 1, 2],
            "state": ["B", "A", "A", "C", "A"],
        }
    )


def _consensus() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "group": ["g1", "g1", "g2", "g2"],
            "sequence_order": [1, 2, 1, 2],
            "consensus_state": ["A", np.nan, "B", "A"],
            "agreement": [0.8, 0.5, 0.7, 1.0],
        }
    )
    frame.attrs["gp3_class"] = "gp3_consensus_sequence"
    frame.attrs["group_cols"] = ["group"]
    frame.attrs["state_levels"] = ["A", "B"]
    return frame


def _comparison(**overrides) -> GroupComparisonResult:
    values = {
        "groups": pd.DataFrame({"group": ["g1", "g2"]}),
        "state_summary": pd.DataFrame(
            {
                "group": ["g1", "g2", "g1", "g2"],
                "state": ["A", "A", "B", "B"],
                "sequence_prevalence": [0.8, 0.4, 0.3, 0.7],
            }
        ),
        "state_contrasts": None,
        "transition_summary": pd.DataFrame(
            {
                "group": ["g1", "g2"],
                "transition": ["A -> B", "A -> B"],
                "sequence_prevalence": [0.5, 0.25],
            }
        ),
        "transition_contrasts": None,
        "length_summary": pd.DataFrame({"group": ["g1", "g2"], "mean_length": [2.0, 1.5]}),
        "length_contrasts": None,
        "settings": {},
    }
    values.update(overrides)
    return GroupComparisonResult(**values)


def _distance() -> pd.DataFrame:
    return pd.DataFrame(
        [[0.0, 2.0, 1.0], [2.0, 0.0, 3.0], [1.0, 3.0, 0.0]],
        index=["s1", "s2", "s3"],
        columns=["s1", "s2", "s3"],
    )


def _network() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "from_state": ["A", "A", "B"],
            "to_state": ["A", "B", "A"],
            "weight": [0.5, 1.0, 0.25],
        }
    )
    frame.attrs["gp3_class"] = "gp3_transition_network"
    frame.attrs["settings"] = {"order": 1}
    return frame


def test_palette_and_consensus_validation_group_selection_paths():
    with pytest.raises(ValidationError, match="Unknown plotting palette"):
        visualisations._palette_cmap("definitely-not-a-matplotlib-palette")

    with pytest.raises(ValidationError, match="type"):
        visualisations.plot_consensus_sequence(_consensus(), type="bad")
    with pytest.raises(ValidationError, match="create_consensus_sequence"):
        visualisations.plot_consensus_sequence(pd.DataFrame())
    with pytest.raises(ValidationError, match="Select one consensus group"):
        visualisations.plot_consensus_sequence(_consensus())
    with pytest.raises(ValidationError, match="one value per group column"):
        visualisations.plot_consensus_sequence(_consensus(), group={"wrong": "g1"})
    with pytest.raises(ValidationError, match="one value per group column"):
        visualisations.plot_consensus_sequence(_consensus(), group={"group": ["g1"]})
    with pytest.raises(ValidationError, match="No consensus positions"):
        visualisations.plot_consensus_sequence(_consensus(), group="missing")

    single = _consensus().iloc[:2].copy()
    single.attrs["gp3_class"] = "gp3_consensus_sequence"
    single.attrs["group_cols"] = ["group"]
    single.attrs["state_levels"] = ["A", "B"]
    single_ax = visualisations.plot_consensus_sequence(single)
    assert len(single_ax.gp3_data) == 2

    nullable = _consensus().iloc[:2].copy()
    nullable["group"] = [np.nan, "g1"]
    nullable.attrs["gp3_class"] = "gp3_consensus_sequence"
    nullable.attrs["group_cols"] = ["group"]
    nullable.attrs["state_levels"] = ["A", "B"]
    ax = visualisations.plot_consensus_sequence(nullable, group={"group": np.nan}, type="states")
    assert len(ax.gp3_data) == 1
    assert ax.gp3_data["group"].isna().all()


def test_group_comparison_validation_and_length_paths():
    with pytest.raises(ValidationError, match="Invalid comparison component"):
        visualisations.plot_sequence_group_comparison(_comparison(), component="bad")
    with pytest.raises(ValidationError, match="compare_sequence_groups"):
        visualisations.plot_sequence_group_comparison(object())
    with pytest.raises(ValidationError, match="Length summaries"):
        visualisations.plot_sequence_group_comparison(
            _comparison(length_summary=None), component="length"
        )
    with pytest.raises(ValidationError, match="Unknown length measure"):
        visualisations.plot_sequence_group_comparison(
            _comparison(), component="length", measure="missing"
        )
    with pytest.raises(ValidationError, match="requested component"):
        visualisations.plot_sequence_group_comparison(
            _comparison(state_summary=None), component="state"
        )
    with pytest.raises(ValidationError, match="Unknown comparison measure"):
        visualisations.plot_sequence_group_comparison(
            _comparison(), component="state", measure="missing"
        )

    ax = visualisations.plot_sequence_group_comparison(_comparison(), component="length")
    assert ax.gp3_data.mean_length.tolist() == [2.0, 1.5]
    transition_ax = visualisations.plot_sequence_group_comparison(
        _comparison(), component="transition", top_n=1
    )
    assert transition_ax.gp3_matrix.shape == (1, 2)


def test_sequence_index_sorting_levels_and_label_suppression():
    data = _long_sequences()
    with pytest.raises(ValidationError, match="sort_by"):
        visualisations.plot_sequence_index(data, sort_by="bad")
    with pytest.raises(ValidationError, match="does not cover"):
        visualisations.plot_sequence_index(data, state_levels=["A", "B"])

    by_length = visualisations.plot_sequence_index(
        data, sort_by="length", show_sequence_labels=False
    )
    assert by_length.gp3_data.index.tolist() == ["s2", "s1", "s3"]
    assert len(by_length.get_yticks()) == 0

    by_path = visualisations.plot_sequence_index(data, sort_by="path")
    assert by_path.gp3_data.index.tolist()[0] == "s2"


def test_state_distribution_count_path_and_entropy_non_normalised_paths():
    data = _long_sequences()
    counts = visualisations.plot_sequence_state_distribution(data, proportion=False)
    assert counts.get_ylabel() == "State count"
    assert counts.gp3_data.loc[1].sum() == 3

    entropy = visualisations.plot_sequence_entropy(data, normalise=False)
    assert entropy.get_ylabel() == "Entropy"
    assert not entropy.gp3_data.normalised.any()

    one_state = pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s2", "s2"],
            "sequence_order": [1, 2, 1, 2],
            "state": ["A", "A", "A", "A"],
        }
    )
    normalised = visualisations.plot_sequence_entropy(one_state, normalise=True)
    assert np.allclose(normalised.gp3_data.entropy, 0.0)


def test_distance_heatmap_mapping_validation_and_hidden_labels():
    distance = _distance()
    with pytest.raises(ValidationError, match="named for every sequence"):
        visualisations.plot_sequence_distance_heatmap(distance, order_by=[1, 2, 3])
    with pytest.raises(ValidationError, match="named for every sequence"):
        visualisations.plot_sequence_distance_heatmap(distance, order_by={"s1": 1, "s2": 2})

    ax = visualisations.plot_sequence_distance_heatmap(
        distance,
        order_by={"s1": 2, "s2": 1, "s3": 1},
        show_labels=False,
    )
    assert ax.gp3_data.index.tolist() == ["s2", "s3", "s1"]
    assert len(ax.get_xticks()) == 0
    assert len(ax.get_yticks()) == 0


def test_transition_network_guards_threshold_self_loop_and_edge_paths():
    with pytest.raises(ValidationError, match="create_transition_network"):
        visualisations.plot_transition_network(pd.DataFrame())

    higher = _network()
    higher.attrs["settings"] = {"order": 2}
    with pytest.raises(ValidationError, match="first-order"):
        visualisations.plot_transition_network(higher)

    grouped = _network()
    grouped["group_key"] = ["g1", "g2", "g1"]
    with pytest.raises(ValidationError, match="one group"):
        visualisations.plot_transition_network(grouped)

    nonnumeric = _network()
    nonnumeric["weight"] = ["a", "b", "c"]
    with pytest.raises(ValidationError, match="numeric network column"):
        visualisations.plot_transition_network(nonnumeric)

    with pytest.raises(ValidationError, match="No edges satisfy"):
        visualisations.plot_transition_network(_network(), minimum_weight=10)

    ax = visualisations.plot_transition_network(_network(), minimum_weight=0.5)
    assert len(ax.gp3_data) == 2
    assert len(ax.patches) >= 1
    assert len(ax.texts) >= 2
