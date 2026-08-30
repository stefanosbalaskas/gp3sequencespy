from __future__ import annotations

import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy import adapters, motifs
from gp3sequencespy._exceptions import ValidationError


def test_summaries_numeric_ids_string_state_levels_and_empty_self_transitions():
    numeric_ids = pd.DataFrame(
        {
            "id": [2, 2, 1, 1],
            "order": [1, 2, 1, 2],
            "state": ["A", "B", "A", "B"],
        }
    )
    encoded = g.encode_sequence_data(numeric_ids, "id", "order", "state")
    assert encoded.data["sequence_id"].tolist() == ["1", "1", "2", "2"]

    with pytest.raises(ValidationError, match="omits observed states"):
        g.encode_sequence_data(
            numeric_ids,
            "id",
            "order",
            "state",
            state_levels="A",
        )

    self_only = pd.DataFrame(
        {
            "id": ["s1", "s1", "s2", "s2"],
            "order": [1, 2, 1, 2],
            "state": ["A", "A", "B", "B"],
        }
    )
    transitions = g.summarise_sequence_transitions(
        self_only,
        "id",
        "order",
        "state",
        include_self=False,
    )
    assert transitions.by_sequence.empty


def test_adapter_higher_order_rejection_and_explicit_mapping_paths():
    higher_order = pd.DataFrame(
        {
            "from_state": ["A"],
            "to_state": ["B"],
            "weight": [1.0],
            "count": [1],
            "sequence_count": [1],
            "sequence_prevalence": [1.0],
        }
    )
    higher_order.attrs["settings"] = {"order": 2}
    with pytest.raises(ValidationError, match="first-order"):
        adapters.as_igraph_transition_network(higher_order)

    frame = pd.DataFrame({"chosen": [1], "other": [2]})
    assert adapters._infer_column(frame, "chosen", ["other"], "test") == "chosen"

    data = pd.DataFrame(
        {
            "sid": ["s1", "s1"],
            "pos": [1, 2],
            "event": ["A", "B"],
            "milliseconds": [10.0, 20.0],
        }
    )
    prepared = adapters.prepare_gp3tools_sequences(
        data,
        sequence_id_col="sid",
        order_col="pos",
        state_col="event",
        duration_col="milliseconds",
    )
    assert prepared.data is not None
    assert prepared.data["duration"].tolist() == [10.0, 20.0]


def test_motif_summary_dispatch_invalid_inputs_and_first_tie_ranking():
    data = pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s1", "s2", "s2", "s2"],
            "sequence_order": [1, 2, 3, 1, 2, 3],
            "state": ["A", "B", "A", "A", "B", "C"],
        }
    )
    extraction = g.extract_sequence_ngrams(data, min_length=2, max_length=2)
    summary = motifs._as_summary(extraction)
    assert len(summary.overall) > 0

    with pytest.raises(ValidationError, match="motif extraction, summary, or filtered-motif"):
        motifs._as_summary(object())
    with pytest.raises(ValidationError, match="extract_sequence_ngrams"):
        motifs.summarise_sequence_motifs(object())

    formatted = g.format_sequence_motifs(extraction, ties="first", include_rank=True)
    assert "rank" in formatted.table.columns
    assert formatted.table["rank"].tolist() == list(range(1, len(formatted.table) + 1))
