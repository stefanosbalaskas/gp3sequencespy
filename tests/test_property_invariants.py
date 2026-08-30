from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gp3sequencespy import _advanced as adv
from gp3sequencespy import compute_sequence_distance


@settings(max_examples=80, deadline=None)
@given(
    st.lists(st.integers(min_value=0, max_value=4), max_size=8),
    st.lists(st.integers(min_value=0, max_value=4), max_size=8),
)
def test_edit_distance_symmetry_and_identity(a, b):
    da = adv.edit_distance(a, b, 1.0, 1.0, None, [str(i) for i in range(5)])
    db = adv.edit_distance(b, a, 1.0, 1.0, None, [str(i) for i in range(5)])
    assert da == pytest.approx(db)
    assert adv.edit_distance(a, a, 1.0, 1.0, None, [str(i) for i in range(5)]) == 0
    assert da >= 0


@settings(max_examples=80, deadline=None)
@given(
    st.lists(st.integers(min_value=0, max_value=4), max_size=10),
    st.lists(st.integers(min_value=0, max_value=4), max_size=10),
)
def test_lcs_bounds_and_symmetry(a, b):
    value = adv.lcs_length(a, b)
    assert 0 <= value <= min(len(a), len(b))
    assert value == adv.lcs_length(b, a)
    assert adv.lcs_length(a, a) == len(a)


@settings(max_examples=60, deadline=None)
@given(
    st.lists(
        st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    ),
    st.floats(min_value=0, max_value=2, allow_nan=False, allow_infinity=False),
)
def test_vector_normalise_is_probability_vector(values, pseudocount):
    out = adv.vector_normalise(np.asarray(values, dtype=float), pseudocount)
    assert np.all(np.isfinite(out))
    assert np.all(out >= 0)
    assert out.sum() == pytest.approx(1.0)


@settings(max_examples=40, deadline=None)
@given(
    st.lists(st.sampled_from(["A", "B", "C"]), min_size=1, max_size=8),
    st.lists(st.sampled_from(["A", "B", "C"]), min_size=1, max_size=8),
)
def test_public_levenshtein_distance_matrix_is_symmetric(seq1, seq2):
    rows = []
    for sid, seq in [("s1", seq1), ("s2", seq2)]:
        rows.extend(
            {"sequence_id": sid, "sequence_order": i + 1, "state": state}
            for i, state in enumerate(seq)
        )
    data = pd.DataFrame(rows)
    result = compute_sequence_distance(data, method="levenshtein")
    matrix = np.asarray(result.matrix, dtype=float)
    np.testing.assert_allclose(matrix, matrix.T)
    np.testing.assert_allclose(np.diag(matrix), 0)
    assert np.all(matrix >= 0)
