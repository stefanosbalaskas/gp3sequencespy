from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import hmm
from gp3sequencespy._exceptions import ModelFitError, ValidationError


def _data(n_sequences: int = 4) -> pd.DataFrame:
    paths = [
        ["A", "B", "A", "B"],
        ["A", "A", "B", "B"],
        ["B", "A", "B", "A"],
        ["B", "B", "A", "A"],
    ]
    rows = []
    for i in range(n_sequences):
        sid = f"s{i + 1}"
        for order, state in enumerate(paths[i % len(paths)], 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": order,
                    "state": state,
                }
            )
    return pd.DataFrame(rows)


def _fit_single(**kwargs):
    defaults = dict(n_states=2, max_iter=3, tolerance=1.0, seed=11)
    defaults.update(kwargs)
    return hmm.fit_sequence_hmm(_data(), **defaults)


def _fit_mixture(**kwargs):
    defaults = dict(
        n_components=2,
        n_states=[2, 2],
        max_iter=3,
        inner_initial_iter=1,
        tolerance=1.0,
        seed=17,
    )
    defaults.update(kwargs)
    return hmm.fit_sequence_hmm_mixture(_data(), **defaults)


def test_hmm_initialisation_sufficient_statistics_and_single_fit_guards():
    with pytest.raises(ValidationError, match="emission_probs"):
        hmm._init(2, 2, 1, emission_probs=np.ones((2, 1)))

    params = hmm._init(2, 2, 2)
    with pytest.raises(ValidationError, match="weights"):
        hmm._sufficient([np.array([0], dtype=int)], params, weights=np.array([-1.0]))

    sufficient = hmm._sufficient([np.array([0], dtype=int)], params, pseudocount=0)
    assert sufficient["transition"].shape == (2, 2)
    assert np.allclose(sufficient["transition"], 0.0)

    with pytest.raises(ValidationError, match="state_names"):
        hmm.fit_sequence_hmm(_data(), 2, state_names=["same", "same"], max_iter=1)

    fitted = _fit_single(keep_posteriors=True)
    assert fitted.converged is True
    assert fitted.posteriors is not None
    assert len(fitted.posteriors) == len(fitted.sequence_ids)


def test_hmm_mixture_shape_component_and_normalisation_guards(monkeypatch):
    with pytest.raises(ValidationError, match="one value per component"):
        hmm.fit_sequence_hmm_mixture(_data(), 2, [2], max_iter=1, inner_initial_iter=1)

    with pytest.raises(ValidationError, match="More components than sequences"):
        hmm.fit_sequence_hmm_mixture(_data(2), 3, 2, max_iter=1, inner_initial_iter=1)

    monkeypatch.setattr(
        hmm,
        "_loglik",
        lambda encoded, params: np.full(len(encoded), np.nan),
    )
    with pytest.raises(ModelFitError, match="responsibilities"):
        hmm.fit_sequence_hmm_mixture(_data(), 2, 2, max_iter=1, inner_initial_iter=1, seed=3)


def test_hmm_mixture_fit_decode_external_and_summary_paths():
    mixture = _fit_mixture()
    assert mixture.converged is True
    assert mixture.n_components == 2

    with pytest.raises(ValidationError, match="decoding method"):
        hmm.decode_sequence_states(mixture, method="bad")
    with pytest.raises(ValidationError, match="Unsupported HMM"):
        hmm.decode_sequence_states(object())

    explicit = hmm.decode_sequence_states(mixture, component=1, method="posterior")
    assert explicit.component.eq(1).all()
    assert explicit.decoding_method.eq("posterior").all()

    external = _data().copy()
    external["sequence_id"] = external["sequence_id"].map({f"s{i}": f"x{i}" for i in range(1, 5)})
    assigned = hmm.decode_sequence_states(mixture, data=external, method="viterbi")
    assert set(assigned.sequence_id) == {"x1", "x2", "x3", "x4"}
    assert assigned.component.between(1, 2).all()

    summary = hmm.summarise_sequence_hmm(mixture)
    assert summary["mixture"].component.tolist() == [1, 2]
    assert len(summary["initial"]) == 4
    assert len(summary["transition"]) == 8
    assert len(summary["emission"]) == 8
    assert summary["responsibilities"] is mixture.responsibilities

    with pytest.raises(ValidationError, match="Unsupported HMM"):
        hmm.summarise_sequence_hmm(object())


def test_hmm_compare_argument_validation_and_mixed_label_path():
    model = _fit_single()
    with pytest.raises(ValidationError, match="at least two"):
        hmm.compare_sequence_hmms(model)
    with pytest.raises(ValidationError, match="All objects"):
        hmm.compare_sequence_hmms(model, object())

    compared = hmm.compare_sequence_hmms(model, duplicate=model)
    assert set(compared.model) == {"model_1", "duplicate"}
    assert np.allclose(compared.delta_aic, 0.0)
    assert np.allclose(compared.delta_bic, 0.0)
