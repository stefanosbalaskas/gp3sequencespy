import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.october_2026.smoothing_preservation import (  # noqa: E402
    audit_smoothing_event_preservation,
)


def test_smoothing_erases_brief_reference_event():
    d = pd.DataFrame(
        {
            "participant_id": ["p"] * 7,
            "trial_id": ["t"] * 7,
            "sample_index": list(range(7)),
            "reference_label": ["A", "A", "A", "B", "A", "A", "A"],
            "raw_label": ["A", "A", "A", "B", "A", "A", "A"],
            "smoothed_label": ["A"] * 7,
        }
    )
    x = audit_smoothing_event_preservation(d, brief_event_max_samples=1)
    assert x["brief_event_raw_retention"] == pytest.approx(1)
    assert x["brief_event_smoothed_retention"] == pytest.approx(0)
    assert x["trial_metrics"].iloc[0].smoothed_sample_error == pytest.approx(1 / 7)


def test_smoothing_duplicate_index_rejected():
    d = pd.DataFrame(
        {
            "participant_id": ["p"] * 3,
            "trial_id": ["t"] * 3,
            "sample_index": [0, 0, 1],
            "reference_label": ["A", "A", "B"],
            "raw_label": ["A", "A", "B"],
            "smoothed_label": ["A", "A", "B"],
        }
    )
    with pytest.raises(ValueError, match="duplicate order"):
        audit_smoothing_event_preservation(d)
