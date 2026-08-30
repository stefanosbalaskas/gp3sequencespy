from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import data as data_mod
from gp3sequencespy._exceptions import ValidationError


def _base() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["s1", "s1", "s2", "s2"],
            "pos": [1.0, 2.0, 1.0, 2.0],
            "label": ["A", "B", "A", "A"],
            "duration_ms": [1.0, 2.0, 3.0, 4.0],
            "meta": ["x", "x", "y", "y"],
        }
    )


def _audit(frame: pd.DataFrame, **kwargs) -> pd.DataFrame:
    return data_mod.audit_sequence_data(
        frame,
        "id",
        "pos",
        "label",
        duration_col=kwargs.pop("duration_col", "duration_ms"),
        metadata_cols=kwargs.pop("metadata_cols", ["meta"]),
        **kwargs,
    )


def _prepare(frame: pd.DataFrame, **kwargs):
    return data_mod.prepare_sequence_data(
        frame,
        "id",
        "pos",
        "label",
        duration_col=kwargs.pop("duration_col", "duration_ms"),
        metadata_cols=kwargs.pop("metadata_cols", ["meta"]),
        **kwargs,
    )


def test_value_text_series_and_isna_exception(monkeypatch):
    assert data_mod._value_text(pd.Series([1, 2])) == "1 | 2"

    original = data_mod.pd.isna
    sentinel = object()

    def fake_isna(value):
        if value is sentinel:
            raise TypeError("sentinel")
        return original(value)

    monkeypatch.setattr(data_mod.pd, "isna", fake_isna)
    assert data_mod._value_text(sentinel).startswith("<object object")


def test_audit_mapping_expected_metadata_and_atomic_type_guards():
    frame = _base()
    with pytest.raises(ValidationError, match="expected_states"):
        _audit(frame, expected_states={"A": 1})
    with pytest.raises(ValidationError, match="distinct columns"):
        data_mod.audit_sequence_data(frame, "id", "id", "label")
    with pytest.raises(ValidationError, match="metadata_cols"):
        data_mod.audit_sequence_data(frame, "id", "pos", "label", metadata_cols=["id"])

    missing_meta = _audit(frame, metadata_cols=["missing"])
    assert "missing_metadata_column" in set(missing_meta.issue_code)

    bad_id = frame.astype(object).copy()
    bad_id.at[0, "id"] = ["s1"]
    audit = _audit(bad_id)
    assert "invalid_sequence_id_type" in set(audit.issue_code)

    bad_state = frame.astype(object).copy()
    bad_state.at[0, "label"] = ["A"]
    audit = _audit(bad_state)
    assert "invalid_state_type" in set(audit.issue_code)

    bad_order = frame.copy()
    bad_order["pos"] = ["1", "2", "1", "2"]
    audit = _audit(bad_order)
    assert "invalid_order_type" in set(audit.issue_code)


def test_audit_missing_nonfinite_duration_metadata_and_empty_valid_positions():
    missing_order = _base()
    missing_order.loc[0, "pos"] = np.nan
    audit = _audit(missing_order)
    assert "missing_sequence_order" in set(audit.issue_code)

    all_order_missing = _base()
    all_order_missing["pos"] = np.nan
    audit = _audit(all_order_missing)
    assert "missing_sequence_order" in set(audit.issue_code)

    bad_duration = _base()
    bad_duration["duration_ms"] = ["1", "2", "3", "4"]
    audit = _audit(bad_duration)
    assert "invalid_duration_type" in set(audit.issue_code)

    infinite_duration = _base()
    infinite_duration.loc[0, "duration_ms"] = np.inf
    audit = _audit(infinite_duration)
    assert "non_finite_duration" in set(audit.issue_code)

    list_meta = _base().astype(object)
    list_meta.at[0, "meta"] = ["x"]
    audit = _audit(list_meta)
    assert "invalid_metadata_type" in set(audit.issue_code)

    no_ids = _base().copy()
    no_ids["id"] = None
    audit = _audit(no_ids)
    assert "missing_sequence_id" in set(audit.issue_code)


def test_validate_list_columns_and_categorical_state_paths():
    frame = _base().astype(object)
    frame.at[0, "id"] = ["s1"]
    result = data_mod.validate_sequence_data(
        frame, "id", "pos", "label", duration_col="duration_ms", metadata_cols=["meta"]
    )
    assert result.n_sequences == 0

    frame2 = _base().astype(object)
    frame2.at[0, "label"] = ["A"]
    result2 = data_mod.validate_sequence_data(
        frame2, "id", "pos", "label", duration_col="duration_ms", metadata_cols=["meta"]
    )
    assert result2.state_levels == []

    categorical = _base().copy()
    categorical["label"] = pd.Categorical(categorical["label"], categories=["A", "B"])
    result3 = data_mod.validate_sequence_data(
        categorical, "id", "pos", "label", duration_col="duration_ms", metadata_cols=["meta"]
    )
    assert result3.state_levels == ["A", "B"]


def test_prepare_zero_duplicate_repeat_unused_and_categorical_output_paths():
    frame = _base().copy()
    frame.loc[0, "duration_ms"] = 0.0
    frame.loc[1, "pos"] = 1.0
    frame["label"] = pd.Categorical(frame["label"], categories=["A", "B", "UNUSED"])

    prepared = _prepare(
        frame,
        zero_duration_policy="drop",
        duplicate_position_policy="first",
        repeated_state_policy="collapse",
        unused_state_levels="drop",
    )
    assert prepared.data is not None
    assert 0.0 not in prepared.data["duration"].tolist()
    assert "UNUSED" not in prepared.state_levels
    assert prepared.data["state"].dtype.name == "category"


def test_prepare_duplicate_first_without_keys_and_collapse_without_duration():
    frame = _base().copy()
    frame["label"] = None
    prepared = _prepare(
        frame,
        missing_state_policy="drop",
        duplicate_position_policy="first",
        duration_col=None,
        repeated_state_policy="collapse",
        metadata_cols=["meta"],
    )
    assert prepared.prepared_n_rows == 0

    repeated = pd.DataFrame(
        {
            "id": ["s1", "s1", "s1"],
            "pos": [1, 2, 3],
            "label": ["A", "A", "B"],
            "meta": ["x", "x", "x"],
        }
    )
    collapsed = _prepare(
        repeated,
        duration_col=None,
        repeated_state_policy="collapse",
        metadata_cols=["meta"],
    )
    assert collapsed.data is not None
    assert collapsed.prepared_n_rows == 2


def test_prepare_reserved_collision_and_unknown_error_policy_paths():
    collision = _base().copy()
    collision["state"] = "extra"
    with pytest.raises(ValidationError, match="reserved canonical names"):
        _prepare(collision)

    unknown = _base().copy()
    prepared = _prepare(
        unknown,
        expected_states=["A"],
        unknown_state_policy="error",
    )
    assert prepared.status == "fail"
    assert prepared.data is None
    assert "unknown_state_disallowed" in set(prepared.audit.issue_code)
