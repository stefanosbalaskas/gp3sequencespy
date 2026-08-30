from __future__ import annotations

import pandas as pd
import pytest

from gp3sequencespy import multichannel_hmm
from gp3sequencespy._exceptions import ValidationError


def _data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s2", "s2"],
            "sequence_order": [1, 2, 1, 2],
            "gaze": ["left", "right", "right", "left"],
            "event": ["view", "click", "click", "view"],
        }
    )


def test_multichannel_input_rejects_invalid_channel_collections():
    data = _data()
    with pytest.raises(ValidationError, match="at least two unique channel names"):
        multichannel_hmm._input(data, "sequence_id", "sequence_order", ["gaze"])
    with pytest.raises(ValidationError, match="at least two unique channel names"):
        multichannel_hmm._input(data, "sequence_id", "sequence_order", ["gaze", "gaze"])


def test_multichannel_input_accepts_positional_symbol_levels():
    parsed = multichannel_hmm._input(
        _data(),
        "sequence_id",
        "sequence_order",
        ["gaze", "event"],
        symbol_levels=[["right", "left"], ["click", "view"]],
    )
    assert parsed["symbols"] == {
        "gaze": ["right", "left"],
        "event": ["click", "view"],
    }
