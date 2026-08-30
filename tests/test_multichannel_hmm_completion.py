from __future__ import annotations

from types import SimpleNamespace

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from gp3sequencespy import multichannel_hmm
from gp3sequencespy._exceptions import ValidationError


def _data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s1", "s2", "s2", "s2"],
            "sequence_order": [1, 2, 3, 1, 2, 3],
            "gaze": ["left", "right", "left", "right", "left", "right"],
            "event": ["view", "click", "view", "click", "view", "click"],
        }
    )


def test_multichannel_input_wrapper_validation_and_symbol_level_paths():
    data = _data()
    wrapped = SimpleNamespace(data=data)
    parsed = multichannel_hmm._input(wrapped, "sequence_id", "sequence_order", ["gaze", "event"])
    assert parsed["channel_cols"] == ["gaze", "event"]

    with pytest.raises(ValidationError, match="data frame"):
        multichannel_hmm._input(object(), "sequence_id", "sequence_order", ["gaze", "event"])
    with pytest.raises(ValidationError, match="Missing channel columns"):
        multichannel_hmm._input(data, "sequence_id", "sequence_order", ["gaze", "missing"])

    blank = data.copy()
    blank.loc[0, "event"] = ""
    with pytest.raises(ValidationError, match="contains missing, blank"):
        multichannel_hmm._input(blank, "sequence_id", "sequence_order", ["gaze", "event"])

    with pytest.raises(ValidationError, match="one list element per channel"):
        multichannel_hmm._input(
            data,
            "sequence_id",
            "sequence_order",
            ["gaze", "event"],
            symbol_levels=[["left", "right"]],
        )

    mapped = multichannel_hmm._input(
        data,
        "sequence_id",
        "sequence_order",
        ["gaze", "event"],
        symbol_levels={"gaze": ["right", "left"], "event": ["click", "view"]},
    )
    assert mapped["symbols"]["gaze"] == ["right", "left"]

    categorical = data.copy()
    categorical["gaze"] = pd.Categorical(
        categorical["gaze"], categories=["right", "left"], ordered=True
    )
    cat = multichannel_hmm._input(
        categorical, "sequence_id", "sequence_order", ["gaze", "event"]
    )
    assert cat["symbols"]["gaze"] == ["right", "left"]

    with pytest.raises(ValidationError, match="Invalid symbol levels"):
        multichannel_hmm._input(
            data,
            "sequence_id",
            "sequence_order",
            ["gaze", "event"],
            symbol_levels={"gaze": ["left", "left"], "event": ["view", "click"]},
        )
    with pytest.raises(ValidationError, match="do not cover"):
        multichannel_hmm._input(
            data,
            "sequence_id",
            "sequence_order",
            ["gaze", "event"],
            symbol_levels={"gaze": ["left"], "event": ["view", "click"]},
        )


def test_multichannel_fit_initialisation_and_probability_guards():
    data = _data()
    kwargs = dict(
        data=data,
        n_states=2,
        channel_cols=["gaze", "event"],
        max_iter=1,
        seed=3,
    )
    with pytest.raises(ValidationError, match="state_names"):
        multichannel_hmm.fit_multichannel_sequence_hmm(**kwargs, state_names=["x", "x"])
    with pytest.raises(ValidationError, match="initial_probs"):
        multichannel_hmm.fit_multichannel_sequence_hmm(**kwargs, initial_probs=[1.0])
    with pytest.raises(ValidationError, match="transition_probs"):
        multichannel_hmm.fit_multichannel_sequence_hmm(
            **kwargs, transition_probs=[[1.0, 0.0]]
        )
    with pytest.raises(ValidationError, match="one matrix per channel"):
        multichannel_hmm.fit_multichannel_sequence_hmm(
            **kwargs, emission_probs=[np.ones((2, 2))]
        )
    with pytest.raises(ValidationError, match="Invalid emission probabilities"):
        multichannel_hmm.fit_multichannel_sequence_hmm(
            **kwargs,
            emission_probs={
                "gaze": np.ones((2, 1)),
                "event": np.ones((2, 2)),
            },
        )

    fitted = multichannel_hmm.fit_multichannel_sequence_hmm(
        **kwargs,
        state_names=["low", "high"],
        initial_probs=[0.6, 0.4],
        transition_probs=[[0.8, 0.2], [0.3, 0.7]],
        emission_probs=[
            [[0.7, 0.3], [0.2, 0.8]],
            [[0.6, 0.4], [0.3, 0.7]],
        ],
        keep_posteriors=True,
    )
    assert fitted.posteriors is not None
    assert len(fitted.posteriors) == 2
    assert fitted.state_names == ["low", "high"]


def test_multichannel_single_observation_sequences_cover_no_transition_counts():
    data = pd.DataFrame(
        {
            "sequence_id": ["s1", "s2"],
            "sequence_order": [1, 1],
            "gaze": ["left", "right"],
            "event": ["view", "click"],
        }
    )
    model = multichannel_hmm.fit_multichannel_sequence_hmm(
        data,
        2,
        ["gaze", "event"],
        max_iter=1,
        seed=7,
    )
    assert model.n_observations == 2
    assert np.allclose(model.transition_probs.sum(axis=1), 1.0)


def test_multichannel_decode_summary_and_plot_paths():
    model = multichannel_hmm.fit_multichannel_sequence_hmm(
        _data(),
        2,
        ["gaze", "event"],
        max_iter=2,
        tolerance=1.0,
        seed=11,
    )

    with pytest.raises(ValidationError, match="fit_multichannel"):
        multichannel_hmm.decode_multichannel_sequence_states(object())
    with pytest.raises(ValidationError, match="Invalid method"):
        multichannel_hmm.decode_multichannel_sequence_states(model, method="bad")

    posterior = multichannel_hmm.decode_multichannel_sequence_states(model, method="posterior")
    assert posterior.decoding_method.eq("posterior").all()

    external = _data().copy()
    external["sequence_id"] = external["sequence_id"].map({"s1": "x1", "s2": "x2"})
    decoded = multichannel_hmm.decode_multichannel_sequence_states(
        model,
        data=external,
        channel_cols=["gaze", "event"],
        method="viterbi",
    )
    assert set(decoded.sequence_id) == {"x1", "x2"}

    with pytest.raises(ValidationError, match="fit_multichannel"):
        multichannel_hmm.summarise_multichannel_sequence_hmm(object())
    summary = multichannel_hmm.summarise_multichannel_sequence_hmm(model)
    assert set(summary) == {"fit", "initial", "transition", "emission"}

    with pytest.raises(ValidationError, match="fit_multichannel"):
        multichannel_hmm.plot_multichannel_sequence_hmm(object())
    with pytest.raises(ValidationError, match="Unknown channel"):
        multichannel_hmm.plot_multichannel_sequence_hmm(model, channel="missing")

    matrix = multichannel_hmm.plot_multichannel_sequence_hmm(model)
    assert matrix.shape == model.emission_probs[model.channel_names[0]].shape
