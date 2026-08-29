from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import networkx as nx
import pandas as pd

from ._advanced import adv_data, scalar_logical
from ._exceptions import ValidationError
from .data import prepare_sequence_data


@dataclass(slots=True)
class WideSequenceAdapter:
    data: pd.DataFrame
    positions: list[float]
    state_levels: list[str]
    sequence_ids: list[str]
    missing: Any = None
    right: str = "DEL"
    backend: str = "TraMineR"


@dataclass(slots=True)
class ArulesSequenceAdapter:
    itemsets: list[list[str]]
    transaction_info: pd.DataFrame
    sequence_ids: list[str]


@dataclass(slots=True)
class GrpStringInput:
    events: pd.DataFrame
    event_names: list[str]
    characters: list[str]
    key: pd.DataFrame
    strings: dict[str, str]
    sequence_ids: list[str]


def _wide_sequence_data(
    data: Any,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    fill: Any = None,
) -> tuple[pd.DataFrame, list[float], list[str], list[str]]:
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    positions = sorted(float(v) for v in pd.unique(x["data"][order_col]))
    columns = [
        f"position_{int(p) if float(p).is_integer() else format(p, '.17g')}" for p in positions
    ]
    wide = pd.DataFrame(fill, index=x["sequence_ids"], columns=columns, dtype=object)
    position_index = {p: i for i, p in enumerate(positions)}
    for sid in x["sequence_ids"]:
        rows = x["data"].loc[x["data"][sequence_id_col].astype(str) == sid]
        for _, row in rows.iterrows():
            p = float(row[order_col])
            wide.iat[wide.index.get_loc(sid), position_index[p]] = str(row[state_col])
    wide.index.name = sequence_id_col
    return wide, positions, list(x["state_levels"]), list(x["sequence_ids"])


def as_traminer_sequences(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    missing: Any = None,
    right: str = "DEL",
    **_: Any,
) -> WideSequenceAdapter:
    wide, positions, states, ids = _wide_sequence_data(
        data, sequence_id_col, order_col, state_col, fill=missing
    )
    return WideSequenceAdapter(wide, positions, states, ids, missing, right, "TraMineR")


def as_arules_sequences(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
) -> ArulesSequenceAdapter:
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    itemsets = [[str(v)] for v in x["data"][state_col].tolist()]
    sequence_lookup = {sid: i + 1 for i, sid in enumerate(x["sequence_ids"])}
    sequence_id = x["data"][sequence_id_col].astype(str).map(sequence_lookup).astype(int)
    event_id = x["data"].groupby(sequence_id_col, sort=False).cumcount() + 1
    info = pd.DataFrame(
        {"sequenceID": sequence_id.to_numpy(), "eventID": event_id.to_numpy(dtype=int)}
    )
    return ArulesSequenceAdapter(itemsets, info, list(x["sequence_ids"]))


def as_grpstring_data(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    alphabet: Sequence[str] | None = None,
) -> GrpStringInput:
    wide, _, states, ids = _wide_sequence_data(data, sequence_id_col, order_col, state_col)
    if alphabet is None:
        alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") + list(
            "!#$%&*+-./:;<=>?@^_~"
        )
    chars = list(alphabet)
    if (
        len(chars) < len(states)
        or any(not isinstance(x, str) or len(x) != 1 for x in chars)
        or len(set(chars)) != len(chars)
    ):
        raise ValidationError(
            "`alphabet` must provide at least one unique character per observed state."
        )
    characters = chars[: len(states)]
    lookup = dict(zip(states, characters, strict=True))
    strings: dict[str, str] = {}
    for sid, row in wide.iterrows():
        values = [str(v) for v in row.tolist() if not pd.isna(v) and str(v) != ""]
        strings[str(sid)] = "".join(lookup[v] for v in values)
    key = pd.DataFrame({"event_name": states, "character": characters})
    return GrpStringInput(wide, states, characters, key, strings, ids)


def as_seqhmm_sequences(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    **kwargs: Any,
) -> WideSequenceAdapter:
    result = as_traminer_sequences(
        data,
        sequence_id_col=sequence_id_col,
        order_col=order_col,
        state_col=state_col,
        **kwargs,
    )
    result.backend = "seqHMM"
    return result


def as_igraph_transition_network(network: pd.DataFrame, directed: bool = True) -> nx.Graph:
    scalar_logical(directed, "directed")
    if not isinstance(network, pd.DataFrame):
        raise ValidationError("`network` must be created by `create_transition_network()`.")
    required = {
        "from_state",
        "to_state",
        "weight",
        "count",
        "sequence_count",
        "sequence_prevalence",
    }
    if not required.issubset(network.columns):
        raise ValidationError("`network` must be created by `create_transition_network()`.")
    order = int(network.attrs.get("settings", {}).get("order", 1))
    if order != 1:
        raise ValidationError("Only first-order networks can be converted directly to a graph.")
    group_cols = list(network.attrs.get("group_cols", []))
    if group_cols and len(network[group_cols].drop_duplicates()) > 1:
        raise ValidationError("Select one network group before converting to a graph.")
    graph: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    for _, row in network.iterrows():
        graph.add_edge(
            str(row["from_state"]),
            str(row["to_state"]),
            weight=float(row["weight"]),
            count=float(row["count"]),
            sequence_count=float(row["sequence_count"]),
            sequence_prevalence=float(row["sequence_prevalence"]),
        )
    return graph


def _infer_column(
    data: pd.DataFrame, explicit: str | None, candidates: list[str], role: str
) -> str:
    if explicit is not None:
        if explicit not in data.columns:
            raise ValidationError(f"Missing explicitly mapped {role} column `{explicit}`.")
        return explicit
    found = [c for c in candidates if c in data.columns]
    if not found:
        raise ValidationError(f"Could not infer the {role} column. Supply it explicitly.")
    if len(found) > 1:
        raise ValidationError(
            f"Multiple candidate {role} columns were found: {', '.join(found)}. "
            "Supply the mapping explicitly."
        )
    return found[0]


def prepare_gp3tools_sequences(
    data: Any,
    sequence_id_col: str | None = None,
    order_col: str | None = None,
    state_col: str | None = None,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | str | None = None,
    **kwargs: Any,
):
    if (
        not isinstance(data, pd.DataFrame)
        and hasattr(data, "data")
        and isinstance(data.data, pd.DataFrame)
    ):
        data = data.data
    elif isinstance(data, dict) and isinstance(data.get("data"), pd.DataFrame):
        data = data["data"]
    if not isinstance(data, pd.DataFrame):
        raise ValidationError(
            "A data frame or object with a data-frame `data` component is required."
        )
    sequence_id_col = _infer_column(
        data,
        sequence_id_col,
        ["sequence_id", "scanpath_id", "trial_id", "participant_trial_id"],
        "sequence identifier",
    )
    order_col = _infer_column(
        data,
        order_col,
        ["sequence_order", "position", "event_order", "fixation_index", "row_order"],
        "sequence order",
    )
    state_col = _infer_column(
        data,
        state_col,
        ["state", "aoi", "aoi_label", "event", "event_name"],
        "state",
    )
    if duration_col is None:
        found = [
            c for c in ["duration", "fixation_duration", "event_duration"] if c in data.columns
        ]
        if len(found) > 1:
            raise ValidationError(
                "Multiple candidate duration columns were found: "
                + ", ".join(found)
                + ". Supply `duration_col` explicitly."
            )
        duration_col = found[0] if found else None
    return prepare_sequence_data(
        data,
        sequence_id_col=sequence_id_col,
        order_col=order_col,
        state_col=state_col,
        duration_col=duration_col,
        metadata_cols=metadata_cols,
        **kwargs,
    )
