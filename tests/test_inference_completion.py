from __future__ import annotations

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from gp3sequencespy import inference
from gp3sequencespy._exceptions import ValidationError


def _data() -> pd.DataFrame:
    rows = []
    paths = {
        "s1": ("g1", "u1", ["A", "B", "A"]),
        "s2": ("g1", "u2", ["A", "A"]),
        "s3": ("g2", "u3", ["B", "A", "B", "A"]),
        "s4": ("g2", "u4", ["B", "B", "A"]),
    }
    for sid, (group, unit, states) in paths.items():
        for order, state in enumerate(states, 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": order,
                    "state": state,
                    "group": group,
                    "unit": unit,
                }
            )
    return pd.DataFrame(rows)


def test_design_pair_requirement_and_metric_specific_paths():
    with pytest.raises(ValidationError, match="pair_col"):
        inference.declare_sequence_comparison_design("group", "unit", design="paired_randomized")

    design = inference.declare_sequence_comparison_design("group", "unit")
    transition = inference.test_sequence_group_difference(
        _data(), design, metric="transition_count", n_permutations=2, seed=2
    )
    assert transition.unit_data.metric.min() >= 1

    prevalence = inference.test_sequence_group_difference(
        _data(),
        design,
        metric="state_prevalence",
        target_state="A",
        n_permutations=2,
        alternative="greater",
        seed=2,
    )
    assert prevalence.unit_data.metric.between(0, 1).all()

    subsequence = inference.test_sequence_group_difference(
        _data(),
        design,
        metric="subsequence_presence",
        target_subsequence="A > B",
        n_permutations=2,
        alternative="less",
        seed=2,
    )
    assert set(subsequence.unit_data.metric.unique()) <= {0.0, 1.0}


def test_permute_paired_and_cluster_validation_paths():
    paired = inference.declare_sequence_comparison_design(
        "group", "unit", design="paired_randomized", pair_col="pair"
    )
    invalid_pair = pd.DataFrame(
        {
            "group": ["g1", "g1"],
            "unit": ["u1", "u2"],
            "pair": ["p1", "p1"],
            "metric": [1.0, 2.0],
        }
    )
    with pytest.raises(ValidationError, match="exactly one unit from each group"):
        inference._permute(invalid_pair, paired, ["g1", "g2"], np.random.default_rng(1))

    class FlipRng:
        @staticmethod
        def random():
            return 0.1

    valid_pairs = pd.DataFrame(
        {
            "group": ["g1", "g2", "g1", "g2"],
            "unit": ["u1", "u2", "u3", "u4"],
            "pair": ["p1", "p1", "p2", "p2"],
            "metric": [1.0, 2.0, 3.0, 4.0],
        }
    )
    swapped = inference._permute(valid_pairs, paired, ["g1", "g2"], FlipRng())
    assert swapped.tolist() == ["g2", "g1", "g2", "g1"]

    clustered = inference.declare_sequence_comparison_design(
        "group", "unit", design="randomized", cluster_col="cluster"
    )
    mixed_cluster = pd.DataFrame(
        {
            "group": ["g1", "g2"],
            "unit": ["u1", "u2"],
            "cluster": ["c1", "c1"],
            "metric": [1.0, 2.0],
        }
    )
    with pytest.raises(ValidationError, match="one group label"):
        inference._permute(
            mixed_cluster,
            clustered,
            ["g1", "g2"],
            np.random.default_rng(1),
        )


def test_group_value_and_two_group_guards(monkeypatch):
    design = inference.declare_sequence_comparison_design("group", "unit")
    sequence_data = pd.DataFrame({"sequence_id": ["s1"]})

    blank_unit = pd.DataFrame({"group": [""], "unit": ["u1"], "metric": [1.0], "n_sequences": [1]})
    monkeypatch.setattr(
        inference,
        "_metric_data",
        lambda *args, **kwargs: (sequence_data, blank_unit, ["A"]),
    )
    with pytest.raises(ValidationError, match="Group values"):
        inference.test_sequence_group_difference(sequence_data, design, n_permutations=1)

    one_group = pd.DataFrame({"group": ["g1"], "unit": ["u1"], "metric": [1.0], "n_sequences": [1]})
    monkeypatch.setattr(
        inference,
        "_metric_data",
        lambda *args, **kwargs: (sequence_data, one_group, ["A"]),
    )
    with pytest.raises(ValidationError, match="exactly two groups"):
        inference.test_sequence_group_difference(sequence_data, design, n_permutations=1)


def test_bootstrap_summary_and_plot_guard_paths():
    with pytest.raises(ValidationError, match="test_sequence_group_difference"):
        inference.bootstrap_sequence_group_difference(object())
    with pytest.raises(ValidationError, match="test_sequence_group_difference"):
        inference.summarise_sequence_group_inference(object())
    with pytest.raises(ValidationError, match="test_sequence_group_difference"):
        inference.plot_sequence_group_inference(object())

    design = inference.declare_sequence_comparison_design("group", "unit")
    result = inference.test_sequence_group_difference(_data(), design, n_permutations=2, seed=4)
    with pytest.raises(ValidationError, match="Invalid type"):
        inference.plot_sequence_group_inference(result, type="bad")

    returned = inference.plot_sequence_group_inference(result, type="permutation")
    assert returned is result

    summary_before = inference.summarise_sequence_group_inference(result)
    assert summary_before["bootstrap_interval"] is None
    inference.bootstrap_sequence_group_difference(result, n_boot=2, seed=5)
    summary_after = inference.summarise_sequence_group_inference(result)
    assert summary_after["bootstrap_interval"] is not None
