from __future__ import annotations

from types import SimpleNamespace

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from gp3sequencespy import time_models
from gp3sequencespy._exceptions import ModelFitError, ValidationError


def _valid_long() -> pd.DataFrame:
    rows = []
    for sid, group, participant, states in [
        ("s1", "g1", "p1", ["A", "B", "A", "B"]),
        ("s2", "g2", "p2", ["B", "A", "B", "A"]),
    ]:
        for order, state in enumerate(states, 1):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": order,
                    "state": state,
                    "time": float(order),
                    "group": group,
                    "participant": participant,
                }
            )
    return pd.DataFrame(rows)


def _model(backend_model=None, *, include_random_effect=True) -> time_models.TimeVaryingSequenceModel:
    if backend_model is None:
        backend_model = SimpleNamespace(
            coef=np.array([0.1, 0.2]),
            term_edf=np.array([1.1, 1.2, 0.5]),
            mus=[np.array([0.25, 0.75, 0.25, 0.75])],
            edf=2.8,
            info=SimpleNamespace(code=0, eps=0.0, lambda_updates=2),
            get_reml=lambda: 1.5,
        )
    formula = SimpleNamespace(
        coef_names=["Intercept", "group"],
        coef_idx_per_term=[np.array([0]), np.array([1])],
        get_linear_term_idx=lambda: [0, 1],
    )
    md = pd.DataFrame(
        {
            "outcome": [0, 1, 0, 1],
            "time": [1.0, 2.0, 3.0, 4.0],
            "group": ["g1", "g1", "g2", "g2"],
            "participant": ["p1", "p1", "p2", "p2"],
        }
    )
    return time_models.TimeVaryingSequenceModel(
        model=backend_model,
        model_data=md,
        outcome="state",
        target_state="A",
        from_state=None,
        to_state=None,
        group_levels=["g1", "g2"],
        participant_levels=["p1", "p2"],
        time_range=(1.0, 4.0),
        k=4,
        method="REML",
        include_random_effect=include_random_effect,
        columns={
            "group": "group",
            "participant": "participant",
            "sequence_id": "sequence_id",
            "order": "sequence_order",
            "state": "state",
            "time": "time",
        },
        design_info=formula,
        design_columns=["Intercept", "group"],
        backend="mssm",
        population_terms=(0, 1, 2),
        spline_degree=3,
    )


def test_make_model_data_validation_and_transition_paths():
    data = _valid_long()
    with pytest.raises(ValidationError, match="Missing time column"):
        time_models._make_model_data(
            data.drop(columns="time"),
            "group",
            "participant",
            "sequence_id",
            "sequence_order",
            "state",
            "time",
            "state",
            "A",
            None,
            None,
        )

    bad_time = data.copy()
    bad_time["time"] = bad_time["time"].astype(str)
    with pytest.raises(ValidationError, match="time column"):
        time_models._make_model_data(
            bad_time,
            "group",
            "participant",
            "sequence_id",
            "sequence_order",
            "state",
            "time",
            "state",
            "A",
            None,
            None,
        )

    blank_group = data.copy()
    blank_group.loc[blank_group.sequence_id == "s1", "group"] = ""
    with pytest.raises(ValidationError, match="Group values"):
        time_models._make_model_data(
            blank_group,
            "group",
            "participant",
            "sequence_id",
            "sequence_order",
            "state",
            "time",
            "state",
            "A",
            None,
            None,
        )

    blank_participant = data.copy()
    blank_participant.loc[blank_participant.sequence_id == "s1", "participant"] = ""
    with pytest.raises(ValidationError, match="Participant identifiers"):
        time_models._make_model_data(
            blank_participant,
            "group",
            "participant",
            "sequence_id",
            "sequence_order",
            "state",
            "time",
            "state",
            "A",
            None,
            None,
        )

    md, groups, parts = time_models._make_model_data(
        data,
        "group",
        "participant",
        "sequence_id",
        "sequence_order",
        "state",
        "time",
        "transition",
        None,
        "A",
        "B",
    )
    assert len(md) == 6
    assert groups == ["g1", "g2"]
    assert parts == ["p1", "p2"]


def test_make_model_data_postconstruction_guards(monkeypatch):
    def run(frame, ids, outcome="state"):
        monkeypatch.setattr(
            time_models,
            "adv_data",
            lambda *args, **kwargs: {
                "data": frame,
                "sequence_ids": ids,
            },
        )
        return time_models._make_model_data(
            frame,
            "group",
            "participant",
            "sequence_id",
            "sequence_order",
            "state",
            "time",
            outcome,
            "A",
            "A",
            "B",
        )

    no_transitions = pd.DataFrame(
        {
            "sequence_id": ["s1", "s2"],
            "sequence_order": [1, 1],
            "state": ["A", "B"],
            "time": [1.0, 2.0],
            "group": ["g1", "g2"],
            "participant": ["p1", "p2"],
        }
    )
    with pytest.raises(ValidationError, match="No transitions"):
        run(no_transitions, ["s1", "s2"], "transition")

    one_group = _valid_long().copy()
    one_group["group"] = "g1"
    with pytest.raises(ValidationError, match="At least two groups"):
        run(one_group, ["s1", "s2"])

    few_times = _valid_long().copy()
    few_times["time"] = [1, 2, 3, 1, 2, 3, 1, 2]
    with pytest.raises(ValidationError, match="four distinct"):
        run(few_times, ["s1", "s2"])

    no_variation = _valid_long().copy()
    no_variation["state"] = "A"
    with pytest.raises(ValidationError, match="no variation"):
        run(no_variation, ["s1", "s2"])


def test_method_convergence_and_public_fit_argument_guards():
    with pytest.raises(ValidationError, match="non-empty string"):
        time_models._validate_method("")
    with pytest.raises(ValidationError, match="REML"):
        time_models._validate_method("GCV")
    assert time_models._validate_method(" reml ") == "reml"

    assert time_models._converged(SimpleNamespace()) is True
    assert time_models._converged(SimpleNamespace(info=SimpleNamespace(code=0, eps=None))) is True
    assert time_models._converged(SimpleNamespace(info=SimpleNamespace(code=1, eps=0.0))) is False

    data = _valid_long()
    with pytest.raises(ValidationError, match="Invalid outcome"):
        time_models.fit_time_varying_sequence_model(data, "group", "participant", outcome="bad")
    with pytest.raises(ValidationError, match="group_col"):
        time_models.fit_time_varying_sequence_model(data, "", "participant", target_state="A")
    with pytest.raises(ValidationError, match="participant_id_col"):
        time_models.fit_time_varying_sequence_model(data, "group", "", target_state="A")
    with pytest.raises(ValidationError, match="time_col"):
        time_models.fit_time_varying_sequence_model(
            data, "group", "participant", time_col="", target_state="A"
        )
    with pytest.raises(ValidationError, match="target_state"):
        time_models.fit_time_varying_sequence_model(data, "group", "participant")
    with pytest.raises(ValidationError, match="from_state"):
        time_models.fit_time_varying_sequence_model(
            data, "group", "participant", outcome="transition", from_state="A", to_state=""
        )


def test_fit_wraps_backend_failures(monkeypatch):
    data = _valid_long()

    class BrokenFormula:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("formula boom")

    monkeypatch.setattr(
        time_models,
        "_require_time_backend",
        lambda: (
            BrokenFormula,
            object,
            lambda: object(),
            lambda *args, **kwargs: object(),
            lambda *args, **kwargs: object(),
            lambda *args, **kwargs: object(),
            lambda *args, **kwargs: object(),
            lambda *args, **kwargs: object(),
        ),
    )
    with pytest.raises(ValidationError, match="fitting failed"):
        time_models.fit_time_varying_sequence_model(
            data,
            "group",
            "participant",
            time_col="time",
            target_state="A",
            include_random_effect=False,
        )


def test_prediction_guards_failure_uncertainty_and_success():
    with pytest.raises(ValidationError, match="fit_time_varying"):
        time_models.predict_time_varying_sequence_model(object())

    model = _model()
    with pytest.raises(ValidationError, match="time"):
        time_models.predict_time_varying_sequence_model(model, time=[1.0, np.nan])
    with pytest.raises(ValidationError, match="Unknown groups"):
        time_models.predict_time_varying_sequence_model(model, groups=["missing"])

    broken = _model(SimpleNamespace(predict=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))))
    with pytest.raises(ValidationError, match="Prediction construction failed"):
        time_models.predict_time_varying_sequence_model(broken, time=[1.0])

    no_uncertainty = _model(
        SimpleNamespace(predict=lambda *args, **kwargs: (np.array([0.0]), None, None))
    )
    with pytest.raises(ModelFitError, match="uncertainty"):
        time_models.predict_time_varying_sequence_model(no_uncertainty, time=[1.0], groups=["g1"])

    class Predictor:
        def predict(self, terms, grid, alpha, ci):
            n = len(grid)
            return np.zeros(n), None, np.repeat(0.5, n)

    successful = _model(Predictor())
    pred = time_models.predict_time_varying_sequence_model(
        successful, time=[2.0, 1.0, 1.0], groups=["g2", "g1"]
    )
    assert pred.shape[0] == 4
    assert set(pred.group) == {"g1", "g2"}
    assert pred.estimate.eq(0.5).all()


def test_summary_tables_and_plot_branches():
    with pytest.raises(ValidationError, match="fit_time_varying"):
        time_models.summarise_time_varying_sequence_model(object())

    fallback_model = _model(
        SimpleNamespace(
            coef=np.array([0.1, 0.2, 0.3]),
            term_edf=np.array([1.0]),
            mus=None,
            edf=1.0,
            info=None,
            get_reml=lambda: (_ for _ in ()).throw(RuntimeError("no score")),
        ),
        include_random_effect=False,
    )
    fallback_model.design_info = SimpleNamespace(
        coef_names=["only-one-name"],
        coef_idx_per_term=[np.array([0, 2])],
        get_linear_term_idx=lambda: [0],
    )
    parametric = time_models._parametric_table(fallback_model)
    assert parametric.term.tolist() == ["coefficient_0", "coefficient_2"]
    smooth = time_models._smooth_table(fallback_model)
    assert smooth.term.tolist() == ["smooth_term_1"]

    summary = time_models.summarise_time_varying_sequence_model(fallback_model)
    assert np.isnan(summary["metadata"].loc[0, "deviance_explained"])
    assert np.isnan(summary["metadata"].loc[0, "reml_score"])
    assert summary["converged"] is True

    class Predictor:
        coef = np.array([])
        term_edf = np.array([])
        mus = None
        edf = 0.0
        info = None

        @staticmethod
        def get_reml():
            return 0.0

        @staticmethod
        def predict(terms, grid, alpha, ci):
            n = len(grid)
            return np.zeros(n), None, np.repeat(0.2, n)

    plot_model = _model(Predictor())
    ax = time_models.plot_time_varying_sequence_model(
        plot_model, time=[1.0, 2.0], show_interval=False
    )
    assert len(ax.lines) == 2
    assert len(ax.gp3_data) == 4
