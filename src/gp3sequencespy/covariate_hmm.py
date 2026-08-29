from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from ._advanced import adv_data, row_normalise, scalar_logical, scalar_number
from ._exceptions import ValidationError


@dataclass(slots=True)
class CovariateSequenceHMM:
    initial_coefficients: np.ndarray
    transition_coefficients: list[np.ndarray]
    emission_probs: np.ndarray
    state_names: list[str]
    symbol_names: list[str]
    sequence_ids: list[str]
    sequence_log_likelihoods: pd.Series
    log_likelihood: float
    iterations: int
    converged: bool
    optimizer_convergence: np.ndarray
    tolerance: float
    pseudocount: float
    ridge: float
    log_likelihood_history: np.ndarray
    n_parameters: int
    n_observations: int
    aic: float
    bic: float
    seed: int
    initial_covariate_cols: list[str]
    transition_covariate_cols: list[str]
    initial_center: pd.Series
    initial_scale: pd.Series
    transition_center: pd.Series
    transition_scale: pd.Series
    training_observations: dict[str, np.ndarray]
    training_orders: dict[str, list[Any]]
    training_initial_design: np.ndarray
    training_transition_design: dict[str, np.ndarray]
    training_data: pd.DataFrame
    columns: dict[str, str]
    posteriors: list[dict[str, Any]] | None


def _numeric_matrix(data: pd.DataFrame, columns: Sequence[str], center=None, scale=None):
    cols = list(columns)
    if not cols:
        return np.ones((len(data), 1)), pd.Series(dtype=float), pd.Series(dtype=float), []
    missing = [c for c in cols if c not in data.columns]
    if missing:
        raise ValidationError("Missing covariate columns: " + ", ".join(missing) + ".")
    for c in cols:
        if (
            not pd.api.types.is_numeric_dtype(data[c])
            or data[c].isna().any()
            or not np.isfinite(data[c].to_numpy(float)).all()
        ):
            raise ValidationError(
                "Covariates must be finite, non-missing numeric columns: " + c + "."
            )
    raw = data[cols].to_numpy(float)
    ctr = (
        pd.Series(raw.mean(0), index=cols)
        if center is None
        else pd.Series(center, index=cols, dtype=float)
    )
    if scale is None:
        scl = np.std(raw, axis=0, ddof=1)
        scl[(~np.isfinite(scl)) | (scl <= 0)] = 1
        scl = pd.Series(scl, index=cols)
    else:
        scl = pd.Series(scale, index=cols, dtype=float)
    z = (raw - ctr.to_numpy()) / scl.to_numpy()
    return np.column_stack([np.ones(len(data)), z]), ctr, scl, cols


def _input(
    data,
    sequence_id_col,
    order_col,
    state_col,
    initial_cols,
    transition_cols,
    symbol_levels=None,
    initial_center=None,
    initial_scale=None,
    transition_center=None,
    transition_scale=None,
):
    if not isinstance(data, pd.DataFrame) and hasattr(data, "data"):
        data = data.data
    if not isinstance(data, pd.DataFrame):
        raise ValidationError("`data` must be a data frame.")
    all_cols = list(dict.fromkeys([*initial_cols, *transition_cols]))
    missing = [c for c in all_cols if c not in data.columns]
    if missing:
        raise ValidationError("Missing covariate columns: " + ", ".join(missing) + ".")
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    w = x["data"]
    observed = x["state_levels"]
    symbols = observed if symbol_levels is None else [str(v) for v in symbol_levels]
    if not symbols or len(set(symbols)) != len(symbols) or any(not s.strip() for s in symbols):
        raise ValidationError("`symbol_levels` must contain unique non-missing symbols.")
    miss = [s for s in observed if s not in symbols]
    if miss:
        raise ValidationError(
            "`symbol_levels` does not cover observed symbols: " + ", ".join(miss) + "."
        )
    groups = {sid: w.loc[w[sequence_id_col].astype(str) == sid] for sid in x["sequence_ids"]}
    for c in initial_cols:
        bad = [sid for sid, p in groups.items() if p[c].nunique(dropna=False) > 1]
        if bad:
            raise ValidationError(
                f"Initial covariate `{c}` must remain constant within each sequence."
            )
    initial_data = pd.DataFrame([p.iloc[0] for p in groups.values()]).reset_index(drop=True)
    initial_design, ic, iscl, _ = _numeric_matrix(
        initial_data, initial_cols, initial_center, initial_scale
    )
    transition_source = (
        pd.concat([p.iloc[:-1] for p in groups.values() if len(p) > 1], ignore_index=True)
        if any(len(p) > 1 for p in groups.values())
        else pd.DataFrame()
    )
    if transition_source.empty:
        raise ValidationError("At least one transition is required.")
    td_all, tc, tscl, _ = _numeric_matrix(
        transition_source, transition_cols, transition_center, transition_scale
    )
    obs = {}
    orders = {}
    td = {}
    cursor = 0
    symidx = {s: i for i, s in enumerate(symbols)}
    for sid, p in groups.items():
        obs[sid] = np.array([symidx[s] for s in p[state_col].astype(str)], dtype=int)
        orders[sid] = p[order_col].tolist()
        nt = max(len(p) - 1, 0)
        td[sid] = td_all[cursor : cursor + nt].copy()
        cursor += nt
    return {
        "data": w,
        "sequence_ids": x["sequence_ids"],
        "observations": obs,
        "orders": orders,
        "symbol_levels": symbols,
        "initial_design": initial_design,
        "transition_design": td,
        "initial_center": ic,
        "initial_scale": iscl,
        "transition_center": tc,
        "transition_scale": tscl,
        "initial_covariate_cols": list(initial_cols),
        "transition_covariate_cols": list(transition_cols),
        "columns": {"sequence_id": sequence_id_col, "order": order_col, "state": state_col},
    }


def _softmax(eta):
    eta = np.asarray(eta, float).ravel()
    eta = eta - np.max(eta)
    e = np.exp(eta)
    return e / e.sum()


def _fit_softmax(x, counts, start, ridge, maxit):
    p = x.shape[1]
    k = counts.shape[1]
    theta0 = np.asarray(start[:, : k - 1], float).reshape(-1, order="F")

    def fg(theta):
        beta = np.column_stack([np.asarray(theta).reshape((p, k - 1), order="F"), np.zeros(p)])
        eta = x @ beta
        eta -= eta.max(1, keepdims=True)
        ex = np.exp(eta)
        pr = ex / ex.sum(1, keepdims=True)
        pr = np.maximum(pr, np.finfo(float).tiny)
        val = -np.sum(counts * np.log(pr)) + 0.5 * ridge * np.sum(theta**2)
        tot = counts.sum(1)
        res = pr * tot[:, None] - counts
        grad = x.T @ res[:, : k - 1]
        return float(val), grad.reshape(-1, order="F") + ridge * theta

    fit = minimize(
        lambda th: fg(th)[0],
        theta0,
        jac=lambda th: fg(th)[1],
        method="BFGS",
        options={"maxiter": int(maxit), "gtol": 1e-9},
    )
    beta = np.column_stack([fit.x.reshape((p, k - 1), order="F"), np.zeros(p)])
    return beta, 0 if fit.success else 1


def _probabilities(ix, tx, initial_coef, transition_coef):
    initial = _softmax(np.asarray(ix) @ initial_coef)
    k = initial_coef.shape[1]
    arr = np.zeros((len(tx), k, k))
    for t in range(len(tx)):
        for origin in range(k):
            arr[t, origin] = _softmax(tx[t] @ transition_coef[origin])
    return initial, arr


def _fb(like, initial, transition):
    n, k = like.shape
    alpha = np.zeros((n, k))
    sc = np.zeros(n)
    alpha[0] = initial * like[0]
    sc[0] = alpha[0].sum()
    sc[0] = np.finfo(float).tiny if not np.isfinite(sc[0]) or sc[0] <= 0 else sc[0]
    alpha[0] /= sc[0]
    for t in range(1, n):
        alpha[t] = (alpha[t - 1] @ transition[t - 1]) * like[t]
        sc[t] = alpha[t].sum()
        sc[t] = np.finfo(float).tiny if not np.isfinite(sc[t]) or sc[t] <= 0 else sc[t]
        alpha[t] /= sc[t]
    beta = np.ones((n, k))
    for t in range(n - 2, -1, -1):
        beta[t] = transition[t] @ (like[t + 1] * beta[t + 1])
        beta[t] /= sc[t + 1]
    gamma = alpha * beta
    gt = gamma.sum(1)
    bad = (~np.isfinite(gt)) | (gt <= 0)
    gamma[bad] = 1 / k
    gt[bad] = 1
    gamma /= gt[:, None]
    xi = np.zeros((max(n - 1, 0), k, k))
    for t in range(n - 1):
        cur = np.outer(alpha[t], like[t + 1] * beta[t + 1]) * transition[t]
        total = cur.sum()
        xi[t] = cur / total if np.isfinite(total) and total > 0 else cur
    return {
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "xi": xi,
        "log_likelihood": float(np.log(sc).sum()),
    }


def _viterbi(like, initial, transition):
    n, k = like.shape
    delta = np.full((n, k), -np.inf)
    psi = np.zeros((n, k), int)
    tiny = np.finfo(float).tiny
    delta[0] = np.log(np.maximum(initial, tiny)) + np.log(np.maximum(like[0], tiny))
    for t in range(1, n):
        for j in range(k):
            cand = delta[t - 1] + np.log(np.maximum(transition[t - 1, :, j], tiny))
            psi[t, j] = np.argmax(cand)
            delta[t, j] = cand[psi[t, j]] + np.log(max(like[t, j], tiny))
    path = np.zeros(n, int)
    path[-1] = np.argmax(delta[-1])
    for t in range(n - 2, -1, -1):
        path[t] = psi[t + 1, path[t + 1]]
    return path


def fit_covariate_sequence_hmm(
    data: Any,
    n_states: int,
    initial_covariate_cols: Sequence[str] | None = None,
    transition_covariate_cols: Sequence[str] | None = None,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    symbol_levels: Sequence[str] | None = None,
    state_names: Sequence[str] | None = None,
    emission_probs=None,
    max_iter: int = 100,
    inner_maxit: int = 100,
    tolerance: float = 1e-6,
    pseudocount: float = 1e-6,
    ridge: float = 1e-6,
    seed: int = 1,
    keep_posteriors: bool = False,
) -> CovariateSequenceHMM:
    scalar_number(n_states, "n_states", 2, integer=True)
    scalar_number(max_iter, "max_iter", 1, integer=True)
    scalar_number(inner_maxit, "inner_maxit", 1, integer=True)
    scalar_number(tolerance, "tolerance", 0)
    scalar_number(pseudocount, "pseudocount", 0)
    scalar_number(ridge, "ridge", 0)
    scalar_number(seed, "seed", 0, integer=True)
    scalar_logical(keep_posteriors, "keep_posteriors")
    ic = [] if initial_covariate_cols is None else list(initial_covariate_cols)
    tc = [] if transition_covariate_cols is None else list(transition_covariate_cols)
    if len(set(ic)) != len(ic) or any(not isinstance(c, str) or not c for c in ic):
        raise ValidationError("Invalid `initial_covariate_cols`.")
    if len(set(tc)) != len(tc) or any(not isinstance(c, str) or not c for c in tc):
        raise ValidationError("Invalid `transition_covariate_cols`.")
    inp = _input(data, sequence_id_col, order_col, state_col, ic, tc, symbol_levels)
    states = (
        [f"latent_{i + 1}" for i in range(n_states)]
        if state_names is None
        else [str(s) for s in state_names]
    )
    if (
        len(states) != n_states
        or len(set(states)) != len(states)
        or any(not s.strip() for s in states)
    ):
        raise ValidationError("`state_names` must uniquely name all latent states.")
    rng = np.random.default_rng(seed)
    p0 = inp["initial_design"].shape[1]
    pt = next(iter(inp["transition_design"].values())).shape[1]
    icoef = rng.normal(0, 0.02, (p0, n_states))
    tcoef = [rng.normal(0, 0.02, (pt, n_states)) for _ in range(n_states)]
    icoef[:, -1] = 0
    for b in tcoef:
        b[:, -1] = 0
    emission = (
        np.asarray(emission_probs, float)
        if emission_probs is not None
        else rng.exponential(size=(n_states, len(inp["symbol_levels"]))) + 0.1
    )
    if (
        emission.shape != (n_states, len(inp["symbol_levels"]))
        or not np.isfinite(emission).all()
        or (emission < 0).any()
    ):
        raise ValidationError("Invalid `emission_probs`.")
    emission = row_normalise(emission)
    history = []
    converged = False
    previous = -np.inf
    optconv = np.array([], dtype=int)
    ids = inp["sequence_ids"]
    for iteration in range(1, max_iter + 1):
        init_counts = np.zeros((len(ids), n_states))
        tx = np.vstack([inp["transition_design"][sid] for sid in ids])
        tr_counts = [np.zeros((len(tx), n_states)) for _ in range(n_states)]
        ec = np.full((n_states, len(inp["symbol_levels"])), pseudocount)
        ll = []
        cursor = 0
        for s, sid in enumerate(ids):
            obs = inp["observations"][sid]
            initial, tr = _probabilities(
                inp["initial_design"][s], inp["transition_design"][sid], icoef, tcoef
            )
            like = emission[:, obs].T
            fb = _fb(like, initial, tr)
            init_counts[s] = fb["gamma"][0]
            nt = max(len(obs) - 1, 0)
            if nt:
                for origin in range(n_states):
                    tr_counts[origin][cursor : cursor + nt] = fb["xi"][:, origin, :]
                cursor += nt
            for t, o in enumerate(obs):
                ec[:, o] += fb["gamma"][t]
            ll.append(fb["log_likelihood"])
        current = float(np.sum(ll))
        history.append(current)
        icoef, ci = _fit_softmax(inp["initial_design"], init_counts, icoef, ridge, inner_maxit)
        new = []
        convs = [ci]
        for origin in range(n_states):
            b, c = _fit_softmax(tx, tr_counts[origin], tcoef[origin], ridge, inner_maxit)
            new.append(b)
            convs.append(c)
        tcoef = new
        optconv = np.asarray(convs, int)
        emission = row_normalise(ec)
        if iteration > 1 and abs(current - previous) / max(1, abs(previous)) <= tolerance:
            converged = True
            break
        previous = current
    finals = []
    posts = []
    for s, sid in enumerate(ids):
        obs = inp["observations"][sid]
        initial, tr = _probabilities(
            inp["initial_design"][s], inp["transition_design"][sid], icoef, tcoef
        )
        fb = _fb(emission[:, obs].T, initial, tr)
        finals.append(fb["log_likelihood"])
        posts.append(fb)
    loglik = float(np.sum(finals))
    history[-1] = loglik
    npar = (
        p0 * (n_states - 1)
        + n_states * pt * (n_states - 1)
        + n_states * (len(inp["symbol_levels"]) - 1)
    )
    nobs = sum(len(inp["observations"][sid]) for sid in ids)
    return CovariateSequenceHMM(
        icoef,
        tcoef,
        emission,
        states,
        inp["symbol_levels"],
        ids,
        pd.Series(finals, index=ids),
        loglik,
        len(history),
        converged,
        optconv,
        float(tolerance),
        float(pseudocount),
        float(ridge),
        np.asarray(history),
        int(npar),
        int(nobs),
        float(-2 * loglik + 2 * npar),
        float(-2 * loglik + np.log(max(1, nobs)) * npar),
        int(seed),
        ic,
        tc,
        inp["initial_center"],
        inp["initial_scale"],
        inp["transition_center"],
        inp["transition_scale"],
        inp["observations"],
        inp["orders"],
        inp["initial_design"],
        inp["transition_design"],
        inp["data"],
        inp["columns"],
        posts if keep_posteriors else None,
    )


def predict_covariate_transition_probabilities(
    model: CovariateSequenceHMM, newdata: pd.DataFrame
) -> pd.DataFrame:
    if not isinstance(model, CovariateSequenceHMM):
        raise ValidationError("`model` must be created by `fit_covariate_sequence_hmm()`.")
    if not isinstance(newdata, pd.DataFrame) or newdata.empty:
        raise ValidationError("`newdata` must be a non-empty data frame.")
    design, _, _, _ = _numeric_matrix(
        newdata, model.transition_covariate_cols, model.transition_center, model.transition_scale
    )
    rows: list[dict[str, Any]] = []
    for r, x in enumerate(design, 1):
        for origin, from_state in enumerate(model.state_names):
            pr = _softmax(x @ model.transition_coefficients[origin])
            rows.extend(
                {"row": r, "from_state": from_state, "to_state": to, "probability": float(pr[j])}
                for j, to in enumerate(model.state_names)
            )
    return pd.DataFrame(rows)


def decode_covariate_sequence_states(
    model: CovariateSequenceHMM,
    data: Any = None,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    method: str = "viterbi",
) -> pd.DataFrame:
    if not isinstance(model, CovariateSequenceHMM):
        raise ValidationError("`model` must be created by `fit_covariate_sequence_hmm()`.")
    if method not in {"viterbi", "posterior"}:
        raise ValidationError("Invalid method.")
    if data is None:
        ids = model.sequence_ids
        obs = model.training_observations
        orders = model.training_orders
        ix = model.training_initial_design
        tx = model.training_transition_design
    else:
        inp = _input(
            data,
            sequence_id_col,
            order_col,
            state_col,
            model.initial_covariate_cols,
            model.transition_covariate_cols,
            model.symbol_names,
            model.initial_center,
            model.initial_scale,
            model.transition_center,
            model.transition_scale,
        )
        ids = inp["sequence_ids"]
        obs = inp["observations"]
        orders = inp["orders"]
        ix = inp["initial_design"]
        tx = inp["transition_design"]
    rows = []
    for s, sid in enumerate(ids):
        initial, tr = _probabilities(
            ix[s], tx[sid], model.initial_coefficients, model.transition_coefficients
        )
        like = model.emission_probs[:, obs[sid]].T
        fb = _fb(like, initial, tr)
        path = (
            _viterbi(like, initial, tr) if method == "viterbi" else np.argmax(fb["gamma"], axis=1)
        )
        probs = fb["gamma"][np.arange(len(path)), path]
        for t, j in enumerate(path):
            rows.append(
                {
                    "sequence_id": sid,
                    "sequence_order": orders[sid][t],
                    "observed_state": model.symbol_names[obs[sid][t]],
                    "latent_state": model.state_names[j],
                    "posterior_probability": float(probs[t]),
                    "decoding_method": method,
                }
            )
    return pd.DataFrame(rows)


def summarise_covariate_sequence_hmm(model: CovariateSequenceHMM) -> dict[str, pd.DataFrame]:
    if not isinstance(model, CovariateSequenceHMM):
        raise ValidationError("`model` must be created by `fit_covariate_sequence_hmm()`.")

    def coef_rows(mat, state_col):
        cov = ["(Intercept)", *state_col]
        return [
            {
                "covariate": cov[i],
                "latent_state": model.state_names[j],
                "coefficient": float(mat[i, j]),
            }
            for j in range(mat.shape[1])
            for i in range(mat.shape[0])
        ]

    initial = pd.DataFrame(coef_rows(model.initial_coefficients, model.initial_covariate_cols))
    trans: list[dict[str, Any]] = []
    cov = ["(Intercept)", *model.transition_covariate_cols]
    for origin, mat in enumerate(model.transition_coefficients):
        trans.extend(
            {
                "from_state": model.state_names[origin],
                "covariate": cov[i],
                "to_state": model.state_names[j],
                "coefficient": float(mat[i, j]),
            }
            for j in range(mat.shape[1])
            for i in range(mat.shape[0])
        )
    emission = pd.DataFrame(
        [
            {
                "latent_state": model.state_names[i],
                "symbol": model.symbol_names[j],
                "probability": float(model.emission_probs[i, j]),
            }
            for j in range(len(model.symbol_names))
            for i in range(len(model.state_names))
        ]
    )
    fit = pd.DataFrame(
        [
            {
                "n_states": len(model.state_names),
                "n_sequences": len(model.sequence_ids),
                "n_observations": model.n_observations,
                "log_likelihood": model.log_likelihood,
                "aic": model.aic,
                "bic": model.bic,
                "iterations": model.iterations,
                "converged": model.converged,
                "optimizers_converged": bool(np.all(model.optimizer_convergence == 0)),
                "ridge": model.ridge,
            }
        ]
    )
    return {
        "fit": fit,
        "initial_coefficients": initial,
        "transition_coefficients": pd.DataFrame(trans),
        "emission": emission,
    }
