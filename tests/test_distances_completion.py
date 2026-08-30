from __future__ import annotations

from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy import distances
from gp3sequencespy._exceptions import ValidationError


def _data(n_sequences: int = 5) -> pd.DataFrame:
    paths = [
        list("ABCA"),
        list("ABBA"),
        list("BACA"),
        list("CCAB"),
        list("CABA"),
    ]
    rows = []
    for i in range(n_sequences):
        sid = f"s{i + 1}"
        for order, state in enumerate(paths[i % len(paths)], 1):
            rows.append({"sequence_id": sid, "sequence_order": order, "state": state})
    return pd.DataFrame(rows)


def _distance(n_sequences: int = 5):
    return g.compute_sequence_distance(_data(n_sequences), method="lcs")


def test_distance_property_substitution_and_public_argument_guards():
    fit = g.cluster_sequences(_distance(), 2)
    pd.testing.assert_series_equal(fit.cluster, fit.assignments)

    with pytest.raises(ValidationError, match="array substitution matrix"):
        distances._substitution_df(np.eye(2), ["A", "B"])
    with pytest.raises(ValidationError, match="finite, non-negative"):
        distances._substitution_df(pd.DataFrame(), [])

    negative = pd.DataFrame(
        [[0.0, -1.0], [-1.0, 0.0]], index=["A", "B"], columns=["A", "B"]
    )
    with pytest.raises(ValidationError, match="finite, non-negative"):
        distances._substitution_df(negative, ["A", "B"])

    partial = pd.DataFrame(
        [[0.0, 1.0], [1.0, 0.0]], index=["A", "B"], columns=["A", "B"]
    )
    with pytest.raises(ValidationError, match="does not cover"):
        distances._substitution_df(partial, ["A", "B", "C"])

    with pytest.raises(ValidationError, match="distance method"):
        g.compute_sequence_distance(_data(), method="bad")
    with pytest.raises(ValidationError, match="normalisation"):
        g.compute_sequence_distance(_data(), normalise="bad")

    path = g.compute_sequence_distance(_data(), method="lcs", normalise="path_length")
    raw = g.compute_sequence_distance(_data(), method="lcs", normalise="none")
    assert np.all(path.matrix <= raw.matrix + 1e-12)


def test_exact_binary_rounding_edge_branches():
    assert distances._floor_log2_fraction(Fraction(5, 3)) == 0
    assert distances._floor_log2_fraction(Fraction(1, 3)) == -2
    rounded = distances._round_fraction_binary(Fraction(1025, 1), 2)
    assert isinstance(rounded, Fraction)
    assert rounded == Fraction(1024, 1)


def test_lance_williams_all_update_rules_with_members():
    matrix = np.array(
        [
            [0.0, 1.0, 4.0, 5.0],
            [1.0, 0.0, 3.0, 4.0],
            [4.0, 3.0, 0.0, 2.0],
            [5.0, 4.0, 2.0, 0.0],
        ]
    )
    for linkage in [
        "ward.D2",
        "single",
        "complete",
        "average",
        "mcquitty",
        "median",
        "centroid",
        "ward.D",
    ]:
        z = distances._r_lance_williams_members(
            matrix, linkage, [1.0, 2.0, 1.0, 3.0]
        )
        assert z.shape == (3, 4)
        assert np.isfinite(z).all()


def test_cluster_sequence_validation_paths_and_clara_kwargs():
    distance = _distance()
    with pytest.raises(ValidationError, match="Invalid clustering method"):
        g.cluster_sequences(distance, 2, method="bad")
    with pytest.raises(ValidationError, match="not a supported"):
        g.cluster_sequences(distance, 2, linkage="bad")
    with pytest.raises(ValidationError, match="smaller than"):
        g.cluster_sequences(distance, len(distance.labels))
    with pytest.raises(ValidationError, match="protected clustering arguments"):
        g.cluster_sequences(distance, 2, x=1)
    with pytest.raises(ValidationError, match="Unsupported hierarchical"):
        g.cluster_sequences(distance, 2, method="hierarchical", foo=1)
    with pytest.raises(ValidationError, match="Unsupported CLARA"):
        g.cluster_sequences(
            distance, 2, method="clara", samples=1, sampsize=4, foo=1
        )


def test_assignment_validation_paths():
    distance = _distance(4)
    ids = distance.labels
    with pytest.raises(ValidationError, match="named pandas Series"):
        distances._assignments_and_distance([1, 1, 2, 2], distance)

    duplicate = pd.Series(
        [1, 1, 2, 2], index=[ids[0], ids[0], ids[2], ids[3]]
    )
    with pytest.raises(ValidationError, match="unique sequence-ID"):
        distances._assignments_and_distance(duplicate, distance)

    mismatch = pd.Series([1, 1, 2, 2], index=[*ids[:3], "other"])
    with pytest.raises(ValidationError, match="identifiers must match"):
        distances._assignments_and_distance(mismatch, distance)

    one = pd.Series([1, 1, 1, 1], index=ids)
    with pytest.raises(ValidationError, match="At least two"):
        distances._assignments_and_distance(one, distance)


def test_bootstrap_and_stability_validation_low_pair_paths():
    distance = _distance(4)
    with pytest.raises(ValidationError, match="subsample"):
        g.bootstrap_sequence_clusters(distance, 4, n_boot=1, sample_fraction=1.0)
    with pytest.raises(ValidationError, match="bootstrap_sequence_clusters"):
        g.summarise_sequence_cluster_stability(object())

    original = g.cluster_sequences(distance, 2)
    ids = original.assignments.index.tolist()
    stability = pd.DataFrame(0.25, index=ids, columns=ids)
    np.fill_diagonal(stability.values, 1.0)
    boot = distances.SequenceClusterBootstrap(
        original=original,
        pairwise_stability=stability,
        evaluated_counts=pd.DataFrame(1, index=ids, columns=ids),
        iterations=pd.DataFrame(),
        overall=pd.DataFrame([{"mean_pairwise_stability": 0.25}]),
        settings={},
    )
    summary = g.summarise_sequence_cluster_stability(boot, threshold=0.8)
    assert not summary["low_stability_pairs"].empty
    assert (summary["low_stability_pairs"].stability < 0.8).all()


def test_cluster_ensemble_validation_paths():
    with pytest.raises(ValidationError, match="at least two"):
        g.create_sequence_cluster_ensemble(
            pd.Series([1, 2], index=["a", "b"]), k=2
        )

    valid = pd.Series([1, 1, 2], index=["a", "b", "c"])
    with pytest.raises(ValidationError, match="Every solution"):
        g.create_sequence_cluster_ensemble(valid, object(), k=2)

    mismatch = pd.Series([1, 1, 2], index=["a", "b", "d"])
    with pytest.raises(ValidationError, match="same sequence IDs"):
        g.create_sequence_cluster_ensemble(valid, mismatch, k=2)

    second = pd.Series([1, 2, 2], index=["a", "b", "c"])
    with pytest.raises(ValidationError, match="smaller than"):
        g.create_sequence_cluster_ensemble(valid, second, k=3)
