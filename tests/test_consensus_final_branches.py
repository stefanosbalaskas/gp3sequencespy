from __future__ import annotations

import pandas as pd
import pytest

from gp3sequencespy import consensus
from gp3sequencespy._exceptions import ValidationError


def _consensus() -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s2", "s2"],
            "sequence_order": [1, 2, 1, 2],
            "state": ["A", "B", "A", "C"],
        }
    )
    return consensus.create_consensus_sequence(data)


def test_consensus_final_guard_and_format_branches():
    with pytest.raises(ValidationError, match="create_consensus_sequence"):
        consensus._check_consensus(pd.DataFrame())

    value = _consensus()
    with pytest.raises(ValidationError, match="Invalid `by`"):
        consensus.summarise_consensus_agreement(value, by="bad")

    ordered_only = consensus.format_consensus_sequence(
        value,
        include_order=True,
        include_agreement=False,
    )
    assert ordered_only.path.str.contains(":", regex=False).all()
    assert not ordered_only.path.str.contains("[", regex=False).any()
