from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy import networks
from gp3sequencespy._exceptions import ValidationError


def _data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1"] * 4 + ["s2"] * 4,
            "sequence_order": [1, 2, 3, 4] * 2,
            "state": list("AABC") + list("ABCA"),
        }
    )


def _empty_network(order: int = 1) -> pd.DataFrame:
    out = pd.DataFrame(
        columns=[
            "group_key",
            "context",
            "from_state",
            "to_state",
            "count",
            "weight",
            "sequence_count",
            "sequence_prevalence",
        ]
    )
    out.attrs.update(
        gp3_class="gp3_transition_network",
        group_cols=[],
        settings={
            "order": order,
            "normalise": "count",
            "include_self": True,
            "smoothing": 0,
        },
    )
    return out


def _manual_network(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    out = pd.DataFrame(
        [
            {
                "group_key": "__all__",
                "context": a,
                "from_state": a,
                "to_state": b,
                "count": w,
                "weight": w,
                "sequence_count": 1,
                "sequence_prevalence": 1.0,
            }
            for a, b, w in rows
        ]
    )
    out.attrs.update(
        gp3_class="gp3_transition_network",
        group_cols=[],
        settings={
            "order": 1,
            "normalise": "count",
            "include_self": True,
            "smoothing": 0,
        },
    )
    return out


def test_create_transition_network_validation_empty_skip_and_global_paths():
    with pytest.raises(ValidationError, match="normalise"):
        g.create_transition_network(_data(), normalise="bad")

    short = pd.DataFrame({"sequence_id": ["s1"], "sequence_order": [1], "state": ["A"]})
    empty = g.create_transition_network(short, order=1)
    assert empty.empty
    assert empty.attrs["gp3_class"] == "gp3_transition_network"

    global_net = g.create_transition_network(_data(), normalise="global")
    assert np.isclose(global_net.weight.sum(), 1.0)


def test_graph_matrix_and_dijkstra_validation_and_disconnected_paths():
    with pytest.raises(ValidationError, match="create_transition_network"):
        networks._graph_matrix(pd.DataFrame())
    with pytest.raises(ValidationError, match="first-order"):
        networks._graph_matrix(_empty_network(order=2))

    cost = np.array(
        [
            [0.0, 1.0, np.inf],
            [np.inf, 0.0, np.inf],
            [np.inf, np.inf, 0.0],
        ]
    )
    distance = networks._dijkstra(cost, 0)
    assert distance[0] == 0
    assert distance[1] == 1
    assert np.isinf(distance[2])


def test_centrality_empty_dangling_and_pagerank_normal_exit_paths():
    assert g.summarise_transition_centrality(_empty_network()).empty

    dangling = _manual_network([("A", "B", 1.0)])
    result = g.summarise_transition_centrality(
        dangling, pagerank_max_iter=1, pagerank_tolerance=0.0
    )
    assert set(result.state) == {"A", "B"}
    assert np.isclose(result.pagerank.sum(), 1.0)

    all_dangling = _manual_network([("A", "A", 0.0), ("B", "B", 0.0)])
    dangling_result = g.summarise_transition_centrality(all_dangling)
    assert np.isclose(dangling_result.pagerank.sum(), 1.0)


def test_community_validation_empty_isolated_and_normal_exit_paths():
    with pytest.raises(ValidationError, match="community method"):
        g.detect_transition_communities(_manual_network([("A", "B", 1.0)]), method="bad")
    assert g.detect_transition_communities(_empty_network()).empty

    isolated = _manual_network([("A", "A", 1.0), ("B", "B", 0.0)])
    communities = g.detect_transition_communities(
        isolated, method="label_propagation", max_iter=1, seed=1
    )
    assert set(communities.state) == {"A", "B"}

    changed = _manual_network([("A", "B", 1.0), ("B", "B", 0.0)])
    exhausted = g.detect_transition_communities(
        changed, method="label_propagation", max_iter=1, seed=0
    )
    assert set(exhausted.state) == {"A", "B"}


def test_predict_model_guard_and_bootstrap_no_transition_guard():
    with pytest.raises(ValidationError, match="fit_higher_order_transition_model"):
        g.predict_next_state(object(), ["A"])

    short = pd.DataFrame({"sequence_id": ["s1"], "sequence_order": [1], "state": ["A"]})
    with pytest.raises(ValidationError, match="No first-order transitions"):
        g.bootstrap_transition_network(short, n_boot=1)


def test_dijkstra_defensive_empty_available_guard(monkeypatch):
    original = networks.np.flatnonzero
    calls = {"n": 0}

    def empty_once(values):
        calls["n"] += 1
        if calls["n"] == 1:
            return np.array([], dtype=int)
        return original(values)

    monkeypatch.setattr(networks.np, "flatnonzero", empty_once)
    result = networks._dijkstra(np.array([[0.0]]), 0)
    assert result.tolist() == [0.0]


def test_betweenness_defensive_zero_sigma_predecessor_guard(monkeypatch):
    original_zeros = networks.np.zeros
    calls = {"n": 0}

    class FrozenAfterFirstWrite(np.ndarray):
        def __new__(cls, n):
            obj = original_zeros(n).view(cls)
            obj._writes = 0
            return obj

        def __array_finalize__(self, obj):
            if obj is not None:
                self._writes = getattr(obj, "_writes", 0)

        def __setitem__(self, key, value):
            self._writes += 1
            if self._writes == 1:
                return super().__setitem__(key, value)
            return None

    def selective_zeros(shape, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] in {2, 4} and isinstance(shape, int):
            return FrozenAfterFirstWrite(shape)
        return original_zeros(shape, *args, **kwargs)

    monkeypatch.setattr(networks.np, "zeros", selective_zeros)
    score = networks._betweenness(np.array([[False, True], [False, False]]))
    assert score.shape == (2,)
