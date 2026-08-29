from __future__ import annotations

import io

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

import gp3sequencespy as g
from gp3sequencespy._exceptions import ValidationError


def _distance_frame(name: str, coordinates: np.ndarray) -> pd.DataFrame:
    matrix = squareform(pdist(coordinates, metric="euclidean"))
    ids = [f"{name}_s{i + 1}" for i in range(len(coordinates))]
    return pd.DataFrame(matrix, index=ids, columns=ids)


def test_r_centroid_and_median_hclust_partitions_match_oracle_regressions():
    f1 = _distance_frame(
        "f1",
        np.array(
            [
                [0.00, 0.00],
                [0.73, 0.19],
                [2.11, 1.37],
                [3.94, 0.42],
                [5.28, 2.61],
                [7.63, 0.87],
                [9.17, 3.42],
                [11.83, 1.71],
            ]
        ),
    )

    median = g.cluster_sequences(f1, 2, method="hierarchical", linkage="median")
    assert median.assignments.tolist() == [1, 1, 1, 1, 1, 1, 1, 2]

    centroid = g.cluster_sequences(f1, 4, method="hierarchical", linkage="centroid")
    assert centroid.assignments.tolist() == [1, 1, 1, 1, 2, 2, 3, 4]
    assert centroid.assignments.nunique() == 4


def test_r_ward_d_and_ward_d2_are_distinct_and_match_oracle_regression():
    f2 = _distance_frame(
        "f2",
        np.array(
            [
                [0.13, 1.29, 2.71],
                [1.07, 3.91, 0.42],
                [2.83, 0.31, 4.77],
                [4.26, 2.14, 1.18],
                [5.92, 4.63, 3.09],
                [7.44, 1.73, 5.82],
                [8.69, 3.36, 0.77],
                [10.31, 0.94, 2.46],
                [12.08, 5.17, 4.11],
            ]
        ),
    )

    ward_d = g.cluster_sequences(f2, 4, method="hierarchical", linkage="ward.D")
    ward_d2 = g.cluster_sequences(f2, 4, method="hierarchical", linkage="ward.D2")

    assert ward_d.assignments.tolist() == [1, 2, 1, 2, 2, 3, 3, 3, 4]
    assert ward_d2.assignments.tolist() == [1, 2, 1, 2, 2, 3, 4, 4, 4]


def test_r_hierarchical_medoid_tie_resolution_matches_row_sums_oracle():
    f3 = _distance_frame(
        "f3",
        np.array([[0.0], [0.61], [1.82], [3.47], [5.93], [8.74], [12.16], [16.91], [22.37]]),
    )

    # Exercise the same decimal round-trip used by the cross-language oracle.
    # Pandas' default fast parser can differ by one ULP from R's decimal
    # conversion, which is enough to flip an otherwise tied medoid.
    csv_text = f3.reset_index(names="sequence_id").to_csv(
        index=False,
        float_format="%.17g",
    )
    parsed = pd.read_csv(io.StringIO(csv_text), float_precision="round_trip")
    parsed = parsed.set_index("sequence_id")

    expected = {
        2: ["f3_s3", "f3_s8"],
        3: ["f3_s3", "f3_s7", "f3_s9"],
        4: ["f3_s3", "f3_s5", "f3_s7", "f3_s9"],
    }
    for k, medoids in expected.items():
        fit = g.cluster_sequences(parsed, k, method="hierarchical", linkage="complete")
        assert fit.medoids == medoids

    single = g.cluster_sequences(parsed, 4, method="hierarchical", linkage="single")
    assert single.medoids == ["f3_s3", "f3_s7", "f3_s8", "f3_s9"]


def test_r_hclust_members_argument_is_used_and_validated():
    matrix = np.array(
        [
            [0.0, 2.221, 1.897, 2.095, 1.098],
            [2.221, 0.0, 1.378, 4.381, 2.687],
            [1.897, 1.378, 0.0, 1.192, 3.136],
            [2.095, 4.381, 1.192, 0.0, 2.797],
            [1.098, 2.687, 3.136, 2.797, 0.0],
        ]
    )
    ids = [f"s{i + 1}" for i in range(5)]
    distance = pd.DataFrame(matrix, index=ids, columns=ids)

    unweighted = g.cluster_sequences(distance, 2, linkage="average")
    weighted = g.cluster_sequences(
        distance,
        2,
        linkage="average",
        members=[20, 1, 1, 1, 1],
    )

    unweighted_same = (
        unweighted.assignments.to_numpy()[:, None] == unweighted.assignments.to_numpy()[None, :]
    )
    weighted_same = (
        weighted.assignments.to_numpy()[:, None] == weighted.assignments.to_numpy()[None, :]
    )
    assert not np.array_equal(unweighted_same, weighted_same)

    with np.testing.assert_raises(ValidationError):
        g.cluster_sequences(distance, 2, linkage="average", members=[1, 1])
