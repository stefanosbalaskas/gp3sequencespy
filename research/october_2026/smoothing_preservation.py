"""Research-only temporal smoothing and brief-event preservation tests."""
from __future__ import annotations

import numpy as np
import pandas as pd


def audit_smoothing_event_preservation(
    frame: pd.DataFrame,
    *,
    participant_col="participant_id",
    trial_col="trial_id",
    order_col="sample_index",
    true_col="reference_label",
    raw_col="raw_label",
    smoothed_col="smoothed_label",
    brief_event_max_samples=2,
) -> dict:
    """Compare per-sample error, reference event runs and boundary retention.

    Events are exact contiguous categorical runs on a common ordered sample
    grid. A reference event is 'preserved' if its entire span retains the
    reference label in predictions. This conservative criterion does not
    replace tolerance-based temporal event matching or clinical validation.
    """
    required=[participant_col,trial_col,order_col,true_col,raw_col,smoothed_col]
    if not set(required).issubset(frame):
        raise ValueError("missing aligned event sequence fields")
    if frame[required].isna().any().any() or frame.empty:
        raise ValueError("complete matched sample labels required")
    if brief_event_max_samples < 1:
        raise ValueError("brief-event limit must be positive")
    summary=[]
    events=[]
    for key, group in frame.groupby([participant_col,trial_col],sort=False):
        s=group.sort_values(order_col,kind="stable")
        if s[order_col].duplicated().any():
            raise ValueError("duplicate order inside participant/trial")
        y=s[true_col].astype(str).to_numpy()
        a=s[raw_col].astype(str).to_numpy()
        b=s[smoothed_col].astype(str).to_numpy()
        starts=np.r_[0,np.flatnonzero(y[1:] != y[:-1])+1]
        ends=np.r_[starts[1:],len(y)]
        for start,end in zip(starts,ends,strict=True):
            row={
                "participant_id":key[0],"trial_id":key[1],"reference_label":y[start],
                "start_sample":int(start),"duration_samples":int(end-start),
                "brief_reference_event":bool(end-start<=brief_event_max_samples),
                "raw_whole_event_preserved":bool(np.all(a[start:end]==y[start])),
                "smoothed_whole_event_preserved":bool(np.all(b[start:end]==y[start])),
            }
            events.append(row)
        summary.append({
            "participant_id":key[0],"trial_id":key[1],
            "raw_sample_error":float(np.mean(a!=y)),
            "smoothed_sample_error":float(np.mean(b!=y)),
            "raw_n_transitions":int(np.count_nonzero(a[1:]!=a[:-1])),
            "smoothed_n_transitions":int(np.count_nonzero(b[1:]!=b[:-1])),
            "reference_n_transitions":int(np.count_nonzero(y[1:]!=y[:-1])),
        })
    events_table=pd.DataFrame(events)
    brief=events_table[events_table.brief_reference_event]
    return {
        "trial_metrics":pd.DataFrame(summary),
        "reference_events":events_table,
        "brief_event_raw_retention":float(brief.raw_whole_event_preserved.mean()) if len(brief) else np.nan,
        "brief_event_smoothed_retention":float(brief.smoothed_whole_event_preserved.mean()) if len(brief) else np.nan,
        "claim_boundary":"Exact-span diagnostic, not an independent expert-referenced event reconstruction.",
    }
