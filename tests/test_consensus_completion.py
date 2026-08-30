from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import consensus
from gp3sequencespy._exceptions import ValidationError


def _long(groups: list[str] | None = None) -> pd.DataFrame:
    if groups is None:
        groups = ["g1", "g1", "g2", "g2"]
    rows = []
    paths = {
        "s1": ["A", "B"],
        "s2": ["A", "C"],
        "s3": ["B", "A"],
        "s4": ["B", "C"],
    }
    for (sid, states), group in zip(paths.items(), groups, strict=True):
        for order, state in enumerate(states, 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": order,
                    "state": state,
                    "group": group,
                    "weight": 1.0,
                }
            )
    return pd.DataFrame(rows)


def test_consensus_argument_weight_and_min_support_guards():
    data = _long()
    with pytest.raises(ValidationError, match="missing_state_policy"):
        consensus.create_consensus_sequence(data, missing_state_policy="bad")
    with pytest.raises(ValidationError, match="tie_method"):
        consensus.create_consensus_sequence(data, tie_method="bad")
    with pytest.raises(ValidationError, match="weight_col"):
        consensus.create_consensus_sequence(data, weight_col="absent")

    bad = data.copy()
    bad.loc[0, "weight"] = -1
    with pytest.raises(ValidationError, match="finite, non-negative"):
        consensus.create_consensus_sequence(bad, weight_col="weight")

    filtered = consensus.create_consensus_sequence(data, min_support=99)
    assert filtered.empty


def test_consensus_summary_group_empty_and_zero_weight_paths():
    plain = consensus.create_consensus_sequence(_long(), group_cols=None)
    with pytest.raises(ValidationError, match="requires a consensus"):
        consensus.summarise_consensus_agreement(plain, by="group")

    empty = plain.iloc[0:0].copy()
    empty.attrs.update(plain.attrs)
    out = consensus.summarise_consensus_agreement(empty)
    assert out.empty
    assert "weighted_agreement" in out.columns

    manual = pd.DataFrame(
        {
            "sequence_order": [1, 2],
            "consensus_state": ["A", "B"],
            "support_n": [1, 1],
            "support_weight": [0.0, 0.0],
            "agreement": [0.5, 1.0],
            "tie_n": [2, 1],
            "tied_states": ["A | B", "B"],
            "n_sequences": [2, 2],
        }
    )
    manual.attrs["gp3_class"] = "gp3_consensus_sequence"
    manual.attrs["group_cols"] = []
    summary = consensus.summarise_consensus_agreement(manual, threshold=0.75)
    assert np.isnan(summary.loc[0, "weighted_agreement"])
    assert summary.loc[0, "n_ties"] == 1
    assert summary.loc[0, "n_below_threshold"] == 1


def test_consensus_format_order_agreement_and_empty_paths():
    grouped = consensus.create_consensus_sequence(_long(), group_cols="group")
    formatted = consensus.format_consensus_sequence(
        grouped,
        include_order=True,
        include_agreement=True,
        digits=2,
    )
    assert formatted.path.str.contains(":", regex=False).all()
    assert formatted.path.str.contains("[", regex=False).all()

    empty = grouped.iloc[0:0].copy()
    empty.attrs.update(grouped.attrs)
    formatted_empty = consensus.format_consensus_sequence(empty)
    assert formatted_empty.empty
    assert formatted_empty.columns.tolist() == ["group", "path", "n_positions"]


def test_group_comparison_validation_separator_group_and_zero_policy_paths():
    data = _long()
    with pytest.raises(ValidationError, match="zero_policy"):
        consensus.compare_sequence_groups(data, "group", zero_policy="bad")
    with pytest.raises(ValidationError, match="Select at least one"):
        consensus.compare_sequence_groups(data, "group", metrics=[])
    with pytest.raises(ValidationError, match="Select at least one"):
        consensus.compare_sequence_groups(data, "group", metrics=["bad"])

    separator_state = data.copy()
    separator_state.loc[0, "state"] = "A -> X"
    with pytest.raises(ValidationError, match="transition_separator"):
        consensus.compare_sequence_groups(separator_state, "group")

    blank = _long(["", "g1", "g2", "g2"])
    with pytest.raises(ValidationError, match="non-missing and non-blank"):
        consensus.compare_sequence_groups(blank, "group")

    one = _long(["g1", "g1", "g1", "g1"])
    with pytest.raises(ValidationError, match="At least two"):
        consensus.compare_sequence_groups(one, "group")

    with pytest.raises(ValidationError, match="reference"):
        consensus.compare_sequence_groups(data, "group", reference="absent")

    infinite = consensus.compare_sequence_groups(
        data,
        "group",
        metrics=["state"],
        zero_policy="infinite",
        reference="g2",
    )
    assert infinite.state_summary is not None
    assert infinite.transition_summary is None
    assert infinite.length_summary is None
