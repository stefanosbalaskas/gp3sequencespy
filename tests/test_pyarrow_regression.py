from __future__ import annotations

import pandas as pd
import pytest

import gp3sequencespy as g


def test_prepare_sequence_data_collapse_handles_pyarrow_string_backend():
    pytest.importorskip("pyarrow")
    data = pd.DataFrame(
        {
            "id": pd.Series(["s1"] * 5, dtype="string[pyarrow]"),
            "position": [1, 2, 2, 3, 4],
            "state": pd.Series(["A", "B", "C", "C", "D"], dtype="string[pyarrow]"),
            "duration_ms": [1, 2, 3, 4, 5],
        }
    )
    prepared = g.prepare_sequence_data(
        data,
        "id",
        "position",
        "state",
        "duration_ms",
        duplicate_position_policy="last",
        repeated_state_policy="collapse",
    )
    assert prepared.status in {"pass", "review"}
    assert prepared.data is not None
    assert prepared.data["state"].astype(str).tolist() == ["A", "C", "D"]
    assert prepared.data["duration"].tolist() == [1, 7, 5]
