import pandas as pd
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.october_2026.sequence_transfer import sequence_transfer_audit  # noqa: E402


def _demo():
    rows = []
    for dataset, patterns in [
        ("reading", [["A", "B", "A"], ["A", "B", "A"]]),
        ("search", [["A", "A", "B"], ["A", "A", "B"]]),
    ]:
        for participant, pattern in enumerate(patterns):
            for step, state in enumerate(pattern):
                rows.append((dataset, f"{dataset}-{participant}", "trial", step, state))
    return pd.DataFrame(rows, columns=[
        "dataset_id", "participant_id", "sequence_id", "step", "state"])


def test_transfer_reveals_transition_structure():
    result = sequence_transfer_audit(_demo())
    comparison = result["domain_comparisons"].iloc[0]
    assert 0 <= comparison.token_js_bits <= 1
    assert comparison.transition_js_bits > 0
    assert (result["heldout_prediction"].target_holdout_participants == 1).all()
    assert result["heldout_prediction"].out_of_domain_nll.notna().all()
    assert result["heldout_prediction"].equal_source_mixture_nll.notna().all()
    assert result["heldout_prediction"].target_transition_entropy_bits.notna().all()
    assert len(result["source_specific_prediction"]) == 2


def test_refuses_insufficient_independent_units():
    d = _demo()
    d = d[~((d.dataset_id == "search") & (d.participant_id == "search-1"))]
    with pytest.raises(ValueError, match="at least two participants"):
        sequence_transfer_audit(d)


def test_duplicate_step_is_rejected():
    d = _demo()
    d = pd.concat([d, d.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        sequence_transfer_audit(d)
