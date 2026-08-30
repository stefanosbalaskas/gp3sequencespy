from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import _advanced as adv
from gp3sequencespy._exceptions import ValidationError
from gp3sequencespy._types import PrepareResult


def _base() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s2", "s2"],
            "sequence_order": [1, 2, 1, 2],
            "state": ["A", "B", "B", "A"],
            "meta": ["x", "x", "y", "y"],
            "meta2": ["u", "u", "v", "v"],
        }
    )


def test_match_cols_and_adv_data_validation_paths():
    data = _base()
    with pytest.raises(ValidationError, match="unique, non-missing"):
        adv.match_cols(data, None, "columns", allow_none=False)
    with pytest.raises(ValidationError, match="missing-state policy"):
        adv.adv_data(data, missing_state_policy="bad")
    with pytest.raises(ValidationError, match="missing_state_label"):
        adv.adv_data(data, missing_state_policy="state", missing_state_label="")

    prepared = PrepareResult(
        data, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "ok", 4, 4, ["A", "B"]
    )
    assert adv.adv_data(prepared)["sequence_ids"] == ["s1", "s2"]
    wrapped = SimpleNamespace(data=data)
    assert adv.adv_data(wrapped)["sequence_ids"] == ["s1", "s2"]
    with pytest.raises(ValidationError, match="data frame"):
        adv.adv_data(object())

    with pytest.raises(ValidationError, match="Missing required"):
        adv.adv_data(data.drop(columns="state"))
    with pytest.raises(ValidationError, match="at least one"):
        adv.adv_data(data.iloc[0:0])

    duplicate_cols = data.copy()
    duplicate_cols.columns = ["sequence_id", "sequence_order", "state", "meta", "state"]
    with pytest.raises(ValidationError, match="duplicated column names"):
        adv.adv_data(duplicate_cols)

    atomic = data.astype(object).copy()
    atomic.at[0, "sequence_id"] = ["s1"]
    with pytest.raises(ValidationError, match="atomic vectors"):
        adv.adv_data(atomic)

    bad_order = data.copy()
    bad_order["sequence_order"] = ["1", "2", "1", "2"]
    with pytest.raises(ValidationError, match="finite, non-missing numeric"):
        adv.adv_data(bad_order)

    blank_id = data.copy()
    blank_id.loc[0, "sequence_id"] = " "
    with pytest.raises(ValidationError, match="identifiers must not"):
        adv.adv_data(blank_id)


def test_adv_data_missing_state_duplicate_and_metadata_paths():
    data = _base()
    missing = data.copy()
    missing.loc[0, "state"] = None
    stated = adv.adv_data(missing, missing_state_policy="state", missing_state_label="MISSING")
    assert "MISSING" in stated["state_levels"]

    all_missing = data.copy()
    all_missing["state"] = None
    with pytest.raises(ValidationError, match="No sequence rows remain"):
        adv.adv_data(all_missing, missing_state_policy="drop")

    dup = data.copy()
    dup.loc[1, "sequence_order"] = 1
    with pytest.raises(ValidationError, match="Duplicated sequence positions"):
        adv.adv_data(dup)

    varying = data.copy()
    varying.loc[1, "meta"] = "changed"
    with pytest.raises(ValidationError, match="Metadata vary"):
        adv.adv_data(varying, metadata_cols=["meta"])


def test_group_state_edit_and_distance_validation_paths():
    data = _base()
    key = adv.group_key(data, ["meta", "meta2"])
    assert key.str.contains("\x1d", regex=False).all()

    with pytest.raises(ValidationError, match="state_levels"):
        adv.state_order(["A", "B"], ["A", ""])

    sm = np.array([[0.0, 2.0], [2.0, 0.0]])
    assert adv.edit_distance(["A"], ["B"], substitution_matrix=sm, state_labels=["A", "B"]) == 2.0

    with pytest.raises(ValidationError, match="at least one"):
        adv.validate_distance_matrix(np.empty((0, 0)))

    duplicate_labels = SimpleNamespace(matrix=np.zeros((2, 2)), labels=["s1", "s1"])
    with pytest.raises(ValidationError, match="unique sequence identifiers"):
        adv.validate_distance_matrix(duplicate_labels)
