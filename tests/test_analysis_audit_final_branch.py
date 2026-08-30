from __future__ import annotations

import pandas as pd

from gp3sequencespy import analysis_audit


def test_dataframe_non_mapping_settings_falls_back_to_object_attributes():
    frame = pd.DataFrame({"x": [1]})
    frame.attrs["settings"] = "not-a-mapping"
    assert analysis_audit._settings(frame) == {}
