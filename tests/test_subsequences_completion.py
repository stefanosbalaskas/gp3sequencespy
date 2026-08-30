from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import subsequences
from gp3sequencespy._exceptions import ValidationError


def _long(paths: dict[str, list[str]], groups: dict[str, str] | None = None) -> pd.DataFrame:
    rows = []
    for sid, states in paths.items():
        for order, state in enumerate(states, 1):
            row = {"sequence_id": sid, "sequence_order": order, "state": state}
            if groups is not None:
                row["group"] = groups[sid]
            rows.append(row)
    return pd.DataFrame(rows)


def test_subsequence_input_guards_collapse_and_short_sequences():
    for value in (True, -1, np.nan):
        with pytest.raises(ValidationError, match="non-negative"):
            subsequences._validate_inf_nonnegative(value, "gap")

    data = _long({"s1": ["A", "A", "B"]})
    with pytest.raises(ValidationError, match="repeated_state_policy"):
        subsequences.extract_sequence_subsequences(data, repeated_state_policy="bad")

    separator_data = _long({"s1": ["A > X", "B"]})
    with pytest.raises(ValidationError, match="separator"):
        subsequences.extract_sequence_subsequences(separator_data)

    collapsed = subsequences.extract_sequence_subsequences(
        data,
        min_length=2,
        max_length=2,
        repeated_state_policy="collapse",
    )
    assert collapsed.subsequence.tolist() == ["A > B"]

    short = subsequences.extract_sequence_subsequences(
        _long({"s1": ["A"]}), min_length=2, max_length=2
    )
    assert short.empty
    summary = subsequences.summarise_sequence_subsequences(short)
    assert summary.empty


def test_subsequence_summary_and_filter_validation_and_ties_include():
    with pytest.raises(ValidationError, match="extract_sequence_subsequences"):
        subsequences.summarise_sequence_subsequences(pd.DataFrame())
    with pytest.raises(ValidationError, match="Invalid ties"):
        subsequences.filter_sequence_subsequences(pd.DataFrame(), ties="bad")
    with pytest.raises(ValidationError, match="not a subsequence summary"):
        subsequences.filter_sequence_subsequences(pd.DataFrame({"x": [1]}))

    summary = pd.DataFrame(
        {
            "subsequence": ["A > B", "A > C", "B > C"],
            "subsequence_length": [2, 2, 2],
            "occurrence_count": [3, 2, 1],
            "sequence_count": [2, 2, 1],
            "sequence_prevalence": [0.5, 0.5, 0.25],
            "mean_max_gap": [0.0, 0.0, 0.0],
        }
    )
    unbounded = subsequences.filter_sequence_subsequences(summary)
    assert len(unbounded) == 3
    roomy = subsequences.filter_sequence_subsequences(summary, top_n=10)
    assert len(roomy) == 3
    selected = subsequences.filter_sequence_subsequences(summary, top_n=1, ties="include")
    assert selected.subsequence.tolist() == ["A > B", "A > C"]


def test_subsequence_group_comparison_guard_paths():
    base_paths = {
        "s1": ["A", "B"],
        "s2": ["A", "C"],
        "s3": ["A", "B"],
        "s4": ["A", "C"],
    }
    no_meta = subsequences.extract_sequence_subsequences(
        _long(base_paths), min_length=2, max_length=2
    )
    with pytest.raises(ValidationError, match="created by"):
        subsequences.compare_sequence_subsequences(pd.DataFrame(), "group")
    with pytest.raises(ValidationError, match="Invalid test"):
        subsequences.compare_sequence_subsequences(no_meta, "group", test="bad")
    with pytest.raises(ValidationError, match="not retained"):
        subsequences.compare_sequence_subsequences(no_meta, "group")

    blank_groups = {sid: ("" if sid in {"s1", "s2"} else "g2") for sid in base_paths}
    blank = subsequences.extract_sequence_subsequences(
        _long(base_paths, blank_groups),
        metadata_cols="group",
        min_length=2,
        max_length=2,
    )
    with pytest.raises(ValidationError, match="Group values"):
        subsequences.compare_sequence_subsequences(blank, "group")

    one_groups = {sid: "g1" for sid in base_paths}
    one = subsequences.extract_sequence_subsequences(
        _long(base_paths, one_groups),
        metadata_cols="group",
        min_length=2,
        max_length=2,
    )
    with pytest.raises(ValidationError, match="At least two groups"):
        subsequences.compare_sequence_subsequences(one, "group")

    two_groups = {"s1": "g1", "s2": "g1", "s3": "g2", "s4": "g2"}
    two = subsequences.extract_sequence_subsequences(
        _long(base_paths, two_groups),
        metadata_cols="group",
        min_length=2,
        max_length=2,
    )
    skipped = subsequences.compare_sequence_subsequences(
        two, "group", min_sequence_count=99
    )
    assert skipped.empty

    fisher = subsequences.compare_sequence_subsequences(
        two, "group", test="fisher", p_adjust="none"
    )
    assert not fisher.empty
    assert fisher.test.eq("fisher").all()
    np.testing.assert_allclose(fisher.p_adjusted, fisher.p_value)

    chisq = subsequences.compare_sequence_subsequences(two, "group", test="chisq")
    assert not chisq.empty
    assert chisq.test.eq("chisq").all()


def test_fisher_rejects_more_than_two_groups_and_chisq_accepts_them():
    paths = {
        "s1": ["A", "B"],
        "s2": ["A", "C"],
        "s3": ["A", "B"],
        "s4": ["A", "C"],
        "s5": ["A", "B"],
        "s6": ["A", "C"],
    }
    groups = {
        "s1": "g1",
        "s2": "g1",
        "s3": "g2",
        "s4": "g2",
        "s5": "g3",
        "s6": "g3",
    }
    occurrences = subsequences.extract_sequence_subsequences(
        _long(paths, groups),
        metadata_cols="group",
        min_length=2,
        max_length=2,
    )
    with pytest.raises(ValidationError, match="limited to two groups"):
        subsequences.compare_sequence_subsequences(occurrences, "group", test="fisher")

    chisq = subsequences.compare_sequence_subsequences(occurrences, "group", test="chisq")
    assert not chisq.empty
    assert "prevalence_difference" not in chisq.columns

    with pytest.raises(ValidationError, match="requested numeric metric"):
        subsequences.plot_sequence_subsequences(pd.DataFrame({"subsequence": ["A > B"]}))
