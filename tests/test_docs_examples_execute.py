from __future__ import annotations

import matplotlib
import pandas as pd

matplotlib.use("Agg")

import gp3sequencespy as g


def _demo() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["p1"] * 5 + ["p2"] * 5 + ["p3"] * 5,
            "sequence_order": list(range(1, 6)) * 3,
            "state": list("ABCBA") + list("ABCCA") + list("ACBCA"),
            "group": ["control"] * 10 + ["treatment"] * 5,
        }
    )


def test_quickstart_core_pipeline_executes():
    data = _demo()
    prepared = g.prepare_sequence_data(data, "sequence_id", "sequence_order", "state")
    assert prepared.data is not None
    states = g.summarise_sequence_states(prepared.data, "sequence_id", "sequence_order", "state")
    transitions = g.summarise_sequence_transitions(
        prepared.data, "sequence_id", "sequence_order", "state"
    )
    distance = g.compute_sequence_distance(prepared.data, method="levenshtein")
    clustering = g.cluster_sequences(distance, k=2)
    assert len(states.by_sequence) > 0
    assert len(transitions.by_sequence) > 0
    assert distance.matrix.shape == (3, 3)
    assert len(clustering.assignments) == 3


def test_plot_gallery_core_examples_execute():
    data = _demo()
    g.plot_sequence_index(data)
    g.plot_sequence_state_distribution(data)
    distance = g.compute_sequence_distance(data)
    g.plot_sequence_distance_heatmap(distance)
    network = g.create_transition_network(data)
    g.plot_transition_network(network)
