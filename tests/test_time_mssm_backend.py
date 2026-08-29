import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy._exceptions import ValidationError


def _time_fixture() -> pd.DataFrame:
    rows = []
    n_participants = 20
    n_time = 12
    for p in range(1, n_participants + 1):
        group = "g1" if p <= n_participants // 2 else "g2"
        participant_effect = ((p * 13) % 9 - 4) * 0.06
        for t in range(1, n_time + 1):
            x = (t - 1) / (n_time - 1)
            eta = -0.8 + 0.9 * x + 0.55 * np.sin(2 * np.pi * x) + participant_effect
            if group == "g2":
                eta += 0.35 + 0.30 * np.cos(2 * np.pi * x)
            prob = 1 / (1 + np.exp(-eta))
            threshold = ((p * 31 + t * 47 + p * t * 7) % 997 + 0.5) / 997
            rows.append(
                {
                    "participant_id": f"p{p:02d}",
                    "sequence_id": f"p{p:02d}",
                    "sequence_order": t,
                    "state": "B" if threshold < prob else "A",
                    "group": group,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def fitted_models():
    data = _time_fixture()
    state = {}
    for k in (3, 4, 5):
        state[k] = g.fit_time_varying_sequence_model(
            data,
            "group",
            "participant_id",
            target_state="B",
            k=k,
            include_random_effect=False,
        )
    transition_re = g.fit_time_varying_sequence_model(
        data,
        "group",
        "participant_id",
        outcome="transition",
        from_state="A",
        to_state="B",
        k=5,
        include_random_effect=True,
    )
    return data, state, transition_re


def test_mssm_time_backend_k3_contract(fitted_models):
    _, state, _ = fitted_models
    fit = state[3]
    assert fit.backend == "mssm"
    assert fit.k == 3
    assert fit.spline_degree == 2
    pred = g.predict_time_varying_sequence_model(fit, time=[1, 6, 12])
    assert len(pred) == 6
    assert pred.estimate.between(0, 1).all()


def test_mssm_time_backend_k4_contract(fitted_models):
    _, state, _ = fitted_models
    fit = state[4]
    assert fit.k == 4
    assert fit.spline_degree == 3
    pred = g.predict_time_varying_sequence_model(fit, time=[1, 6, 12])
    assert len(pred) == 6
    assert np.isfinite(pred[["estimate", "lower", "upper"]].to_numpy()).all()


def test_mssm_time_backend_k5_contract(fitted_models):
    _, state, _ = fitted_models
    fit = state[5]
    assert fit.k == 5
    assert fit.spline_degree == 3
    assert tuple(fit.population_terms) == (0, 1, 2)
    assert fit.design_columns


def test_mssm_transition_random_effect_population_prediction_and_extrapolation(fitted_models):
    _, _, fit = fitted_models
    assert fit.include_random_effect is True
    assert fit.time_range[1] == 11.0
    pred = g.predict_time_varying_sequence_model(
        fit,
        time=[11.0, 12.0],
        groups=["g1"],
    )
    assert pred.time.tolist() == [11.0, 12.0]
    assert pred.estimate.between(0, 1).all()
    assert np.isfinite(pred[["estimate", "lower", "upper"]].to_numpy()).all()


def test_mssm_time_summary_is_auditable(fitted_models):
    _, state, transition_re = fitted_models
    summary = g.summarise_time_varying_sequence_model(state[3])
    metadata = summary["metadata"].iloc[0]
    assert metadata["backend"] == "mssm"
    assert metadata["backend_solver"] == "QR"
    assert metadata["k"] == 3
    assert np.isfinite(float(metadata["edf"]))
    assert {"term", "coefficient"} <= set(summary["parametric_terms"].columns)
    assert {"term", "edf"} <= set(summary["smooth_terms"].columns)

    transition_summary = g.summarise_time_varying_sequence_model(transition_re)
    assert "s(participant)" in set(transition_summary["smooth_terms"]["term"])
    assert isinstance(transition_summary["converged"], bool)


def test_mssm_time_backend_rejects_unverified_non_reml_method():
    data = _time_fixture()
    with pytest.raises(ValidationError, match="supports `method='REML'` only"):
        g.fit_time_varying_sequence_model(
            data,
            "group",
            "participant_id",
            target_state="B",
            method="ML",
            include_random_effect=False,
        )
