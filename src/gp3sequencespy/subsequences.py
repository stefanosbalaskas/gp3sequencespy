from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
from math import comb
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

from ._advanced import adv_data, scalar_character, scalar_logical, scalar_number
from ._exceptions import ValidationError


def _validate_inf_nonnegative(x: Any, name: str) -> float:
    if (
        isinstance(x, bool)
        or not isinstance(x, (int, float, np.integer, np.floating))
        or np.isnan(x)
        or x < 0
    ):
        raise ValidationError(f"`{name}` must be one non-negative number or `Inf`.")
    return float(x)


def extract_sequence_subsequences(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    metadata_cols: Sequence[str] | str | None = None,
    min_length: int = 2,
    max_length: int = 5,
    max_gap: float = np.inf,
    max_span: float = np.inf,
    repeated_state_policy: str = "preserve",
    separator: str = " > ",
    max_combinations_per_sequence: int = 100000,
) -> pd.DataFrame:
    if repeated_state_policy not in {"preserve", "collapse"}:
        raise ValidationError("Invalid repeated_state_policy.")
    scalar_number(min_length, "min_length", 1, integer=True)
    scalar_number(max_length, "max_length", min_length, integer=True)
    max_gap = _validate_inf_nonnegative(max_gap, "max_gap")
    max_span = _validate_inf_nonnegative(max_span, "max_span")
    scalar_character(separator, "separator")
    scalar_number(max_combinations_per_sequence, "max_combinations_per_sequence", 1, integer=True)
    x = adv_data(data, sequence_id_col, order_col, state_col, metadata_cols, "error")
    if any(separator in s for s in x["state_levels"]):
        raise ValidationError("`separator` must not occur inside an observed state label.")
    rows = []
    for sid in x["sequence_ids"]:
        states = list(x["sequences"][sid])
        orders = list(x["orders"][sid])
        if repeated_state_policy == "collapse" and len(states) > 1:
            keep = [0] + [i for i in range(1, len(states)) if states[i] != states[i - 1]]
            states = [states[i] for i in keep]
            orders = [orders[i] for i in keep]
        n = len(states)
        upper = min(int(max_length), n)
        if upper < int(min_length):
            continue
        expected = sum(comb(n, k) for k in range(int(min_length), upper + 1))
        if expected > max_combinations_per_sequence:
            raise ValidationError(
                "The subsequence search exceeds `max_combinations_per_sequence` for sequence "
                f"`{sid}`. Reduce `max_length` or tighten gap/span constraints."
            )
        for k in range(int(min_length), upper + 1):
            for inds0 in combinations(range(n), k):
                inds = np.array(inds0)
                skipped = np.diff(inds) - 1 if len(inds) > 1 else np.array([0])
                span = float(orders[inds[-1]] - orders[inds[0]])
                if (skipped > max_gap).any() or span > max_span:
                    continue
                rows.append(
                    {
                        "sequence_id": sid,
                        "subsequence": separator.join(states[i] for i in inds),
                        "subsequence_length": k,
                        "start_order": orders[inds[0]],
                        "end_order": orders[inds[-1]],
                        "span": span,
                        "max_observed_gap": float(skipped.max()) if len(skipped) else 0.0,
                        "selected_positions": ",".join(str(i + 1) for i in inds),
                        "selected_orders": ",".join(str(orders[i]) for i in inds),
                    }
                )
    out = pd.DataFrame(
        rows,
        columns=[
            "sequence_id",
            "subsequence",
            "subsequence_length",
            "start_order",
            "end_order",
            "span",
            "max_observed_gap",
            "selected_positions",
            "selected_orders",
        ],
    )
    if len(out):
        out = out.sort_values(
            [
                "subsequence_length",
                "subsequence",
                "sequence_id",
                "start_order",
                "selected_positions",
            ],
            kind="stable",
        ).reset_index(drop=True)
    out.attrs.update(
        gp3_class="gp3_sequence_subsequences",
        sequence_ids=x["sequence_ids"],
        n_sequences=len(x["sequence_ids"]),
        state_levels=x["state_levels"],
        metadata=(x["metadata"].to_dict(orient="list") if x["metadata"] is not None else None),
        metadata_cols=metadata_cols,
        settings={
            "min_length": int(min_length),
            "max_length": int(max_length),
            "max_gap": max_gap,
            "max_span": max_span,
            "repeated_state_policy": repeated_state_policy,
            "separator": separator,
            "max_combinations_per_sequence": int(max_combinations_per_sequence),
        },
    )
    return out


def summarise_sequence_subsequences(occurrences: pd.DataFrame) -> pd.DataFrame:
    if (
        not isinstance(occurrences, pd.DataFrame)
        or occurrences.attrs.get("gp3_class") != "gp3_sequence_subsequences"
    ):
        raise ValidationError("`occurrences` must be created by `extract_sequence_subsequences()`.")
    nseq = occurrences.attrs.get("n_sequences", 0)
    cols = [
        "subsequence",
        "subsequence_length",
        "occurrence_count",
        "sequence_count",
        "sequence_prevalence",
        "mean_span",
        "median_span",
        "mean_max_gap",
    ]
    if occurrences.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    for motif, cur in occurrences.groupby("subsequence", sort=True):
        sc = cur.sequence_id.nunique()
        rows.append(
            {
                "subsequence": motif,
                "subsequence_length": int(cur.subsequence_length.iloc[0]),
                "occurrence_count": len(cur),
                "sequence_count": sc,
                "sequence_prevalence": sc / nseq,
                "mean_span": float(cur.span.mean()),
                "median_span": float(cur.span.median()),
                "mean_max_gap": float(cur.max_observed_gap.mean()),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(
            ["sequence_prevalence", "occurrence_count", "subsequence_length", "subsequence"],
            ascending=[False, False, True, True],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def filter_sequence_subsequences(
    summary: pd.DataFrame,
    min_sequences: int = 1,
    min_prevalence: float = 0,
    max_mean_gap: float = np.inf,
    top_n: int | None = None,
    ties: str = "include",
) -> pd.DataFrame:
    if ties not in {"include", "exclude"}:
        raise ValidationError("Invalid ties value.")
    req = {
        "subsequence",
        "subsequence_length",
        "occurrence_count",
        "sequence_count",
        "sequence_prevalence",
        "mean_max_gap",
    }
    if not isinstance(summary, pd.DataFrame) or not req.issubset(summary.columns):
        raise ValidationError("`summary` is not a subsequence summary table.")
    scalar_number(min_sequences, "min_sequences", 1, integer=True)
    scalar_number(min_prevalence, "min_prevalence", 0, 1)
    max_mean_gap = _validate_inf_nonnegative(max_mean_gap, "max_mean_gap")
    if top_n is not None:
        scalar_number(top_n, "top_n", 1, integer=True)
    out = summary.loc[
        (summary.sequence_count >= min_sequences)
        & (summary.sequence_prevalence >= min_prevalence)
        & (summary.mean_max_gap <= max_mean_gap)
    ].sort_values(
        ["sequence_prevalence", "occurrence_count", "subsequence_length", "subsequence"],
        ascending=[False, False, True, True],
        kind="stable",
    )
    if top_n is not None and len(out) > top_n:
        if ties == "exclude":
            out = out.head(int(top_n))
        else:
            out = out.loc[out.sequence_prevalence >= out.iloc[int(top_n) - 1].sequence_prevalence]
    return out.reset_index(drop=True)


def _bh(p: np.ndarray) -> np.ndarray:
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1)
    return out


def compare_sequence_subsequences(
    occurrences: pd.DataFrame,
    group_col: str,
    test: str = "auto",
    p_adjust: str = "BH",
    min_sequence_count: int = 1,
) -> pd.DataFrame:
    if (
        not isinstance(occurrences, pd.DataFrame)
        or occurrences.attrs.get("gp3_class") != "gp3_sequence_subsequences"
    ):
        raise ValidationError("`occurrences` must be created by `extract_sequence_subsequences()`.")
    if test not in {"auto", "chisq", "fisher"}:
        raise ValidationError("Invalid test.")
    scalar_character(group_col, "group_col")
    scalar_number(min_sequence_count, "min_sequence_count", 1, integer=True)
    meta_raw = occurrences.attrs.get("metadata")
    meta = pd.DataFrame(meta_raw) if meta_raw is not None else None
    if meta is None or group_col not in meta.columns:
        raise ValidationError("The requested group column was not retained as sequence metadata.")
    idcol = meta.columns[0]
    groups = meta[group_col].astype("string")
    if groups.isna().any() or groups.str.strip().eq("").any():
        raise ValidationError("Group values must not be missing or blank.")
    levels = sorted(groups.astype(str).unique())
    if len(levels) < 2:
        raise ValidationError("At least two groups are required.")
    seqids = meta[idcol].astype(str).tolist()
    rows = []
    for motif in sorted(occurrences.subsequence.unique()):
        present_ids = set(
            occurrences.loc[occurrences.subsequence == motif, "sequence_id"].astype(str)
        )
        table = np.zeros((len(levels), 2), int)
        for i, g in enumerate(levels):
            ids = [sid for sid, gg in zip(seqids, groups.astype(str), strict=True) if gg == g]
            pres = sum(sid in present_ids for sid in ids)
            table[i] = [len(ids) - pres, pres]
        if table[:, 1].sum() < min_sequence_count:
            continue
        _, _, _, expected = chi2_contingency(table, correction=False)
        chosen = (
            "fisher"
            if test == "auto" and (expected < 5).any() and len(levels) == 2
            else ("chisq" if test == "auto" else test)
        )
        if chosen == "fisher" and len(levels) != 2:
            raise ValidationError("Fisher's exact test is currently limited to two groups.")
        if chosen == "fisher":
            stat, p = fisher_exact(table)
            df = np.nan
        else:
            stat, p, df, _ = chi2_contingency(table, correction=False)
        prevalence = table[:, 1] / table.sum(1)
        rec = {
            "subsequence": motif,
            "subsequence_length": int(
                occurrences.loc[occurrences.subsequence == motif, "subsequence_length"].iloc[0]
            ),
            "test": chosen,
            "statistic": float(stat),
            "df": float(df),
            "p_value": float(p),
            "max_prevalence": float(prevalence.max()),
            "min_prevalence": float(prevalence.min()),
            "prevalence_range": float(np.ptp(prevalence)),
        }
        for i, g in enumerate(levels):
            safe = "".join(ch if ch.isalnum() or ch == "." else "." for ch in g)
            rec[f"prevalence_{safe}"] = float(prevalence[i])
            rec[f"n_{safe}"] = int(table[i].sum())
        if len(levels) == 2:
            rec["prevalence_difference"] = float(prevalence[1] - prevalence[0])
        rows.append(rec)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    pvals = out.p_value.to_numpy()
    out["p_adjusted"] = _bh(pvals) if p_adjust.upper() == "BH" else pvals
    out = out.sort_values(
        ["p_adjusted", "prevalence_range", "subsequence"],
        ascending=[True, False, True],
        kind="stable",
    ).reset_index(drop=True)
    out.attrs.update(group_levels=levels, p_adjust=p_adjust)
    return out


def plot_sequence_subsequences(
    x: pd.DataFrame,
    metric: str = "sequence_prevalence",
    top_n: int = 10,
    decreasing: bool = True,
    *,
    ax=None,
    **kwargs,
) -> pd.DataFrame:
    import matplotlib.pyplot as plt

    if (
        not isinstance(x, pd.DataFrame)
        or "subsequence" not in x.columns
        or metric not in x.columns
        or not pd.api.types.is_numeric_dtype(x[metric])
    ):
        raise ValidationError("`x` must contain `subsequence` and the requested numeric metric.")
    scalar_number(top_n, "top_n", 1, integer=True)
    scalar_logical(decreasing, "decreasing")
    sel = x.sort_values(
        [metric, "subsequence"], ascending=[not decreasing, not decreasing], kind="stable"
    ).head(int(top_n))
    ax = ax or plt.gca()
    ax.bar(sel.subsequence, sel[metric], **kwargs)
    ax.tick_params(axis="x", rotation=90)
    ax.set_ylabel(metric)
    return sel.reset_index(drop=True)
