from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ._advanced import adv_data, scalar_character, scalar_number
from ._exceptions import ValidationError


@dataclass(slots=True)
class SequenceComparisonDesign:
    group_col: str
    unit_col: str
    design: str
    pair_col: str | None
    cluster_col: str | None
    interpretation: str


@dataclass(slots=True)
class SequenceGroupInference:
    estimate: pd.DataFrame
    permutation_distribution: np.ndarray
    unit_data: pd.DataFrame
    sequence_data: pd.DataFrame
    design: SequenceComparisonDesign
    metric: str
    target_state: str | None
    target_subsequence: str | None
    interpretation: str
    seed: int
    bootstrap: dict[str, Any] | None = None


def declare_sequence_comparison_design(
    group_col: str,
    unit_col: str,
    design: str = "observational",
    pair_col: str | None = None,
    cluster_col: str | None = None,
) -> SequenceComparisonDesign:
    if design not in {"observational", "randomized", "paired_randomized"}:
        raise ValidationError("Invalid design.")
    scalar_character(group_col, "group_col")
    scalar_character(unit_col, "unit_col")
    if pair_col is not None:
        scalar_character(pair_col, "pair_col")
    if cluster_col is not None:
        scalar_character(cluster_col, "cluster_col")
    if design == "paired_randomized" and pair_col is None:
        raise ValidationError("`pair_col` is required for a paired randomized design.")
    return SequenceComparisonDesign(
        group_col,
        unit_col,
        design,
        pair_col,
        cluster_col,
        "associational" if design == "observational" else "randomization-based",
    )


def _subseq_present(sequence: list[str], pattern: list[str]) -> bool:
    if not pattern or len(pattern) > len(sequence):
        return False
    return any(
        sequence[i : i + len(pattern)] == pattern for i in range(len(sequence) - len(pattern) + 1)
    )


def _metric_data(
    data: Any,
    design: SequenceComparisonDesign,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    metric: str,
    target_state: str | None,
    target_subsequence: str | None,
    separator: str,
):
    meta_cols = list(
        dict.fromkeys(
            [
                x
                for x in [design.group_col, design.unit_col, design.pair_col, design.cluster_col]
                if x is not None
            ]
        )
    )
    x = adv_data(data, sequence_id_col, order_col, state_col, meta_cols, "error")
    meta = x["metadata"].copy()
    meta = meta.rename(columns={sequence_id_col: "sequence_id"})
    values = []
    pattern = target_subsequence.split(separator) if target_subsequence is not None else None
    for sid in x["sequence_ids"]:
        seq = x["sequences"][sid]
        if metric == "sequence_length":
            v = float(len(seq))
        elif metric == "transition_count":
            v = float(max(len(seq) - 1, 0))
        elif metric == "state_prevalence":
            v = float(np.mean(np.array(seq) == target_state))
        else:
            v = float(_subseq_present(seq, pattern or []))
        values.append({"sequence_id": sid, "metric": v})
    merged = pd.DataFrame(values).merge(meta, on="sequence_id", how="left", sort=False)
    unit_cols = list(
        dict.fromkeys(
            [
                x
                for x in [design.unit_col, design.group_col, design.pair_col, design.cluster_col]
                if x is not None
            ]
        )
    )
    rows = []
    for _, part in merged.groupby(unit_cols, sort=True, dropna=False):
        rec = {c: part.iloc[0][c] for c in unit_cols}
        rec.update(metric=float(part.metric.mean()), n_sequences=len(part))
        rows.append(rec)
    return merged, pd.DataFrame(rows), x["state_levels"]


def _difference(metric: np.ndarray, group: np.ndarray, levels: list[str]) -> float:
    return float(metric[group == levels[1]].mean() - metric[group == levels[0]].mean())


def _permute(
    unit: pd.DataFrame,
    design: SequenceComparisonDesign,
    levels: list[str],
    rng: np.random.Generator,
) -> np.ndarray:
    group = unit[design.group_col].astype(str).to_numpy()
    if design.design == "paired_randomized":
        pair = unit[design.pair_col].astype(str).to_numpy()
        out = group.copy()
        for val in pd.unique(pair):
            rows = np.flatnonzero(pair == val)
            if len(rows) != 2 or set(group[rows]) != set(levels):
                raise ValidationError(
                    "Each randomized pair must contain exactly one unit from each group."
                )
            if rng.random() < 0.5:
                out[rows] = out[rows][::-1]
        return out
    assignment_col = design.unit_col if design.cluster_col is None else design.cluster_col
    assignment = unit[assignment_col].astype(str).to_numpy()
    clusters = pd.unique(assignment)
    cg = []
    for c in clusters:
        vals = pd.unique(group[assignment == c])
        if len(vals) != 1:
            raise ValidationError("Assignment clusters must have one group label.")
        cg.append(vals[0])
    perm = rng.permutation(cg)
    mapping = dict(zip(clusters, perm, strict=True))
    return np.array([mapping[a] for a in assignment])


def test_sequence_group_difference(
    data: Any,
    design: SequenceComparisonDesign,
    metric: str = "sequence_length",
    target_state: str | None = None,
    target_subsequence: str | None = None,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    separator: str = " > ",
    n_permutations: int = 999,
    alternative: str = "two.sided",
    seed: int = 1,
) -> SequenceGroupInference:
    if not isinstance(design, SequenceComparisonDesign):
        raise ValidationError("`design` must be created by `declare_sequence_comparison_design()`.")
    if metric not in {
        "sequence_length",
        "transition_count",
        "state_prevalence",
        "subsequence_presence",
    }:
        raise ValidationError("Invalid metric.")
    if alternative not in {"two.sided", "greater", "less"}:
        raise ValidationError("Invalid alternative.")
    if metric == "state_prevalence":
        scalar_character(target_state, "target_state")
    if metric == "subsequence_presence":
        scalar_character(target_subsequence, "target_subsequence")
    scalar_character(separator, "separator")
    scalar_number(n_permutations, "n_permutations", 1, integer=True)
    scalar_number(seed, "seed", 0, integer=True)
    seqdata, unit, _ = _metric_data(
        data,
        design,
        sequence_id_col,
        order_col,
        state_col,
        metric,
        target_state,
        target_subsequence,
        separator,
    )
    groups = unit[design.group_col].astype("string")
    if groups.isna().any() or groups.str.strip().eq("").any():
        raise ValidationError("Group values must not be missing or blank.")
    levels = sorted(groups.astype(str).unique())
    if len(levels) != 2:
        raise ValidationError("The current inferential contrast requires exactly two groups.")
    g = groups.astype(str).to_numpy()
    vals = unit.metric.to_numpy(float)
    obs = _difference(vals, g, levels)
    rng = np.random.default_rng(seed)
    per = np.array(
        [
            _difference(vals, _permute(unit, design, levels, rng), levels)
            for _ in range(int(n_permutations))
        ]
    )
    extreme = (
        np.abs(per) >= abs(obs)
        if alternative == "two.sided"
        else per >= obs
        if alternative == "greater"
        else per <= obs
    )
    p = (1 + int(extreme.sum())) / (n_permutations + 1)
    means = [vals[g == lev].mean() for lev in levels]
    est = pd.DataFrame(
        [
            {
                "group_1": levels[0],
                "group_2": levels[1],
                "mean_group_1": means[0],
                "mean_group_2": means[1],
                "difference_group_2_minus_group_1": obs,
                "p_value": p,
                "alternative": alternative,
                "n_permutations": int(n_permutations),
            }
        ]
    )
    interp = (
        "Associational permutation contrast; causal interpretation is not supported."
        if design.design == "observational"
        else "Randomization-based contrast, conditional on valid assignment and study "
        "implementation."
    )
    return SequenceGroupInference(
        est, per, unit, seqdata, design, metric, target_state, target_subsequence, interp, int(seed)
    )


def bootstrap_sequence_group_difference(
    inference: SequenceGroupInference, n_boot: int = 999, level: float = 0.95, seed: int = 1
) -> SequenceGroupInference:
    if not isinstance(inference, SequenceGroupInference):
        raise ValidationError("`inference` must be created by `test_sequence_group_difference()`.")
    scalar_number(n_boot, "n_boot", 1, integer=True)
    scalar_number(level, "level", 0.5, 0.999999)
    scalar_number(seed, "seed", 0, integer=True)
    unit = inference.unit_data
    groups = unit[inference.design.group_col].astype(str).to_numpy()
    levels = [inference.estimate.group_1.iloc[0], inference.estimate.group_2.iloc[0]]
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(int(n_boot)):
        means = []
        for lev in levels:
            v = unit.metric.to_numpy(float)[groups == lev]
            means.append(float(rng.choice(v, len(v), replace=True).mean()))
        boot.append(means[1] - means[0])
    alpha = (1 - level) / 2
    interval = np.quantile(np.array(boot), [alpha, 1 - alpha], method="weibull")
    inference.bootstrap = {
        "estimates": np.array(boot),
        "interval": pd.DataFrame(
            [
                {
                    "level": level,
                    "lower": interval[0],
                    "upper": interval[1],
                    "n_boot": int(n_boot),
                    "seed": int(seed),
                }
            ]
        ),
    }
    return inference


def summarise_sequence_group_inference(inference: SequenceGroupInference) -> dict[str, Any]:
    if not isinstance(inference, SequenceGroupInference):
        raise ValidationError("`inference` must be created by `test_sequence_group_difference()`.")
    d = inference.design
    design = pd.DataFrame(
        [
            {
                "design": d.design,
                "group_col": d.group_col,
                "unit_col": d.unit_col,
                "pair_col": d.pair_col,
                "cluster_col": d.cluster_col,
            }
        ]
    )
    return {
        "estimate": inference.estimate,
        "bootstrap_interval": None
        if inference.bootstrap is None
        else inference.bootstrap["interval"],
        "design": design,
        "metric": inference.metric,
        "interpretation": inference.interpretation,
    }


def plot_sequence_group_inference(
    inference: SequenceGroupInference, type: str = "permutation", *, ax=None, **kwargs
) -> SequenceGroupInference:
    import matplotlib.pyplot as plt

    if not isinstance(inference, SequenceGroupInference):
        raise ValidationError("`inference` must be created by `test_sequence_group_difference()`.")
    if type not in {"permutation", "group_means"}:
        raise ValidationError("Invalid type.")
    ax = ax or plt.gca()
    if type == "permutation":
        ax.hist(inference.permutation_distribution, **kwargs)
        ax.axvline(inference.estimate.difference_group_2_minus_group_1.iloc[0], linestyle="--")
        ax.set_xlabel("Permuted mean difference")
    else:
        ax.bar(
            [inference.estimate.group_1.iloc[0], inference.estimate.group_2.iloc[0]],
            [inference.estimate.mean_group_1.iloc[0], inference.estimate.mean_group_2.iloc[0]],
            **kwargs,
        )
        ax.set_ylabel(inference.metric)
    return inference
