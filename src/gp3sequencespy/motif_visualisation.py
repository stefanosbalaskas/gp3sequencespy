from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ._exceptions import ValidationError
from ._types import MotifExtractionResult
from .motifs import _as_summary, _sort_overall


@dataclass(slots=True)
class MotifPositionResult:
    summary: pd.DataFrame
    occurrences: pd.DataFrame
    sequences: pd.DataFrame
    state_dictionary: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame
    extraction_settings: dict[str, Any]
    settings: dict[str, Any]
    n_occurrences: int
    n_motifs: int
    n_groups: int


def _whole(v, name, minimum=0):
    if (
        isinstance(v, bool)
        or not isinstance(v, (int, float, np.integer, np.floating))
        or not np.isfinite(v)
        or int(v) != v
        or v < minimum
    ):
        raise ValidationError(
            f"`{name}` must be a whole number greater than or equal to {minimum}."
        )
    return int(v)


def _validate_extraction(x):
    if not isinstance(x, MotifExtractionResult):
        raise ValidationError("`x` must be an object returned by `extract_sequence_ngrams()`.")


def summarise_sequence_motif_positions(
    x: MotifExtractionResult,
    position: str = "start",
    scale: str = "absolute",
    by: Sequence[str] | str | None = None,
) -> MotifPositionResult:
    _validate_extraction(x)
    if position not in {"start", "centre", "end"}:
        raise ValidationError("Invalid `position`.")
    if scale not in {"absolute", "relative"}:
        raise ValidationError("Invalid `scale`.")
    groups = [] if by is None else ([by] if isinstance(by, str) else list(by))
    if len(set(groups)) != len(groups) or any(not isinstance(c, str) or not c for c in groups):
        raise ValidationError("`by` must be `NULL` or a unique character vector of column names.")
    reserved = {
        "sequence_id",
        "motif_id",
        "motif_key",
        "motif",
        "motif_length",
        "start_index",
        "end_index",
        "start_order",
        "end_order",
        "start_original_row",
        "end_original_row",
        "occurrence_index",
    }
    if any(c in reserved for c in groups):
        raise ValidationError(
            "`by` must contain preserved metadata columns, not reserved motif columns."
        )
    missing = [c for c in groups if c not in x.occurrences.columns]
    if missing:
        raise ValidationError(
            "The following `by` columns were not preserved during extraction: "
            + ", ".join(missing)
            + "."
        )
    basecols = [
        "sequence_id",
        *groups,
        "motif_id",
        "motif_key",
        "motif",
        "motif_length",
        "start_index",
        "end_index",
    ]
    if x.occurrences.empty:
        occ = pd.DataFrame(
            columns=[
                *basecols,
                "n_states",
                "position_basis",
                "position_scale",
                "absolute_position",
                "relative_position",
                "position_value",
            ]
        )
        sm = pd.DataFrame(
            columns=[
                *groups,
                "motif_id",
                "motif_key",
                "motif",
                "motif_length",
                "position_basis",
                "position_scale",
                "n_occurrences",
                "n_sequences",
                "min_position",
                "max_position",
                "mean_position",
                "median_position",
            ]
        )
    else:
        occ = x.occurrences.copy()
        lengths = x.sequences.set_index("sequence_id")["n_states"].to_dict()
        occ["n_states"] = occ.sequence_id.map(lengths).astype(int)
        if position == "start":
            absolute = occ.start_index.astype(float)
        elif position == "end":
            absolute = occ.end_index.astype(float)
        else:
            absolute = (occ.start_index.astype(float) + occ.end_index.astype(float)) / 2
        rel = np.where(
            occ.n_states.to_numpy() <= 1,
            0,
            (absolute.to_numpy() - 1) / (occ.n_states.to_numpy() - 1),
        )
        rel = np.clip(rel, 0, 1)
        occ["position_basis"] = position
        occ["position_scale"] = scale
        occ["absolute_position"] = absolute
        occ["relative_position"] = rel
        occ["position_value"] = rel if scale == "relative" else absolute
        occ = occ[
            [
                *basecols,
                "n_states",
                "position_basis",
                "position_scale",
                "absolute_position",
                "relative_position",
                "position_value",
            ]
        ]
        rows = []
        keys = [*groups, "motif_id"]
        for _, g in occ.groupby(keys, sort=True, dropna=False):
            f = g.iloc[0]
            rec = {c: f[c] for c in groups}
            vals = g.position_value.to_numpy(float)
            rec.update(
                {
                    "motif_id": f.motif_id,
                    "motif_key": f.motif_key,
                    "motif": f.motif,
                    "motif_length": int(f.motif_length),
                    "position_basis": position,
                    "position_scale": scale,
                    "n_occurrences": int(len(g)),
                    "n_sequences": int(g.sequence_id.nunique()),
                    "min_position": float(vals.min()),
                    "max_position": float(vals.max()),
                    "mean_position": float(vals.mean()),
                    "median_position": float(np.median(vals)),
                }
            )
            rows.append(rec)
        sm = pd.DataFrame(rows)
        sortcols = [
            *groups,
            "mean_position",
            "median_position",
            "n_occurrences",
            "n_sequences",
            "motif_length",
            "motif_key",
        ]
        asc = [True] * len(groups) + [True, True, False, False, True, True]
        sm = sm.sort_values(sortcols, ascending=asc, kind="stable").reset_index(drop=True)
        occsort = [
            *groups,
            "motif_length",
            "motif_key",
            "position_value",
            "sequence_id",
            "start_index",
            "end_index",
        ]
        occ = occ.sort_values(occsort, kind="stable").reset_index(drop=True)
    ng = 0 if sm.empty else (1 if not groups else sm[groups].drop_duplicates().shape[0])
    return MotifPositionResult(
        sm,
        occ,
        x.sequences,
        x.state_dictionary,
        x.audit,
        x.status,
        x.mapping,
        x.settings,
        {
            "position": position,
            "scale": scale,
            "by": groups,
            "absolute_unit": "one_based_state_index",
            "relative_range": [0, 1],
        },
        len(occ),
        int(occ.motif_id.nunique()) if len(occ) else 0,
        int(ng),
    )


def format_sequence_motif_positions(
    x: MotifPositionResult,
    digits: int = 3,
    position_units: str = "proportion",
    include_rank: bool = True,
) -> dict[str, Any]:
    if not isinstance(x, MotifPositionResult):
        raise ValidationError(
            "`x` must be an object returned by `summarise_sequence_motif_positions()`."
        )
    digits = _whole(digits, "digits", 0)
    if digits > 15:
        raise ValidationError("`digits` must not exceed 15.")
    if not isinstance(include_rank, bool):
        raise ValidationError("`include_rank` must be TRUE or FALSE.")
    if position_units not in {"proportion", "percent"}:
        raise ValidationError("Invalid `position_units`.")
    by = x.settings["by"]
    table = x.summary.copy()
    sortcols = [
        *by,
        "mean_position",
        "median_position",
        "n_occurrences",
        "n_sequences",
        "motif_length",
        "motif_key",
    ]
    asc = [True] * len(by) + [True, True, False, False, True, True]
    if len(table):
        table = table.sort_values(sortcols, ascending=asc, kind="stable").reset_index(drop=True)
    if include_rank:
        table["rank"] = 0
        if len(table):
            if by:
                groupby_key = by[0] if len(by) == 1 else by
                for _, idx in table.groupby(groupby_key, sort=True, dropna=False).groups.items():
                    table.loc[idx, "rank"] = (
                        table.loc[idx, "mean_position"].rank(method="min").astype(int)
                    )
            else:
                table["rank"] = table.mean_position.rank(method="min").astype(int)
        table["rank"] = table["rank"].astype(int)
    applied = position_units if x.settings["scale"] == "relative" else "index"
    cols = ["min_position", "max_position", "mean_position", "median_position"]
    if len(table) and x.settings["scale"] == "relative" and position_units == "percent":
        table[cols] = 100 * table[cols]
    for c in cols:
        table[c] = table[c].round(digits)
    table["position_unit"] = applied
    front = [
        *by,
        *(["rank"] if include_rank else []),
        "motif_id",
        "motif_key",
        "motif",
        "motif_length",
        "position_basis",
        "position_scale",
        "position_unit",
        "n_occurrences",
        "n_sequences",
    ]
    table = table[front + [c for c in table if c not in front]]
    return {
        "table": table,
        "audit": x.audit,
        "status": x.status,
        "mapping": x.mapping,
        "source_settings": x.settings,
        "settings": {
            "digits": digits,
            "requested_position_units": position_units,
            "applied_position_units": applied,
            "include_rank": include_rank,
            "rank_metric": "mean_position",
            "rank_direction": "earlier_to_later",
        },
    }


def _motif_plot_data(x, metric, top_n, motif_lengths, ties):
    if metric not in {"sequence_prevalence", "n_occurrences", "n_sequences", "occurrence_share"}:
        raise ValidationError("Invalid metric.")
    top_n = _whole(top_n, "top_n", 1)
    if ties not in {"include", "first"}:
        raise ValidationError("Invalid ties.")
    sm = _as_summary(x)
    d = sm.overall.copy()
    if motif_lengths is not None:
        d = d.loc[d.motif_length.isin(sorted(set(map(int, motif_lengths))))]
    d = _sort_overall(d, metric)
    if len(d) > top_n:
        d = (
            d.loc[d[metric] >= d.iloc[top_n - 1][metric]].copy()
            if ties == "include"
            else d.iloc[:top_n].copy()
        )
    d = d.reset_index(drop=True)
    d["plot_rank"] = np.arange(1, len(d) + 1)
    d["plot_value"] = d[metric].astype(float)
    d["plot_label"] = d.motif.astype(str)
    return d


def plot_sequence_motifs(
    x,
    metric: str = "sequence_prevalence",
    top_n: int = 20,
    motif_lengths: Sequence[int] | None = None,
    ties: str = "include",
    horizontal: bool = True,
    ax=None,
):
    if not isinstance(horizontal, bool):
        raise ValidationError("`horizontal` must be TRUE or FALSE.")
    d = _motif_plot_data(x, metric, top_n, motif_lengths, ties)
    ax = plt.gca() if ax is None else ax
    if len(d):
        if horizontal:
            bars = ax.barh(np.arange(len(d)), d.plot_value)
            ax.set_yticks(np.arange(len(d)), d.plot_label)
            ax.invert_yaxis()
        else:
            bars = ax.bar(np.arange(len(d)), d.plot_value)
            ax.set_xticks(np.arange(len(d)), d.plot_label, rotation=90)
        d["bar_midpoint"] = [
            float(
                (b.get_y() + b.get_height() / 2) if horizontal else (b.get_x() + b.get_width() / 2)
            )
            for b in bars
        ]
    else:
        d["bar_midpoint"] = pd.Series(dtype=float)
        ax.text(
            0.5,
            0.5,
            "No motifs match the requested plotting settings.",
            ha="center",
            transform=ax.transAxes,
        )
    ax.set_title("Sequence motifs")
    ax.set_xlabel("Sequence prevalence (proportion)" if horizontal else "")
    ax.gp3_data = d
    return ax


def _position_plot_data(x, motifs, position, scale, top_n):
    top_n = _whole(top_n, "top_n", 1)
    pos = (
        x
        if isinstance(x, MotifPositionResult)
        else summarise_sequence_motif_positions(x, position=position, scale=scale)
    )
    # recompute requested basis/scale even for pre-existing summary
    if isinstance(x, MotifPositionResult) and (
        x.settings["position"] != position or x.settings["scale"] != scale
    ):
        occ = x.occurrences.copy()
        if position == "start":
            absolute = occ.start_index.astype(float)
        elif position == "end":
            absolute = occ.end_index.astype(float)
        else:
            absolute = (occ.start_index.astype(float) + occ.end_index.astype(float)) / 2
        rel = np.where(
            occ.n_states.to_numpy() <= 1,
            0,
            (absolute.to_numpy() - 1) / (occ.n_states.to_numpy() - 1),
        )
        occ["position_basis"] = position
        occ["position_scale"] = scale
        occ["absolute_position"] = absolute
        occ["relative_position"] = np.clip(rel, 0, 1)
        occ["position_value"] = occ.relative_position if scale == "relative" else absolute
    else:
        occ = pos.occurrences.copy()
    dictionary = (
        occ[["motif_id", "motif_key", "motif", "motif_length"]].drop_duplicates()
        if len(occ)
        else pd.DataFrame(columns=["motif_id", "motif_key", "motif", "motif_length"])
    )
    if motifs is not None:
        sels = [motifs] if isinstance(motifs, str) else list(motifs)
        ids = []
        unknown = []
        for s in sels:
            hit = (
                dictionary.loc[
                    (dictionary.motif_id == s)
                    | (dictionary.motif_key == s)
                    | (dictionary.motif == s),
                    "motif_id",
                ]
                .unique()
                .tolist()
            )
            ids.extend(hit)
            unknown.extend([] if hit else [s])
        if unknown:
            raise ValidationError(
                "The following requested motifs were not found: "
                + ", ".join(map(str, unknown))
                + "."
            )
        mt = []
        for mid in dict.fromkeys(ids):
            z = occ.loc[occ.motif_id == mid].iloc[0]
            mt.append(
                {
                    "motif_id": mid,
                    "motif": z.motif,
                    "n_occurrences": int((occ.motif_id == mid).sum()),
                    "n_sequences": int(occ.loc[occ.motif_id == mid, "sequence_id"].nunique()),
                    "motif_length": int(z.motif_length),
                    "motif_key": z.motif_key,
                }
            )
        motif_table = pd.DataFrame(mt)
    else:
        mt = []
        for mid, g in occ.groupby("motif_id", sort=True):
            z = g.iloc[0]
            mt.append(
                {
                    "motif_id": mid,
                    "motif": z.motif,
                    "n_occurrences": len(g),
                    "n_sequences": g.sequence_id.nunique(),
                    "motif_length": int(z.motif_length),
                    "motif_key": z.motif_key,
                }
            )
        motif_table = (
            pd.DataFrame(mt)
            .sort_values(
                ["n_occurrences", "n_sequences", "motif_length", "motif_key"],
                ascending=[False, False, True, True],
                kind="stable",
            )
            .head(top_n)
            .reset_index(drop=True)
            if mt
            else pd.DataFrame(
                columns=[
                    "motif_id",
                    "motif",
                    "n_occurrences",
                    "n_sequences",
                    "motif_length",
                    "motif_key",
                ]
            )
        )
    rank = {mid: i + 1 for i, mid in enumerate(motif_table.motif_id.tolist())}
    d = occ.loc[occ.motif_id.isin(rank)].copy()
    d["plot_rank"] = d.motif_id.map(rank).astype(int) if len(d) else pd.Series(dtype=int)
    return d, motif_table


def plot_sequence_motif_positions(
    x,
    motifs: Sequence[str] | str | None = None,
    position: str = "start",
    scale: str = "relative",
    top_n: int = 10,
    display: str = "strip",
    ax=None,
):
    if position not in {"start", "centre", "end"}:
        raise ValidationError("Invalid position.")
    if scale not in {"absolute", "relative"}:
        raise ValidationError("Invalid scale.")
    if display not in {"strip", "distribution"}:
        raise ValidationError("Invalid `display`.")
    d, mt = _position_plot_data(x, motifs, position, scale, top_n)
    ax = plt.gca() if ax is None else ax
    if not len(d):
        d["plot_y"] = pd.Series(dtype=float)
        ax.text(
            0.5,
            0.5,
            "No motif occurrences match the requested plotting settings.",
            ha="center",
            transform=ax.transAxes,
        )
    elif display == "strip":
        base = len(mt) - d.plot_rank + 1
        keys = list(zip(d.motif_id, d.position_value, strict=True))
        seen: dict[tuple[Any, Any], int] = {}
        counts = {k: keys.count(k) for k in set(keys)}
        ys = []
        for b, k in zip(base, keys, strict=True):
            seen[k] = seen.get(k, 0) + 1
            ys.append(float(b + (seen[k] - (counts[k] + 1) / 2) * 0.06))
        d["plot_y"] = ys
        ax.scatter(d.position_value, d.plot_y)
        ax.set_yticks(range(1, len(mt) + 1), list(reversed(mt.motif.tolist())))
    else:
        vals = [
            d.loc[d.motif_id == mid, "position_value"].to_numpy()
            for mid in reversed(mt.motif_id.tolist())
        ]
        labels = list(reversed(mt.motif.tolist()))
        from importlib.metadata import version as package_version

        mpl_version = tuple(int(part) for part in package_version("matplotlib").split(".")[:2])
        if mpl_version >= (3, 10):
            ax.boxplot(vals, tick_labels=labels, orientation="horizontal")
        elif mpl_version >= (3, 9):
            ax.boxplot(vals, tick_labels=labels, vert=False)
        else:
            ax.boxplot(vals, labels=labels, vert=False)
        d["plot_y"] = len(mt) - d.plot_rank + 1
    if scale == "relative":
        ax.set_xlim(0, 1)
    ax.set_title("Sequence motif positions")
    ax.gp3_data = d
    ax.gp3_motif_table = mt
    return ax
