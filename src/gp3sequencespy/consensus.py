from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from ._advanced import (
    adv_data,
    group_key,
    match_cols,
    scalar_character,
    scalar_logical,
    scalar_number,
    state_order,
    tie,
)
from ._exceptions import ValidationError
from ._types import GroupComparisonResult


def create_consensus_sequence(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    group_cols: Sequence[str] | str | None = None,
    weight_col: str | None = None,
    missing_state_policy: str = "exclude",
    missing_state_label: str = "<MISSING>",
    tie_method: str = "first",
    state_levels: Sequence[Any] | None = None,
    min_support: int = 1,
) -> pd.DataFrame:
    if missing_state_policy not in {"exclude", "state", "error"}:
        raise ValidationError("Invalid missing_state_policy.")
    if tie_method not in {"first", "last", "missing", "all"}:
        raise ValidationError("Invalid tie_method.")
    scalar_number(min_support, "min_support", lower=1, integer=True)
    inp = adv_data(
        data,
        sequence_id_col,
        order_col,
        state_col,
        group_cols,
        {"exclude": "drop", "state": "state", "error": "error"}[missing_state_policy],
        missing_state_label,
    )
    groups = match_cols(inp["data"], group_cols, "group_cols")
    working = inp["data"].copy()
    if weight_col is not None:
        scalar_character(weight_col, "weight_col")
        if weight_col not in working.columns:
            raise ValidationError("`weight_col` is absent from `data`.")
        weights = pd.to_numeric(working[weight_col], errors="coerce")
        if weights.isna().any() or (~np.isfinite(weights)).any() or (weights < 0).any():
            raise ValidationError("`weight_col` must contain finite, non-negative numeric values.")
    else:
        weights = pd.Series(np.ones(len(working)), index=working.index)
    working[".gp3_adv_weight"] = weights
    working[".gp3_adv_group"] = group_key(working, groups)
    order_states = state_order(working[state_col], state_levels)
    rows = []
    for _, gdf in working.groupby(".gp3_adv_group", sort=True):
        positions = sorted(pd.unique(gdf[order_col]))
        nseq = gdf[sequence_id_col].astype(str).nunique()
        for pos in positions:
            sub = gdf.loc[gdf[order_col] == pos]
            contribute = sub.loc[sub[".gp3_adv_weight"] > 0]
            support = contribute[sequence_id_col].astype(str).nunique()
            if support < min_support or len(contribute) == 0:
                continue
            t = tie(
                contribute[state_col].astype(str).tolist(),
                contribute[".gp3_adv_weight"].astype(float).tolist(),
                order_states,
                tie_method,
            )
            rec = {c: gdf.iloc[0][c] for c in groups}
            rec.update(
                sequence_order=pos,
                consensus_state=t["selected"],
                support_n=int(support),
                support_weight=float(contribute[".gp3_adv_weight"].sum()),
                agreement=float(t["agreement"]),
                tie_n=len(t["tied"]),
                tied_states=" | ".join(t["tied"]),
                n_sequences=int(nseq),
            )
            rows.append(rec)
    result = pd.DataFrame(
        rows,
        columns=[
            *groups,
            "sequence_order",
            "consensus_state",
            "support_n",
            "support_weight",
            "agreement",
            "tie_n",
            "tied_states",
            "n_sequences",
        ],
    )
    result.attrs["gp3_class"] = "gp3_consensus_sequence"
    result.attrs["group_cols"] = groups
    result.attrs["state_levels"] = order_states
    result.attrs["settings"] = {
        "missing_state_policy": missing_state_policy,
        "missing_state_label": missing_state_label,
        "tie_method": tie_method,
        "min_support": int(min_support),
        "weight_col": weight_col,
    }
    return result


def _check_consensus(consensus: pd.DataFrame) -> list[str]:
    if (
        not isinstance(consensus, pd.DataFrame)
        or consensus.attrs.get("gp3_class") != "gp3_consensus_sequence"
    ):
        raise ValidationError("`consensus` must be created by `create_consensus_sequence()`.")
    return list(consensus.attrs.get("group_cols", []))


def summarise_consensus_agreement(
    consensus: pd.DataFrame, by: str = "overall", threshold: float = 0.5
) -> pd.DataFrame:
    if by not in {"overall", "group", "position"}:
        raise ValidationError("Invalid `by`.")
    scalar_number(threshold, "threshold", 0, 1)
    groups = _check_consensus(consensus)
    if by == "group" and not groups:
        raise ValidationError('`by = "group"` requires a consensus created with `group_cols`.')
    split = [] if by == "overall" else (groups if by == "group" else groups + ["sequence_order"])
    cols = [
        *split,
        "n_positions",
        "mean_agreement",
        "median_agreement",
        "min_agreement",
        "max_agreement",
        "weighted_agreement",
        "n_ties",
        "n_below_threshold",
        "threshold",
    ]
    if consensus.empty:
        return pd.DataFrame(columns=cols)
    key = group_key(consensus, split)
    out = []
    for k in dict.fromkeys(key.tolist()):
        sub = consensus.loc[key == k]
        rec = {c: sub.iloc[0][c] for c in split}
        sw = float(sub.support_weight.sum())
        weighted = (
            float(np.average(sub.agreement, weights=sub.support_weight)) if sw > 0 else np.nan
        )
        rec.update(
            n_positions=len(sub),
            mean_agreement=float(sub.agreement.mean()),
            median_agreement=float(sub.agreement.median()),
            min_agreement=float(sub.agreement.min()),
            max_agreement=float(sub.agreement.max()),
            weighted_agreement=weighted,
            n_ties=int((sub.tie_n > 1).sum()),
            n_below_threshold=int((sub.agreement < threshold).sum()),
            threshold=float(threshold),
        )
        out.append(rec)
    return pd.DataFrame(out, columns=cols)


def format_consensus_sequence(
    consensus: pd.DataFrame,
    separator: str = " -> ",
    include_order: bool = False,
    include_agreement: bool = False,
    digits: int = 3,
) -> pd.DataFrame:
    groups = _check_consensus(consensus)
    scalar_character(separator, "separator")
    scalar_logical(include_order, "include_order")
    scalar_logical(include_agreement, "include_agreement")
    scalar_number(digits, "digits", 0, integer=True)
    if consensus.empty:
        return pd.DataFrame(columns=[*groups, "path", "n_positions"])
    key = group_key(consensus, groups)
    out = []
    for k in dict.fromkeys(key.tolist()):
        sub = consensus.loc[key == k].sort_values("sequence_order", kind="stable")
        labels = ["<TIE>" if pd.isna(x) else str(x) for x in sub.consensus_state]
        if include_order:
            labels = [f"{o}:{x}" for o, x in zip(sub.sequence_order, labels, strict=True)]
        if include_agreement:
            labels = [f"{x} [{a:.{digits}f}]" for x, a in zip(labels, sub.agreement, strict=True)]
        out.append(
            {
                **{c: sub.iloc[0][c] for c in groups},
                "path": separator.join(labels),
                "n_positions": len(sub),
            }
        )
    return pd.DataFrame(out)


def compare_sequence_groups(
    data: Any,
    group_col: str,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    reference: Any = None,
    metrics: Sequence[str] = ("state", "transition", "length"),
    include_self: bool = True,
    transition_separator: str = " -> ",
    zero_policy: str = "missing",
) -> GroupComparisonResult:
    if zero_policy not in {"missing", "infinite"}:
        raise ValidationError("Invalid zero_policy.")
    metrics = list(dict.fromkeys(metrics))
    invalid = [m for m in metrics if m not in {"state", "transition", "length"}]
    if invalid or not metrics:
        raise ValidationError("Select at least one comparison metric.")
    scalar_logical(include_self, "include_self")
    scalar_character(transition_separator, "transition_separator")
    scalar_character(group_col, "group_col")
    x = adv_data(data, sequence_id_col, order_col, state_col, group_col, "error")
    if any(transition_separator in s for s in x["state_levels"]):
        raise ValidationError(
            "`transition_separator` must not occur inside an observed state label."
        )
    gm = x["metadata"].copy()
    gm = gm.rename(columns={sequence_id_col: ".sequence_id", group_col: ".group"})
    gtext = gm[".group"].astype("string")
    if gm[".group"].isna().any() or gtext.str.strip().eq("").any():
        raise ValidationError(
            "The grouping column must be non-missing and non-blank for every sequence."
        )
    groups = sorted(gtext.astype(str).unique().tolist())
    if len(groups) < 2:
        raise ValidationError("At least two sequence groups are required.")
    if reference is not None and str(reference) not in groups:
        raise ValidationError("`reference` is not an observed group.")
    seq_group = dict(zip(gm[".sequence_id"].astype(str), gm[".group"].astype(str), strict=True))
    state_rows = []
    trans_rows = []
    length_rows = []
    for g in groups:
        ids = [sid for sid, val in seq_group.items() if val == g]
        seqs = [x["sequences"][sid] for sid in ids]
        allstates = [z for seq in seqs for z in seq]
        for st in x["state_levels"]:
            cnt = allstates.count(st)
            sc = sum(st in seq for seq in seqs)
            state_rows.append(
                {
                    "group": g,
                    "state": st,
                    "event_count": cnt,
                    "event_share": cnt / max(1, len(allstates)),
                    "sequence_count": sc,
                    "sequence_prevalence": sc / len(seqs),
                }
            )
        transitions = []
        for seq in seqs:
            transitions.extend(
                [
                    f"{a}{transition_separator}{b}"
                    for a, b in zip(seq[:-1], seq[1:], strict=True)
                    if include_self or a != b
                ]
            )
        for tr in sorted(set(transitions)):
            cnt = transitions.count(tr)
            sc = sum(
                tr
                in [f"{a}{transition_separator}{b}" for a, b in zip(seq[:-1], seq[1:], strict=True)]
                for seq in seqs
            )
            trans_rows.append(
                {
                    "group": g,
                    "transition": tr,
                    "occurrence_count": cnt,
                    "occurrence_share": cnt / max(1, len(transitions)),
                    "sequence_count": sc,
                    "sequence_prevalence": sc / len(seqs),
                }
            )
        lens = np.array([len(z) for z in seqs], float)
        length_rows.append(
            {
                "group": g,
                "n_sequences": len(lens),
                "mean_length": float(lens.mean()),
                "median_length": float(np.median(lens)),
                "min_length": int(lens.min()),
                "max_length": int(lens.max()),
                "sd_length": float(lens.std(ddof=1)) if len(lens) > 1 else 0.0,
            }
        )
    ss = pd.DataFrame(state_rows)
    ts = pd.DataFrame(
        trans_rows,
        columns=[
            "group",
            "transition",
            "occurrence_count",
            "occurrence_share",
            "sequence_count",
            "sequence_prevalence",
        ],
    )
    ls = pd.DataFrame(length_rows)
    pairs = (
        [(a, b) for a, b in combinations(groups, 2)]
        if reference is None
        else [(g, str(reference)) for g in groups if g != str(reference)]
    )

    def contrasts(summary: pd.DataFrame, keycol: str, measures: list[str]) -> pd.DataFrame:
        out = []
        keys = list(dict.fromkeys(summary[keycol].astype(str).tolist())) if len(summary) else []
        for g1, g2 in pairs:
            for key in keys:
                a = summary.loc[(summary.group == g1) & (summary[keycol].astype(str) == key)]
                b = summary.loc[(summary.group == g2) & (summary[keycol].astype(str) == key)]
                rec = {"group_1": g1, "group_2": g2, keycol: key}
                for m in measures:
                    va = float(a.iloc[0][m]) if len(a) else 0.0
                    vb = float(b.iloc[0][m]) if len(b) else 0.0
                    ratio = (
                        np.inf
                        if vb == 0 and zero_policy == "infinite" and va > 0
                        else (np.nan if vb == 0 else va / vb)
                    )
                    rec.update(
                        {
                            f"{m}_group_1": va,
                            f"{m}_group_2": vb,
                            f"{m}_difference": va - vb,
                            f"{m}_ratio": ratio,
                        }
                    )
                out.append(rec)
        return pd.DataFrame(out)

    sc = contrasts(ss, "state", ["event_share", "sequence_prevalence"])
    tc = contrasts(ts, "transition", ["occurrence_share", "sequence_prevalence"])
    lc = pd.DataFrame(
        [
            {
                "group_1": g1,
                "group_2": g2,
                "mean_length_group_1": float(ls.loc[ls.group == g1, "mean_length"].iloc[0]),
                "mean_length_group_2": float(ls.loc[ls.group == g2, "mean_length"].iloc[0]),
                "mean_length_difference": float(
                    ls.loc[ls.group == g1, "mean_length"].iloc[0]
                    - ls.loc[ls.group == g2, "mean_length"].iloc[0]
                ),
                "median_length_group_1": float(ls.loc[ls.group == g1, "median_length"].iloc[0]),
                "median_length_group_2": float(ls.loc[ls.group == g2, "median_length"].iloc[0]),
                "median_length_difference": float(
                    ls.loc[ls.group == g1, "median_length"].iloc[0]
                    - ls.loc[ls.group == g2, "median_length"].iloc[0]
                ),
            }
            for g1, g2 in pairs
        ]
    )
    groupdf = pd.DataFrame(
        {"group": groups, "n_sequences": [sum(v == g for v in seq_group.values()) for g in groups]}
    )
    return GroupComparisonResult(
        groupdf,
        ss if "state" in metrics else None,
        sc if "state" in metrics else None,
        ts if "transition" in metrics else None,
        tc if "transition" in metrics else None,
        ls if "length" in metrics else None,
        lc if "length" in metrics else None,
        {
            "reference": reference,
            "metrics": metrics,
            "include_self": include_self,
            "transition_separator": transition_separator,
            "zero_policy": zero_policy,
        },
    )
