from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ._advanced import adv_data, scalar_logical, scalar_number, validate_distance_matrix
from ._exceptions import ValidationError
from ._types import GroupComparisonResult
from .distances import SequenceClustering, validate_sequence_clusters


def _axis(ax=None):
    return ax if ax is not None else plt.subplots()[1]


_R_PALETTE_ALIASES = {
    "Viridis": "viridis",
    "Dark 3": "tab10",
}


def _palette_cmap(palette: str):
    if not isinstance(palette, str) or not palette.strip():
        raise ValidationError("`palette` must be one non-blank palette name.")
    resolved = _R_PALETTE_ALIASES.get(palette, palette)
    try:
        return plt.get_cmap(resolved)
    except ValueError as exc:
        raise ValidationError(f"Unknown plotting palette: {palette!r}.") from exc


def plot_consensus_sequence(
    consensus: pd.DataFrame,
    type: str = "agreement",
    group: Any = None,
    main: str | None = None,
    xlab: str = "Sequence position",
    ylab: str | None = None,
    *,
    ax=None,
    **kwargs,
):
    if type not in {"agreement", "states"}:
        raise ValidationError("`type` must be 'agreement' or 'states'.")
    if (
        not isinstance(consensus, pd.DataFrame)
        or consensus.attrs.get("gp3_class") != "gp3_consensus_sequence"
    ):
        raise ValidationError("`consensus` must be created by `create_consensus_sequence()`.")
    data = consensus.copy()
    group_cols = list(consensus.attrs.get("group_cols", []))
    if group_cols:
        key_frame = data[group_cols].copy()
        for col in group_cols:
            key_frame[col] = key_frame[col].map(
                lambda value: "<NA>" if pd.isna(value) else str(value)
            )
        keys = key_frame.agg("\x1c".join, axis=1)
        available = list(dict.fromkeys(keys.tolist()))
        if len(available) > 1 and group is None:
            raise ValidationError("Select one consensus group before plotting grouped results.")
        if group is not None:
            if isinstance(group, Mapping):
                if set(group) != set(group_cols) or any(
                    isinstance(v, (list, tuple, dict, set)) for v in group.values()
                ):
                    raise ValidationError(
                        "A mapping-valued `group` must provide one value per group column."
                    )
                mask = np.ones(len(data), dtype=bool)
                for col in group_cols:
                    target = group[col]
                    mask &= (
                        data[col].isna().to_numpy()
                        if pd.isna(target)
                        else (data[col].astype(str).to_numpy() == str(target))
                    )
                data = data.loc[mask].copy()
            else:
                data = data.loc[keys.astype(str) == str(group)].copy()
    if data.empty:
        raise ValidationError("No consensus positions are available to plot.")
    data = data.sort_values("sequence_order", kind="stable").reset_index(drop=True)
    ax = _axis(ax)
    if type == "agreement":
        ax.plot(data.sequence_order, data.agreement, marker="o", **kwargs)
        ax.set_ylim(0, 1)
        ax.axhline(0.5, linestyle=":")
        ax.axhline(1, linestyle="--")
        ax.set_ylabel(ylab or "Agreement proportion")
        ax.set_title(main or "Consensus agreement by position")
    else:
        display = (
            data.consensus_state.astype(object)
            .where(data.consensus_state.notna(), "<TIE>")
            .astype(str)
        )
        levels = list(consensus.attrs.get("state_levels", []))
        levels = [str(v) for v in levels]
        for v in display:
            if v not in levels:
                levels.append(v)
        y = np.array([levels.index(v) + 1 for v in display])
        ax.plot(data.sequence_order, y, marker="o", **kwargs)
        ax.set_yticks(range(1, len(levels) + 1), levels)
        ax.set_ylabel(ylab or "Consensus state")
        ax.set_title(main or "Consensus states by position")
    ax.set_xlabel(xlab)
    ax.gp3_data = data
    return ax


def plot_sequence_group_comparison(
    comparison: GroupComparisonResult,
    component: str = "state",
    measure: str | None = None,
    top_n: int = 12,
    main: str | None = None,
    xlab: str | None = None,
    ylab: str | None = None,
    *,
    ax=None,
    **kwargs,
):
    if component not in {"state", "transition", "length"}:
        raise ValidationError("Invalid comparison component.")
    scalar_number(top_n, "top_n", lower=1, integer=True)
    ax = _axis(ax)
    if not isinstance(comparison, GroupComparisonResult):
        raise ValidationError("`comparison` must be created by `compare_sequence_groups()`.")
    if component == "length":
        data = comparison.length_summary
        if data is None:
            raise ValidationError("Length summaries were not requested.")
        measure = measure or "mean_length"
        if measure not in data:
            raise ValidationError("Unknown length measure.")
        ax.bar(data.group.astype(str), data[measure], **kwargs)
        ax.set_title(main or "Sequence length by group")
        ax.set_xlabel(xlab or "Group")
        ax.set_ylabel(ylab or measure)
        ax.gp3_data = data.copy()
        return ax
    data = comparison.state_summary if component == "state" else comparison.transition_summary
    if data is None:
        raise ValidationError("The requested component was not calculated.")
    if data.empty:
        raise ValidationError("No comparison rows are available to plot.")
    key = "state" if component == "state" else "transition"
    measure = measure or "sequence_prevalence"
    if measure not in data:
        raise ValidationError("Unknown comparison measure.")
    totals = (
        data.groupby(key, sort=True)[measure]
        .max()
        .reset_index(name="score")
        .sort_values(["score", key], ascending=[False, True], kind="stable")
    )
    selected = totals.head(int(top_n))[key].astype(str).tolist()
    plotted = data.loc[data[key].astype(str).isin(selected)].copy()
    groups = comparison.groups.group.astype(str).tolist()
    matrix = pd.DataFrame(0.0, index=selected, columns=groups)
    for _, r in plotted.iterrows():
        matrix.loc[str(r[key]), str(r.group)] = float(r[measure])
    y = np.arange(len(selected))
    height = 0.8 / max(len(groups), 1)
    for i, g in enumerate(groups):
        ax.barh(
            y + (i - (len(groups) - 1) / 2) * height,
            matrix[g].to_numpy(),
            height=height,
            label=g,
            **kwargs,
        )
    ax.set_yticks(y, selected)
    ax.invert_yaxis()
    ax.legend()
    ax.set_title(main or f"Sequence {component} comparison")
    ax.set_xlabel(xlab or measure)
    ax.set_ylabel(ylab or component)
    ax.gp3_data = plotted
    ax.gp3_matrix = matrix
    return ax


def plot_sequence_index(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    sort_by: str = "input",
    state_levels: Sequence[str] | None = None,
    palette: str = "Dark 3",
    show_sequence_labels: bool = True,
    *,
    ax=None,
    **kwargs,
):
    if sort_by not in {"input", "length", "path"}:
        raise ValidationError("Invalid sort_by value.")
    scalar_logical(show_sequence_labels, "show_sequence_labels")
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    levels = list(state_levels) if state_levels is not None else list(x["state_levels"])
    levels = [str(v) for v in levels]
    observed = set(sum((list(v) for v in x["sequences"].values()), []))
    missing = sorted(observed - set(levels))
    if missing:
        raise ValidationError(
            "`state_levels` does not cover all observed states: " + ", ".join(missing) + "."
        )
    ids = list(x["sequence_ids"])
    if sort_by == "length":
        ids = sorted(ids, key=lambda sid: (len(x["sequences"][sid]), sid))
    elif sort_by == "path":
        ids = sorted(ids, key=lambda sid: ("\x1c".join(x["sequences"][sid]), sid))
    maxlen = max(map(len, x["sequences"].values()))
    matrix = np.full((len(ids), maxlen), np.nan)
    for i, sid in enumerate(ids):
        seq = x["sequences"][sid]
        matrix[i, : len(seq)] = [levels.index(s) + 1 for s in seq]
    table = pd.DataFrame(matrix, index=ids, columns=range(1, maxlen + 1))
    ax = _axis(ax)
    image_kwargs = dict(kwargs)
    image_kwargs.setdefault("cmap", _palette_cmap(palette))
    ax.imshow(matrix, aspect="auto", interpolation="nearest", **image_kwargs)
    ax.set_xlabel("Sequence position")
    ax.set_ylabel("Sequence")
    if show_sequence_labels:
        ax.set_yticks(range(len(ids)), ids)
    else:
        ax.set_yticks([])
    ax.gp3_data = table
    ax.gp3_state_levels = levels
    return ax


def plot_sequence_state_distribution(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    proportion: bool = True,
    state_levels: Sequence[str] | None = None,
    palette: str = "Dark 3",
    *,
    ax=None,
    **kwargs,
):
    scalar_logical(proportion, "proportion")
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    levels = [str(v) for v in (state_levels or x["state_levels"])]
    positions = sorted(pd.unique(x["data"][order_col]))
    table = pd.DataFrame(0.0, index=positions, columns=levels)
    for p in positions:
        counts = x["data"].loc[x["data"][order_col] == p, state_col].astype(str).value_counts()
        table.loc[p, levels] = counts.reindex(levels, fill_value=0).to_numpy()
        if proportion and table.loc[p].sum() > 0:
            table.loc[p] /= table.loc[p].sum()
    ax = _axis(ax)
    palette_colors = _palette_cmap(palette)(np.linspace(0.05, 0.95, max(len(levels), 1)))
    for index, state in enumerate(levels):
        line_kwargs = dict(kwargs)
        line_kwargs.setdefault("color", palette_colors[index])
        ax.plot(positions, table[state], label=state, **line_kwargs)
    ax.set_xlabel("Sequence position")
    ax.set_ylabel("State proportion" if proportion else "State count")
    ax.legend()
    ax.gp3_data = table
    return ax


def plot_sequence_entropy(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    base: float = 2,
    normalise: bool = True,
    *,
    ax=None,
    **kwargs,
):
    scalar_number(base, "base", lower=1 + np.finfo(float).eps)
    scalar_logical(normalise, "normalise")
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    positions = sorted(pd.unique(x["data"][order_col]))
    vals = []
    for p in positions:
        probs = (
            x["data"]
            .loc[x["data"][order_col] == p, state_col]
            .astype(str)
            .value_counts(normalize=True)
            .to_numpy(float)
        )
        ent = float(-(probs * np.log(probs)).sum() / np.log(base))
        if normalise and len(x["state_levels"]) > 1:
            ent /= np.log(len(x["state_levels"])) / np.log(base)
        vals.append(ent)
    result = pd.DataFrame({"position": positions, "entropy": vals, "normalised": normalise})
    ax = _axis(ax)
    ax.plot(result.position, result.entropy, marker="o", **kwargs)
    ax.set_xlabel("Sequence position")
    ax.set_ylabel("Normalised entropy" if normalise else "Entropy")
    ax.gp3_data = result
    return ax


def plot_sequence_distance_heatmap(
    distance: Any,
    order_by: Any = None,
    palette: str = "Viridis",
    show_labels: bool = True,
    *,
    ax=None,
    **kwargs,
):
    scalar_logical(show_labels, "show_labels")
    arr, ids = validate_distance_matrix(distance)
    ids = list(map(str, ids))
    if order_by is not None:
        assignments = order_by.assignments if isinstance(order_by, SequenceClustering) else order_by
        if isinstance(assignments, pd.Series):
            series = assignments.copy()
            series.index = series.index.astype(str)
        elif isinstance(assignments, Mapping):
            series = pd.Series(assignments)
            series.index = series.index.astype(str)
        else:
            raise ValidationError("`order_by` assignments must be named for every sequence.")
        if set(series.index) != set(ids):
            raise ValidationError("`order_by` assignments must be named for every sequence.")
        ids = sorted(ids, key=lambda sid: (series.loc[sid], sid))
        original = list(map(str, validate_distance_matrix(distance)[1]))
        idx = [original.index(s) for s in ids]
        arr = arr[np.ix_(idx, idx)]
    table = pd.DataFrame(arr, index=ids, columns=ids)
    ax = _axis(ax)
    image_kwargs = dict(kwargs)
    image_kwargs.setdefault("cmap", _palette_cmap(palette))
    ax.imshow(arr, aspect="equal", interpolation="nearest", **image_kwargs)
    ax.set_xlabel("Sequence")
    ax.set_ylabel("Sequence")
    if show_labels:
        ax.set_xticks(range(len(ids)), ids, rotation=90)
        ax.set_yticks(range(len(ids)), ids)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    ax.gp3_data = table
    return ax


def plot_transition_network(
    network: pd.DataFrame,
    weight_col: str = "weight",
    minimum_weight: float = 0,
    vertex_cex: float = 1,
    edge_scale: float = 5,
    *,
    ax=None,
    **kwargs,
):
    if (
        not isinstance(network, pd.DataFrame)
        or network.attrs.get("gp3_class") != "gp3_transition_network"
    ):
        raise ValidationError("`network` must be created by `create_transition_network()`.")
    if int(network.attrs.get("settings", {}).get("order", 1)) != 1:
        raise ValidationError("Only first-order networks can be plotted with this helper.")
    if "group_key" in network and network.group_key.nunique(dropna=False) > 1:
        raise ValidationError("Filter a grouped network to one group before plotting.")
    if weight_col not in network or not pd.api.types.is_numeric_dtype(network[weight_col]):
        raise ValidationError("`weight_col` must name a numeric network column.")
    scalar_number(minimum_weight, "minimum_weight", lower=0)
    scalar_number(vertex_cex, "vertex_cex", lower=0)
    scalar_number(edge_scale, "edge_scale", lower=0)
    edges = network.loc[network[weight_col] >= minimum_weight].copy()
    states = sorted(
        set(edges.from_state.dropna().astype(str)).union(edges.to_state.dropna().astype(str))
    )
    if not states:
        raise ValidationError("No edges satisfy the plotting threshold.")
    theta = np.linspace(0, 2 * np.pi, len(states), endpoint=False)
    pos = {s: (float(np.cos(t)), float(np.sin(t))) for s, t in zip(states, theta, strict=True)}
    ax = _axis(ax)
    for _, r in edges.iterrows():
        a = np.array(pos[str(r.from_state)])
        b = np.array(pos[str(r.to_state)])
        width = max(0.5, float(r[weight_col]) * edge_scale)
        if str(r.from_state) == str(r.to_state):
            circle = plt.Circle((a[0], a[1] + 0.12), 0.12, fill=False, linewidth=width)
            ax.add_patch(circle)
        else:
            ax.annotate("", xy=b, xytext=a, arrowprops={"arrowstyle": "->", "linewidth": width})
    for s, (px, py) in pos.items():
        ax.scatter([px], [py], s=500, facecolors="white", edgecolors="black")
        ax.text(px, py, s, ha="center", va="center", fontsize=10 * vertex_cex)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.gp3_data = edges
    return ax


def plot_sequence_cluster_silhouette(clustering: Any, distance: Any = None, *, ax=None, **kwargs):
    validation = validate_sequence_clusters(clustering, distance)
    current = validation["per_sequence"].copy()
    current = current.sort_values(
        ["cluster", "silhouette", "sequence_id"], ascending=[True, False, True], kind="stable"
    ).reset_index(drop=True)
    ax = _axis(ax)
    ax.bar(current.sequence_id.astype(str), current.silhouette, **kwargs)
    ax.axhline(0, linestyle="--")
    ax.tick_params(axis="x", rotation=90)
    ax.set_ylabel("Silhouette")
    ax.gp3_data = current
    return ax
