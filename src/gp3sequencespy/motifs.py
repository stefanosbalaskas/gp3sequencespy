from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from ._exceptions import ValidationError
from ._types import (
    FormattedTableResult,
    MotifExtractionResult,
    MotifFilterResult,
    MotifSummaryResult,
)
from .summaries import _assert_flag, _assert_output_names, _assert_text_scalar, encode_sequence_data


def _whole(value: Any, argument: str, minimum: int = 0, allow_none: bool = False) -> int | None:
    if allow_none and value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float, np.integer, np.floating))
        or not np.isfinite(value)
        or value < minimum
        or int(value) != value
    ):
        raise ValidationError(
            f"`{argument}` must be one whole number greater than or equal to {minimum}."
        )
    return int(value)


def _prop(value: Any, argument: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float, np.integer, np.floating))
        or not np.isfinite(value)
        or not 0 <= value <= 1
    ):
        raise ValidationError(f"`{argument}` must be one finite number between 0 and 1.")
    return float(value)


def _choice(value: str, choices: Sequence[str], argument: str) -> str:
    if value not in choices:
        raise ValidationError(
            f"`{argument}` must be one of: " + ", ".join(f"`{x}`" for x in choices) + "."
        )
    return value


def _sort_overall(df: pd.DataFrame, primary: str) -> pd.DataFrame:
    if df.empty:
        return df.reset_index(drop=True)
    secondary = [x for x in ["sequence_prevalence", "n_occurrences", "n_sequences"] if x != primary]
    cols = [primary] + secondary + ["motif_length", "motif_key"]
    asc = [False] * (1 + len(secondary)) + [True, True]
    return df.sort_values(cols, ascending=asc, kind="stable").reset_index(drop=True)


def extract_sequence_ngrams(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
    min_length: int = 2,
    max_length: int = 3,
    overlap: str = "allow",
    separator: str = " > ",
    state_levels: Sequence[Any] | None = None,
) -> MotifExtractionResult:
    min_length = _whole(min_length, "min_length", 1) or 1
    max_length = _whole(max_length, "max_length", 1) or 1
    if max_length < min_length:
        raise ValidationError("`max_length` must be greater than or equal to `min_length`.")
    overlap = _choice(overlap, ["allow", "disallow"], "overlap")
    _assert_text_scalar(separator, "separator")
    metadata = _assert_output_names(
        metadata_cols,
        [
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
            "n_states",
            "n_candidate_occurrences",
            "n_retained_occurrences",
            "n_distinct_motifs",
        ],
        "motif",
    )
    encoded = encode_sequence_data(
        data,
        sequence_id_col,
        order_col,
        state_col,
        duration_col,
        metadata,
        expected_states,
        state_levels,
        prefix="S",
    )
    df = encoded.data
    ids = list(dict.fromkeys(df.sequence_id.tolist()))
    occ = []
    seqrows = []
    for sid in ids:
        inds = df.index[df.sequence_id == sid].tolist()
        n = len(inds)
        meta = {c: df.loc[inds[0], c] for c in metadata}
        candidates = 0
        if n >= min_length:
            for length in range(min_length, min(max_length, n) + 1):
                windows = n - length + 1
                candidates += windows
                for start0 in range(windows):
                    wr = inds[start0 : start0 + length]
                    codes = df.loc[wr, "state_code"].tolist()
                    labels = df.loc[wr, "state"].tolist()
                    key = "|".join(codes)
                    occ.append(
                        {
                            "sequence_id": sid,
                            **meta,
                            "motif_id": f"L{length}:{key}",
                            "motif_key": key,
                            "motif": separator.join(labels),
                            "motif_length": length,
                            "start_index": start0 + 1,
                            "end_index": start0 + length,
                            "start_order": df.loc[wr[0], "sequence_order"],
                            "end_order": df.loc[wr[-1], "sequence_order"],
                            "start_original_row": int(df.loc[wr[0], "original_row"]),
                            "end_original_row": int(df.loc[wr[-1], "original_row"]),
                        }
                    )
        seqrows.append(
            {
                "sequence_id": sid,
                **meta,
                "n_states": n,
                "n_candidate_occurrences": candidates,
                "n_retained_occurrences": 0,
                "n_distinct_motifs": 0,
            }
        )
    occurrences = pd.DataFrame(occ)
    sequences = pd.DataFrame(seqrows)
    if overlap == "disallow" and len(occurrences):
        keep = []
        for _, g in occurrences.groupby(["sequence_id", "motif_id"], sort=True, dropna=False):
            g = g.sort_values(["start_index", "end_index"], kind="stable")
            last = -np.inf
            for idx, row in g.iterrows():
                if row.start_index > last:
                    keep.append(idx)
                    last = row.end_index
        occurrences = occurrences.loc[sorted(keep)].copy()
    if len(occurrences):
        rank = {s: i for i, s in enumerate(ids)}
        occurrences["__rank"] = occurrences.sequence_id.map(rank)
        occurrences = (
            occurrences.sort_values(
                ["__rank", "start_index", "motif_length", "motif_key"], kind="stable"
            )
            .drop(columns="__rank")
            .reset_index(drop=True)
        )
        occurrences["occurrence_index"] = (
            occurrences.groupby(["sequence_id", "motif_id"], sort=True).cumcount() + 1
        )
    else:
        columns = [
            "sequence_id",
            *metadata,
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
        ]
        occurrences = pd.DataFrame(columns=columns)
    for i, row in sequences.iterrows():
        x = (
            occurrences.loc[occurrences.sequence_id == row.sequence_id]
            if len(occurrences)
            else occurrences
        )
        sequences.loc[i, "n_retained_occurrences"] = len(x)
        sequences.loc[i, "n_distinct_motifs"] = x.motif_id.nunique() if len(x) else 0
    for c in ["n_states", "n_candidate_occurrences", "n_retained_occurrences", "n_distinct_motifs"]:
        if c in sequences:
            sequences[c] = sequences[c].astype(int)
    if len(occurrences):
        motifs = (
            occurrences[["motif_id", "motif_key", "motif", "motif_length"]]
            .drop_duplicates()
            .sort_values(["motif_length", "motif_key"], kind="stable")
            .reset_index(drop=True)
        )
    else:
        motifs = pd.DataFrame(columns=["motif_id", "motif_key", "motif", "motif_length"])
    settings = {
        "min_length": min_length,
        "max_length": max_length,
        "overlap": overlap,
        "overlap_scope": "within_sequence_motif",
        "overlap_rule": "left_to_right_greedy"
        if overlap == "disallow"
        else "all_contiguous_windows",
        "separator": separator,
        "n_sequences": len(ids),
    }
    return MotifExtractionResult(
        occurrences,
        motifs,
        sequences,
        encoded.audit,
        encoded.status,
        encoded.mapping,
        encoded.dictionary,
        settings,
    )


def _as_summary(x: Any) -> MotifSummaryResult:
    if isinstance(x, MotifSummaryResult):
        return x
    if isinstance(x, MotifFilterResult):
        return MotifSummaryResult(
            x.by_sequence,
            x.motifs,
            x.sequences,
            x.state_dictionary,
            x.audit,
            x.status,
            x.mapping,
            x.extraction_settings,
            len(x.sequences),
            int(x.by_sequence.n_occurrences.sum()) if len(x.by_sequence) else 0,
            len(x.motifs),
        )
    if isinstance(x, MotifExtractionResult):
        return summarise_sequence_motifs(x)
    raise ValidationError("`x` must be a motif extraction, summary, or filtered-motif object.")


def summarise_sequence_motifs(x: MotifExtractionResult) -> MotifSummaryResult:
    if not isinstance(x, MotifExtractionResult):
        raise ValidationError("`x` must be an object returned by `extract_sequence_ngrams()`.")
    occ = x.occurrences
    sequences = x.sequences
    metadata = [
        c
        for c in sequences.columns
        if c
        not in [
            "sequence_id",
            "n_states",
            "n_candidate_occurrences",
            "n_retained_occurrences",
            "n_distinct_motifs",
        ]
    ]
    total_seq = len(sequences)
    total_occ = len(occ)
    if total_occ == 0:
        by = pd.DataFrame(
            columns=[
                "sequence_id",
                *metadata,
                "motif_id",
                "motif_key",
                "motif",
                "motif_length",
                "n_occurrences",
                "first_start_index",
                "last_start_index",
            ]
        )
        overall = pd.DataFrame(
            columns=[
                "motif_id",
                "motif_key",
                "motif",
                "motif_length",
                "n_occurrences",
                "n_sequences",
                "sequence_prevalence",
                "occurrence_share",
                "mean_occurrences_per_sequence",
                "mean_occurrences_when_present",
            ]
        )
    else:
        rows = []
        for (_, _), g in occ.groupby(["sequence_id", "motif_id"], sort=True, dropna=False):
            first = g.iloc[0]
            rows.append(
                {
                    "sequence_id": first.sequence_id,
                    **{c: first[c] for c in metadata},
                    "motif_id": first.motif_id,
                    "motif_key": first.motif_key,
                    "motif": first.motif,
                    "motif_length": int(first.motif_length),
                    "n_occurrences": len(g),
                    "first_start_index": int(g.start_index.min()),
                    "last_start_index": int(g.start_index.max()),
                }
            )
        by = pd.DataFrame(rows)
        overall_rows = []
        for mid, g in by.groupby("motif_id", sort=True):
            first = g.iloc[0]
            nocc = int(g.n_occurrences.sum())
            nseq = len(g)
            overall_rows.append(
                {
                    "motif_id": mid,
                    "motif_key": first.motif_key,
                    "motif": first.motif,
                    "motif_length": int(first.motif_length),
                    "n_occurrences": nocc,
                    "n_sequences": nseq,
                    "sequence_prevalence": nseq / total_seq if total_seq else np.nan,
                    "occurrence_share": nocc / total_occ,
                    "mean_occurrences_per_sequence": nocc / total_seq if total_seq else np.nan,
                    "mean_occurrences_when_present": nocc / nseq,
                }
            )
        overall = _sort_overall(pd.DataFrame(overall_rows), "sequence_prevalence")
        mr = {x: i for i, x in enumerate(overall.motif_id)}
        sr = {x: i for i, x in enumerate(sequences.sequence_id)}
        by = (
            by.assign(__m=by.motif_id.map(mr), __s=by.sequence_id.map(sr))
            .sort_values(["__m", "__s"], kind="stable")
            .drop(columns=["__m", "__s"])
            .reset_index(drop=True)
        )
    return MotifSummaryResult(
        by,
        overall,
        sequences,
        x.state_dictionary,
        x.audit,
        x.status,
        x.mapping,
        x.settings,
        total_seq,
        total_occ,
        len(overall),
    )


def filter_sequence_motifs(
    x: Any,
    min_occurrences: int = 1,
    min_sequences: int = 1,
    min_prevalence: float = 0,
    motif_lengths: Sequence[int] | None = None,
    top_n: int | None = None,
    rank_by: str = "sequence_prevalence",
    ties: str = "include",
) -> MotifFilterResult:
    min_occurrences = _whole(min_occurrences, "min_occurrences", 0) or 0
    min_sequences = _whole(min_sequences, "min_sequences", 0) or 0
    min_prevalence = _prop(min_prevalence, "min_prevalence")
    top_n = _whole(top_n, "top_n", 1, True)
    if motif_lengths is not None:
        try:
            resolved_lengths: list[int] = []
            for value in motif_lengths:
                resolved = _whole(value, "motif_lengths", 1)
                assert resolved is not None
                resolved_lengths.append(resolved)
        except ValidationError as exc:
            raise ValidationError(
                "`motif_lengths` must contain positive whole numbers or be `NULL`."
            ) from exc
        motif_lengths = sorted(set(resolved_lengths))
    rank_by = _choice(rank_by, ["sequence_prevalence", "n_occurrences", "n_sequences"], "rank_by")
    ties = _choice(ties, ["include", "first"], "ties")
    sm = _as_summary(x)
    available = sm.overall
    selected = available.loc[
        (available.n_occurrences >= min_occurrences)
        & (available.n_sequences >= min_sequences)
        & (available.sequence_prevalence >= min_prevalence)
    ].copy()
    if motif_lengths is not None:
        selected = selected.loc[selected.motif_length.isin(motif_lengths)]
    selected = _sort_overall(selected, rank_by)
    if top_n is not None and len(selected) > top_n:
        selected = (
            selected.loc[selected[rank_by] >= selected.iloc[top_n - 1][rank_by]].copy()
            if ties == "include"
            else selected.iloc[:top_n].copy()
        )
    selected = selected.reset_index(drop=True)
    ids = selected.motif_id.tolist()
    by = sm.by_sequence.loc[sm.by_sequence.motif_id.isin(ids)].copy()
    if len(by):
        mr = {m: i for i, m in enumerate(ids)}
        sr = {s: i for i, s in enumerate(sm.sequences.sequence_id)}
        by = (
            by.assign(__m=by.motif_id.map(mr), __s=by.sequence_id.map(sr))
            .sort_values(["__m", "__s"], kind="stable")
            .drop(columns=["__m", "__s"])
            .reset_index(drop=True)
        )
    settings = {
        "min_occurrences": min_occurrences,
        "min_sequences": min_sequences,
        "min_prevalence": min_prevalence,
        "motif_lengths": motif_lengths,
        "top_n": top_n,
        "rank_by": rank_by,
        "ties": ties,
    }
    return MotifFilterResult(
        selected,
        by,
        sm.sequences,
        sm.state_dictionary,
        sm.audit,
        sm.status,
        sm.mapping,
        sm.extraction_settings,
        settings,
        len(available),
        len(selected),
    )


def format_sequence_motifs(
    x: Any,
    digits: int = 3,
    prevalence: str = "proportion",
    include_rank: bool = True,
    rank_by: str = "sequence_prevalence",
    ties: str = "min",
    include_ids: bool = True,
) -> FormattedTableResult:
    digits = _whole(digits, "digits", 0) or 0
    if digits > 15:
        raise ValidationError("`digits` must not exceed 15.")
    _assert_flag(include_rank, "include_rank")
    _assert_flag(include_ids, "include_ids")
    prevalence = _choice(prevalence, ["proportion", "percent"], "prevalence")
    rank_by = _choice(rank_by, ["sequence_prevalence", "n_occurrences", "n_sequences"], "rank_by")
    ties = _choice(ties, ["min", "first"], "ties")
    sm = _as_summary(x)
    table = _sort_overall(sm.overall.copy(), rank_by)
    if include_rank:
        if ties == "first":
            table["rank"] = np.arange(1, len(table) + 1, dtype=int)
        else:
            table["rank"] = table[rank_by].rank(method="min", ascending=False).astype(int)
    if len(table):
        if prevalence == "percent":
            table["sequence_prevalence"] *= 100
            table["occurrence_share"] *= 100
        for col in [
            "sequence_prevalence",
            "occurrence_share",
            "mean_occurrences_per_sequence",
            "mean_occurrences_when_present",
        ]:
            table[col] = table[col].round(digits)
    if prevalence == "percent":
        table = table.rename(
            columns={
                "sequence_prevalence": "sequence_prevalence_percent",
                "occurrence_share": "occurrence_share_percent",
            }
        )
    if not include_ids:
        table = table.drop(columns=["motif_id", "motif_key"])
    front = (
        (["rank"] if include_rank else [])
        + (["motif_id", "motif_key"] if include_ids else [])
        + ["motif", "motif_length", "n_occurrences", "n_sequences"]
    )
    table = table[front + [c for c in table.columns if c not in front]].reset_index(drop=True)
    return FormattedTableResult(
        table,
        sm.audit,
        sm.status,
        sm.mapping,
        {
            "digits": digits,
            "prevalence": prevalence,
            "include_rank": include_rank,
            "rank_by": rank_by,
            "ties": ties,
            "include_ids": include_ids,
        },
    )
