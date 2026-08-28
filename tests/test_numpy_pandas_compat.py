import pandas as pd

from gp3sequencespy import create_transition_network, detect_transition_communities


def test_community_detection_works_with_pandas_copy_on_write():
    data = pd.DataFrame(
        {
            "sequence_id": ["s1"] * 4 + ["s2"] * 4,
            "sequence_order": [1, 2, 3, 4] * 2,
            "state": ["A", "B", "A", "C", "A", "C", "B", "C"],
        }
    )
    with pd.option_context("mode.copy_on_write", True):
        network = create_transition_network(data, normalise="from")
        first = detect_transition_communities(network, seed=9)
        second = detect_transition_communities(network, seed=9)
    pd.testing.assert_frame_equal(first, second)
