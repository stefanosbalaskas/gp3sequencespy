from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import expit

from ._advanced import adv_data, scalar_logical, scalar_number
from ._exceptions import ModelFitError, ValidationError


def _require_time_backend():
    try:
        # mssm imports its HSMM module from mssm.models and emits an informational
        # warning when the optional multiprocess package is absent. Time-varying
        # sequence GAMMs do not use that HSMM functionality.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"Multi-processing hsmm computations will require.*",
                category=UserWarning,
            )
            from mssm.models import GAMM, Binomial, Formula, f, i, lhs, ri
            from mssm.models import l as linear_term
    except ImportError as exc:
        raise ModelFitError(
            "Time-varying sequence models require the optional 'time' dependency `mssm`. "
            "Install it with `pip install gp3sequencespy[time]` or `uv sync --extra time`."
        ) from exc
    return Formula, GAMM, Binomial, f, i, linear_term, lhs, ri


@dataclass(slots=True)
class TimeVaryingSequenceModel:
    model: Any
    model_data: pd.DataFrame
    outcome: str
    target_state: str | None
    from_state: str | None
    to_state: str | None
    group_levels: list[str]
    participant_levels: list[str]
    time_range: tuple[float, float]
    k: int
    method: str
    include_random_effect: bool
    columns: dict[str, str]
    design_info: Any
    design_columns: list[str]
    backend: str
    population_terms: tuple[int, ...]
    spline_degree: int


def _make_model_data(
    data,
    group_col,
    participant_id_col,
    sequence_id_col,
    order_col,
    state_col,
    time_col,
    outcome,
    target_state,
    from_state,
    to_state,
):
    x = adv_data(
        data,
        sequence_id_col,
        order_col,
        state_col,
        metadata_cols=[group_col, participant_id_col],
        missing_state_policy="error",
    )
    w = x["data"]
    if time_col not in w.columns:
        raise ValidationError(f"Missing time column `{time_col}`.")
    if (
        not pd.api.types.is_numeric_dtype(w[time_col])
        or w[time_col].isna().any()
        or not np.isfinite(w[time_col].to_numpy(float)).all()
    ):
        raise ValidationError("The time column must contain finite, non-missing numeric values.")
    gv = w[group_col].astype("string")
    pv = w[participant_id_col].astype("string")
    if gv.isna().any() or gv.str.strip().eq("").any():
        raise ValidationError("Group values must not be missing or blank.")
    if pv.isna().any() or pv.str.strip().eq("").any():
        raise ValidationError("Participant identifiers must not be missing or blank.")

    if outcome == "state":
        md = pd.DataFrame(
            {
                "outcome": (w[state_col].astype(str) == target_state).astype(int),
                "time": w[time_col].astype(float),
                "group": gv.astype(str),
                "participant": pv.astype(str),
            }
        )
    else:
        rows = []
        for sid in x["sequence_ids"]:
            p = w.loc[w[sequence_id_col].astype(str) == sid].reset_index(drop=True)
            for j in range(len(p) - 1):
                rows.append(
                    {
                        "outcome": int(
                            str(p.loc[j, state_col]) == from_state
                            and str(p.loc[j + 1, state_col]) == to_state
                        ),
                        "time": float(p.loc[j, time_col]),
                        "group": str(p.loc[j, group_col]),
                        "participant": str(p.loc[j, participant_id_col]),
                    }
                )
        if not rows:
            raise ValidationError("No transitions are available for modelling.")
        md = pd.DataFrame(rows)

    groups = sorted(md.group.unique().tolist())
    parts = sorted(md.participant.unique().tolist())
    if len(groups) < 2:
        raise ValidationError("At least two groups are required.")
    if md.time.nunique() < 4:
        raise ValidationError("At least four distinct time values are required.")
    if md.outcome.nunique() < 2:
        raise ValidationError("The target outcome has no variation.")

    # mssm requires factor variables to have object dtype.
    md["group"] = md["group"].astype(object)
    md["participant"] = md["participant"].astype(object)
    return md, groups, parts


def _validate_method(method: Any) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValidationError("`method` must be a non-empty string.")
    requested = method.strip()
    if requested.upper() != "REML":
        raise ValidationError(
            "The Python time-model backend currently supports `method='REML'` only. "
            "The frozen R implementation passes other smoothing criteria to `mgcv::gam()`; "
            "those non-default criteria do not have a verified mssm equivalent."
        )
    return requested


def _binomial_deviance(y: np.ndarray, mu: np.ndarray) -> float:
    eps = np.finfo(float).eps
    p = np.clip(np.asarray(mu, float), eps, 1.0 - eps)
    yy = np.asarray(y, float)
    return float(-2.0 * np.sum(yy * np.log(p) + (1.0 - yy) * np.log(1.0 - p)))


def _converged(fit: Any) -> bool:
    info = getattr(fit, "info", None)
    if info is None:
        return True
    code = getattr(info, "code", 0)
    eps = getattr(info, "eps", 0)
    eps_ok = eps is None or abs(float(eps)) <= np.finfo(float).eps
    return bool(int(code) == 0 and bool(eps_ok))


def fit_time_varying_sequence_model(
    data: Any,
    group_col: str,
    participant_id_col: str,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    time_col: str | None = None,
    outcome: str = "state",
    target_state: str | None = None,
    from_state: str | None = None,
    to_state: str | None = None,
    k: int = 5,
    method: str = "REML",
    include_random_effect: bool = True,
) -> TimeVaryingSequenceModel:
    if outcome not in {"state", "transition"}:
        raise ValidationError("Invalid outcome.")
    for name, val in [("group_col", group_col), ("participant_id_col", participant_id_col)]:
        if not isinstance(val, str) or not val:
            raise ValidationError(f"`{name}` must be a non-empty string.")
    time_col = order_col if time_col is None else time_col
    if not isinstance(time_col, str) or not time_col:
        raise ValidationError("`time_col` must be a non-empty string.")
    scalar_number(k, "k", 3, integer=True)
    scalar_logical(include_random_effect, "include_random_effect")
    requested_method = _validate_method(method)

    if outcome == "state" and (not isinstance(target_state, str) or not target_state):
        raise ValidationError("`target_state` must be a non-empty string.")
    if outcome == "transition" and (
        not isinstance(from_state, str)
        or not from_state
        or not isinstance(to_state, str)
        or not to_state
    ):
        raise ValidationError("`from_state` and `to_state` must be non-empty strings.")

    md, groups, parts = _make_model_data(
        data,
        group_col,
        participant_id_col,
        sequence_id_col,
        order_col,
        state_col,
        time_col,
        outcome,
        target_state,
        from_state,
        to_state,
    )
    k_used = min(int(k), int(md.time.nunique() - 1))

    # mssm documents mgcv's identifiable k-basis convention as nk = k - 1.
    # At the minimum supported k=3, a quadratic basis is required so that the
    # B-spline knot interval remains well-defined after the identifiability
    # bookkeeping. k>=4 uses the ordinary cubic basis.
    nk = k_used - 1
    spline_degree = min(3, k_used - 1)

    Formula, GAMM, Binomial, f, i, linear_term, lhs, ri = _require_time_backend()
    terms = [
        i(),
        linear_term(["group"]),
        f(
            ["time"],
            by="group",
            nk=nk,
            basis_kwargs={"deg": spline_degree},
        ),
    ]
    if include_random_effect:
        terms.append(ri("participant"))

    try:
        formula = Formula(
            lhs("outcome"),
            terms,
            data=md,
            print_warn=False,
        )
        fit = GAMM(formula, Binomial())
        # `method` in mssm.fit selects the numerical linear-system solver.
        # QR maximizes numerical stability. Smoothing parameters are selected
        # automatically against the package's Laplace-approximate REML
        # criterion (the verified analogue of the frozen R default).
        fit.fit(method="QR", progress_bar=False, n_cores=1)
    except Exception as exc:
        raise ValidationError(f"Time-varying model fitting failed: {exc}") from exc

    design_columns = list(getattr(formula, "coef_names", None) or [])
    return TimeVaryingSequenceModel(
        fit,
        md,
        outcome,
        target_state,
        from_state,
        to_state,
        groups,
        parts,
        (float(md.time.min()), float(md.time.max())),
        k_used,
        requested_method,
        bool(include_random_effect),
        {
            "group": group_col,
            "participant": participant_id_col,
            "sequence_id": sequence_id_col,
            "order": order_col,
            "state": state_col,
            "time": time_col,
        },
        formula,
        design_columns,
        "mssm",
        (0, 1, 2),
        spline_degree,
    )


def predict_time_varying_sequence_model(
    model: TimeVaryingSequenceModel,
    time: Sequence[float] | None = None,
    groups: Sequence[str] | None = None,
    level: float = 0.95,
) -> pd.DataFrame:
    if not isinstance(model, TimeVaryingSequenceModel):
        raise ValidationError("`model` must be created by `fit_time_varying_sequence_model()`.")
    scalar_number(level, "level", 0.5, 0.999999)
    tv = np.linspace(*model.time_range, 100) if time is None else np.asarray(time, float)
    if tv.ndim != 1 or not np.isfinite(tv).all():
        raise ValidationError("`time` must contain finite numeric values.")

    gs = model.group_levels if groups is None else [str(g) for g in groups]
    if any(g not in model.group_levels for g in gs):
        raise ValidationError("Unknown groups requested for prediction.")

    rows = [
        {"time": float(t), "group": g, "participant": model.participant_levels[0]}
        for g in gs
        for t in sorted(set(tv.tolist()))
    ]
    grid = pd.DataFrame(rows)
    grid["group"] = grid["group"].astype(object)
    grid["participant"] = grid["participant"].astype(object)

    try:
        eta, _, half_width = model.model.predict(
            list(model.population_terms),
            grid,
            alpha=1.0 - float(level),
            ci=True,
        )
    except Exception as exc:
        raise ValidationError(f"Prediction construction failed: {exc}") from exc

    if half_width is None:
        raise ModelFitError("The time-model backend did not return prediction uncertainty.")

    eta = np.asarray(eta, float).reshape(-1)
    half_width = np.asarray(half_width, float).reshape(-1)
    return pd.DataFrame(
        {
            "time": grid.time.to_numpy(float),
            "group": grid.group.astype(str).to_numpy(),
            "estimate": expit(eta),
            "lower": expit(eta - half_width),
            "upper": expit(eta + half_width),
            "outcome": model.outcome,
        }
    )


def _parametric_table(model: TimeVaryingSequenceModel) -> pd.DataFrame:
    formula = model.design_info
    coef = np.asarray(getattr(model.model, "coef", np.array([])), float).reshape(-1)
    names = list(getattr(formula, "coef_names", None) or [])
    if len(names) != len(coef):
        names = [f"coefficient_{j}" for j in range(len(coef))]

    indices: list[int] = []
    per_term = getattr(formula, "coef_idx_per_term", None)
    if per_term is not None:
        for term_idx in formula.get_linear_term_idx():
            indices.extend(np.asarray(per_term[term_idx], int).reshape(-1).tolist())
    indices = sorted(set(j for j in indices if 0 <= j < len(coef)))
    return pd.DataFrame(
        {
            "term": [names[j] for j in indices],
            "coefficient": [float(coef[j]) for j in indices],
        }
    )


def _smooth_table(model: TimeVaryingSequenceModel) -> pd.DataFrame:
    raw_edf = getattr(model.model, "term_edf", None)
    edf = [] if raw_edf is None else list(np.asarray(raw_edf, float).reshape(-1))
    labels = [f"s(time): {g}" for g in model.group_levels]
    if model.include_random_effect:
        labels.append("s(participant)")
    if len(labels) != len(edf):
        labels = [f"smooth_term_{j + 1}" for j in range(len(edf))]
    return pd.DataFrame({"term": labels, "edf": edf})


def summarise_time_varying_sequence_model(model: TimeVaryingSequenceModel) -> dict[str, Any]:
    if not isinstance(model, TimeVaryingSequenceModel):
        raise ValidationError("`model` must be created by `fit_time_varying_sequence_model()`.")

    y = model.model_data["outcome"].to_numpy(float)
    mus_raw = getattr(model.model, "mus", None)
    if mus_raw is not None and len(mus_raw):
        mu = np.asarray(mus_raw[0], float).reshape(-1)
        dev = _binomial_deviance(y, mu)
        null_mu = np.repeat(float(np.mean(y)), len(y))
        null_dev = _binomial_deviance(y, null_mu)
        dev_expl = float(1.0 - dev / null_dev) if null_dev > 0 else np.nan
    else:
        dev_expl = np.nan

    try:
        reml_score = float(model.model.get_reml())
    except Exception:
        reml_score = np.nan

    info = getattr(model.model, "info", None)
    md = pd.DataFrame(
        [
            {
                "outcome": model.outcome,
                "target_state": model.target_state,
                "from_state": model.from_state,
                "to_state": model.to_state,
                "n_observations": len(model.model_data),
                "n_groups": len(model.group_levels),
                "n_participants": len(model.participant_levels),
                "k": model.k,
                "spline_degree": model.spline_degree,
                "deviance_explained": dev_expl,
                "adjusted_r_squared": np.nan,
                "edf": float(getattr(model.model, "edf", np.nan)),
                "reml_score": reml_score,
                "backend": model.backend,
                "backend_solver": "QR",
                "fit_code": getattr(info, "code", np.nan),
                "lambda_updates": getattr(info, "lambda_updates", np.nan),
            }
        ]
    )
    return {
        "metadata": md,
        "parametric_terms": _parametric_table(model),
        "smooth_terms": _smooth_table(model),
        "converged": _converged(model.model),
        "method": model.method,
    }


def plot_time_varying_sequence_model(
    model: TimeVaryingSequenceModel,
    time: Sequence[float] | None = None,
    level: float = 0.95,
    show_interval: bool = True,
    ax=None,
    **kwargs,
):
    scalar_logical(show_interval, "show_interval")
    pred = predict_time_varying_sequence_model(model, time=time, level=level)
    ax = plt.gca() if ax is None else ax
    for g, p in pred.groupby("group", sort=False):
        p = p.sort_values("time")
        line = ax.plot(p.time, p.estimate, label=g, **kwargs)
        if show_interval:
            ax.fill_between(p.time, p.lower, p.upper, alpha=0.2, color=line[0].get_color())
    ax.set_xlabel("Sequence time")
    ax.set_ylabel("Estimated probability")
    ax.legend()
    ax.gp3_data = pred
    return ax
