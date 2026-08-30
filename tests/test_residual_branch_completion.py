from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from gp3sequencespy import inference, time_models


class _FixedRNG:
    def __init__(self):
        self._values = iter([0.9, 0.1])

    def random(self):
        return next(self._values)


def test_paired_permutation_non_swap_then_swap_loop_back_branch():
    design = inference.SequenceComparisonDesign(
        group_col="group",
        unit_col="unit",
        design="paired_randomized",
        pair_col="pair",
        cluster_col=None,
        interpretation="randomization-based",
    )
    unit = pd.DataFrame(
        {
            "unit": ["u1", "u2", "u3", "u4"],
            "group": ["A", "B", "A", "B"],
            "pair": ["p1", "p1", "p2", "p2"],
        }
    )
    observed = inference._permute(unit, design, ["A", "B"], _FixedRNG())
    assert observed.tolist() == ["A", "B", "B", "A"]


def test_parametric_table_without_per_term_indices():
    formula = SimpleNamespace(
        coef_names=["a", "b"],
        coef_idx_per_term=None,
        get_linear_term_idx=lambda: [0, 1],
    )
    model = SimpleNamespace(
        design_info=formula,
        model=SimpleNamespace(coef=np.array([0.1, 0.2])),
    )
    table = time_models._parametric_table(model)
    assert table.empty
    assert table.columns.tolist() == ["term", "coefficient"]


def test_motif_counter_membership_defensive_branch(monkeypatch):
    import gp3sequencespy as g
    from gp3sequencespy import motifs

    original_contains = pd.DataFrame.__contains__

    def selective_contains(self, key):
        if key == "n_states" and "n_candidate_occurrences" in self.columns:
            return False
        return original_contains(self, key)

    monkeypatch.setattr(motifs.pd.DataFrame, "__contains__", selective_contains)
    frame = pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s1"],
            "sequence_order": [1, 2, 3],
            "state": ["A", "B", "A"],
        }
    )
    result = g.extract_sequence_ngrams(
        frame,
        "sequence_id",
        "sequence_order",
        "state",
        min_length=2,
        max_length=2,
    )
    assert len(result.sequences) == 1
