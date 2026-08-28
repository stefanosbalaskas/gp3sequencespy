from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CsvContract:
    key_columns: tuple[str, ...]
    numeric_tolerance: float = 1e-10


CONTRACTS = {
    "state_summary_overall": CsvContract(("state",)),
    "transition_summary_overall": CsvContract(("from_state", "to_state")),
    "formatted_paths": CsvContract(("sequence_id",)),
    "motif_summary_overall": CsvContract(("motif_key",)),
    "consensus": CsvContract(("sequence_order",)),
    "distance_levenshtein": CsvContract(("sequence_id",)),
}


def load_canonical(path: Path, contract: CsvContract) -> pd.DataFrame:
    frame = pd.read_csv(path, keep_default_na=False)
    missing = [c for c in contract.key_columns if c not in frame.columns]
    if missing:
        raise AssertionError(f"{path}: missing key columns {missing}")
    return frame.sort_values(list(contract.key_columns), kind="stable").reset_index(drop=True)


def compare_frames(left: pd.DataFrame, right: pd.DataFrame, tolerance: float) -> list[str]:
    errors: list[str] = []
    if list(left.columns) != list(right.columns):
        return [f"column mismatch: R={list(left.columns)} Python={list(right.columns)}"]
    if len(left) != len(right):
        return [f"row-count mismatch: R={len(left)} Python={len(right)}"]
    for column in left.columns:
        lcol, rcol = left[column], right[column]
        lnum = pd.to_numeric(lcol, errors="coerce")
        rnum = pd.to_numeric(rcol, errors="coerce")
        numeric_mask = lnum.notna() & rnum.notna()
        nonblank = (lcol.astype(str) != "") | (rcol.astype(str) != "")
        if numeric_mask.sum() == nonblank.sum() and nonblank.any():
            if not np.allclose(lnum[numeric_mask], rnum[numeric_mask], atol=tolerance, rtol=tolerance):
                errors.append(f"numeric mismatch in {column}")
        else:
            if not lcol.astype(str).equals(rcol.astype(str)):
                errors.append(f"value mismatch in {column}")
    return errors
