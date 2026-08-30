from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy import covariate_hmm
from gp3sequencespy._exceptions import ValidationError


def _data() -> pd.DataFrame:
    rows = []
    paths = {
        "s1": ("A", ["A", "B", "A", "B"], 0.0),
        "s2": ("B", ["B", "A", "B", "A"], 1.0),
        "s3": ("A", ["A", "A", "B", "B"], -1.0),
    }
    for sid, (_, states, initial_x) in paths.items():
        for order, state in enumerate(states, 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": order,
                    "state": state,
                    "initial_x": initial_x,
                    "transition_x": float(order - 1),
                }
            )
    return pd.DataFrame(rows)


def _fit(**kwargs):
    defaults = dict(
        data=_data(),
        n_states=2,
        initial_covariate_cols=["initial_x"],
        transition_covariate_cols=["transition_x"],
        max_iter=3,
        inner_maxit=10,
        tolerance=1.0,
        seed=9,
    )
    defaults.update(kwargs)
    return g.fit_covariate_sequence_hmm(**defaults)


def test_numeric_matrix_empty_missing_and_invalid_covariates():
    data = _data()
    matrix, center, scale, cols = covariate_hmm._numeric_matrix(data, [])
    assert matrix.shape == (len(data), 1)
    assert center.empty and scale.empty and cols == []

    with pytest.raises(ValidationError, match="Missing covariate"):
        covariate_hmm._numeric_matrix(data, ["missing"])

    bad = data.copy()
    bad["transition_x"] = "bad"
    with pytest.raises(ValidationError, match="finite, non-missing numeric"):
        covariate_hmm._numeric_matrix(bad, ["transition_x"])


def test_covariate_input_wrapper_symbol_and_sequence_guards():
    data = _data()
    wrapped = SimpleNamespace(data=data)
    parsed = covariate_hmm._input(
        wrapped,
        "sequence_id",
        "sequence_order",
        "state",
        ["initial_x"],
        ["transition_x"],
    )
    assert parsed["sequence_ids"] == ["s1", "s2", "s3"]

    with pytest.raises(ValidationError, match="data frame"):
        covariate_hmm._input(object(), "sequence_id", "sequence_order", "state", [], [])
    with pytest.raises(ValidationError, match="Missing covariate"):
        covariate_hmm._input(
            data,
            "sequence_id",
            "sequence_order",
            "state",
            ["missing"],
            [],
        )
    with pytest.raises(ValidationError, match="unique non-missing symbols"):
        covariate_hmm._input(
            data,
            "sequence_id",
            "sequence_order",
            "state",
            [],
            [],
            symbol_levels=["A", "A"],
        )
    with pytest.raises(ValidationError, match="does not cover"):
        covariate_hmm._input(
            data,
            "sequence_id",
            "sequence_order",
            "state",
            [],
            [],
            symbol_levels=["A"],
        )

    varying = data.copy()
    varying.loc[varying.sequence_id == "s1", "initial_x"] = [0.0, 1.0, 0.0, 0.0]
    with pytest.raises(ValidationError, match="must remain constant"):
        covariate_hmm._input(
            varying,
            "sequence_id",
            "sequence_order",
            "state",
            ["initial_x"],
            ["transition_x"],
        )

    singleton = data.groupby("sequence_id", as_index=False).first()
    singleton["sequence_order"] = 1
    with pytest.raises(ValidationError, match="At least one transition"):
        covariate_hmm._input(
            singleton,
            "sequence_id",
            "sequence_order",
            "state",
            ["initial_x"],
            ["transition_x"],
        )


def test_covariate_fit_argument_emission_and_convergence_paths():
    with pytest.raises(ValidationError, match="initial_covariate_cols"):
        g.fit_covariate_sequence_hmm(
            _data(), 2, initial_covariate_cols=["initial_x", "initial_x"], max_iter=1
        )
    with pytest.raises(ValidationError, match="transition_covariate_cols"):
        g.fit_covariate_sequence_hmm(
            _data(), 2, transition_covariate_cols=["transition_x", "transition_x"], max_iter=1
        )
    with pytest.raises(ValidationError, match="state_names"):
        _fit(state_names=["same", "same"], max_iter=1)
    with pytest.raises(ValidationError, match="emission_probs"):
        _fit(emission_probs=np.ones((2, 1)), max_iter=1)

    fitted = _fit(keep_posteriors=True)
    assert fitted.converged is True
    assert fitted.posteriors is not None
    assert len(fitted.posteriors) == 3

    one_iteration = _fit(max_iter=1, tolerance=0.0)
    assert one_iteration.iterations == 1
    assert one_iteration.converged is False


def test_covariate_prediction_decode_external_and_summary_guards():
    model = _fit()
    with pytest.raises(ValidationError, match="fit_covariate_sequence_hmm"):
        g.predict_covariate_transition_probabilities(object(), pd.DataFrame({"x": [1]}))
    with pytest.raises(ValidationError, match="non-empty data frame"):
        g.predict_covariate_transition_probabilities(model, pd.DataFrame())

    prediction = g.predict_covariate_transition_probabilities(
        model, pd.DataFrame({"transition_x": [0.0, 2.0]})
    )
    assert len(prediction) == 8
    assert np.allclose(prediction.groupby(["row", "from_state"]).probability.sum().to_numpy(), 1.0)

    with pytest.raises(ValidationError, match="fit_covariate_sequence_hmm"):
        g.decode_covariate_sequence_states(object())
    with pytest.raises(ValidationError, match="Invalid method"):
        g.decode_covariate_sequence_states(model, method="bad")

    external = _data().copy()
    external["sequence_id"] = external["sequence_id"].map({"s1": "x1", "s2": "x2", "s3": "x3"})
    decoded = g.decode_covariate_sequence_states(model, data=external, method="posterior")
    assert set(decoded.sequence_id) == {"x1", "x2", "x3"}
    assert decoded.decoding_method.eq("posterior").all()

    with pytest.raises(ValidationError, match="fit_covariate_sequence_hmm"):
        g.summarise_covariate_sequence_hmm(object())
    summary = g.summarise_covariate_sequence_hmm(model)
    assert {"fit", "initial_coefficients", "transition_coefficients", "emission"} <= set(summary)


def test_covariate_fit_handles_singleton_sequence_without_transition_counts():
    data = _data()
    mixed = pd.concat(
        [
            data.loc[data.sequence_id != "s3"],
            data.loc[(data.sequence_id == "s3") & (data.sequence_order == 1)],
        ],
        ignore_index=True,
    )
    model = g.fit_covariate_sequence_hmm(
        mixed,
        2,
        initial_covariate_cols=["initial_x"],
        transition_covariate_cols=["transition_x"],
        max_iter=2,
        inner_maxit=5,
        tolerance=1.0,
        seed=4,
    )
    assert "s3" in model.sequence_ids
    assert len(model.training_observations["s3"]) == 1


def test_viterbi_single_and_multi_observation_and_training_decode_paths():
    single_like = np.array([[0.9, 0.1]])
    initial = np.array([0.6, 0.4])
    single_transition = np.empty((0, 2, 2))
    single_path = covariate_hmm._viterbi(single_like, initial, single_transition)
    assert single_path.tolist() == [0]

    like = np.array([[0.9, 0.1], [0.2, 0.8], [0.7, 0.3]])
    transition = np.array(
        [
            [[0.8, 0.2], [0.3, 0.7]],
            [[0.6, 0.4], [0.2, 0.8]],
        ]
    )
    path = covariate_hmm._viterbi(like, initial, transition)
    assert path.shape == (3,)
    assert set(path.tolist()) <= {0, 1}

    model = _fit()
    decoded = g.decode_covariate_sequence_states(model, method="viterbi")
    assert set(decoded.sequence_id) == set(model.sequence_ids)
    assert decoded.decoding_method.eq("viterbi").all()
