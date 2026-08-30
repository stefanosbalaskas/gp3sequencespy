from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import analysis_audit


def test_family_dispatch_and_primary_class(monkeypatch):
    class Distance:
        pass

    class Clustering:
        pass

    class Bootstrap:
        pass

    class Ensemble:
        pass

    class HigherOrder:
        pass

    class HMM:
        pass

    class Multichannel:
        pass

    class Covariate:
        pass

    class Prepared:
        pass

    class Validation:
        pass

    monkeypatch.setattr(analysis_audit, "SequenceDistanceResult", Distance)
    monkeypatch.setattr(analysis_audit, "SequenceClustering", Clustering)
    monkeypatch.setattr(analysis_audit, "SequenceClusterBootstrap", Bootstrap)
    monkeypatch.setattr(analysis_audit, "SequenceClusterEnsemble", Ensemble)
    monkeypatch.setattr(analysis_audit, "HigherOrderTransitionModel", HigherOrder)
    monkeypatch.setattr(analysis_audit, "HMMResult", HMM)
    monkeypatch.setattr(analysis_audit, "MultichannelSequenceHMM", Multichannel)
    monkeypatch.setattr(analysis_audit, "CovariateSequenceHMM", Covariate)
    monkeypatch.setattr(analysis_audit, "PrepareResult", Prepared)
    monkeypatch.setattr(analysis_audit, "ValidationResult", Validation)

    assert analysis_audit._family(Distance()) == "distance"
    assert analysis_audit._family(Clustering()) == "clustering"
    assert analysis_audit._family(Bootstrap()) == "cluster_bootstrap"
    assert analysis_audit._family(Ensemble()) == "cluster_ensemble"

    network = pd.DataFrame({"context": ["A"], "to_state": ["B"], "count": [1], "weight": [1.0]})
    network.attrs["gp3_class"] = "gp3_transition_network"
    assert analysis_audit._family(network) == "transition_network"
    assert analysis_audit._primary_class(network) == "gp3_transition_network"

    assert analysis_audit._family(HigherOrder()) == "higher_order_transition"
    assert analysis_audit._family(HMM()) == "hmm"
    assert analysis_audit._family(Multichannel()) == "multichannel_hmm"
    assert analysis_audit._family(Covariate()) == "covariate_hmm"
    assert analysis_audit._family(Prepared()) == "prepared_sequence_data"
    assert analysis_audit._family(Validation()) == "sequence_validation"
    assert analysis_audit._family(object()) == "generic"
    assert analysis_audit._primary_class(SimpleNamespace()) == "SimpleNamespace"


def test_sequence_id_state_method_settings_and_seed_helpers(monkeypatch):
    class Distance:
        pass

    class Clustering:
        pass

    class Ensemble:
        pass

    class HMM:
        pass

    class Prepared:
        pass

    monkeypatch.setattr(analysis_audit, "SequenceDistanceResult", Distance)
    monkeypatch.setattr(analysis_audit, "SequenceClustering", Clustering)
    monkeypatch.setattr(analysis_audit, "SequenceClusterEnsemble", Ensemble)
    monkeypatch.setattr(analysis_audit, "HMMResult", HMM)
    monkeypatch.setattr(analysis_audit, "PrepareResult", Prepared)

    distance = Distance()
    distance.labels = [1, "s2"]
    distance.sequences = pd.DataFrame({"state": ["B", "A", "B"]})
    assert analysis_audit._sequence_ids(distance) == ["1", "s2"]
    assert analysis_audit._state_levels(distance) == ["B", "A"]

    clustering = Clustering()
    clustering.assignments = pd.Series([1, 2], index=["s1", "s2"])
    assert analysis_audit._sequence_ids(clustering) == ["s1", "s2"]

    ensemble = Ensemble()
    ensemble.assignments = pd.Series([1, 1], index=["e1", "e2"])
    assert analysis_audit._sequence_ids(ensemble) == ["e1", "e2"]

    hmm = HMM()
    hmm.training_data = pd.DataFrame(
        {"sequence_id": ["h1", "h1", "h2"], "state": ["A", "B", "A"]}
    )
    assert analysis_audit._sequence_ids(hmm) == ["h1", "h2"]
    assert analysis_audit._state_levels(hmm) == ["A", "B"]

    generic_training = SimpleNamespace(
        training_data=pd.DataFrame({"sequence_id": ["t1", "t1", "t2"], "state": ["C", "D", "C"]})
    )
    assert analysis_audit._sequence_ids(generic_training) == ["t1", "t2"]
    assert analysis_audit._state_levels(generic_training) == ["C", "D"]

    generic_data = SimpleNamespace(data=pd.DataFrame({"sequence_id": ["d1", "d2"]}))
    assert analysis_audit._sequence_ids(generic_data) == ["d1", "d2"]

    prepared = Prepared()
    prepared.data = pd.DataFrame({"sequence_id": ["p1", "p1", "p2"]})
    assert analysis_audit._sequence_ids(prepared) == ["p1", "p2"]

    assert analysis_audit._sequence_ids(object()) == []
    assert analysis_audit._state_levels(SimpleNamespace(state_levels=["A", 2])) == ["A", "2"]
    assert analysis_audit._state_levels(object()) == []

    assert analysis_audit._method(SimpleNamespace(method="custom"), "generic") == "custom"
    assert analysis_audit._method(SimpleNamespace(method=None), "hmm") == "categorical_hmm"
    assert (
        analysis_audit._method(SimpleNamespace(method=None), "transition_network")
        == "transition_network"
    )
    assert analysis_audit._method(SimpleNamespace(method=None), "generic") is None

    assert analysis_audit._settings(SimpleNamespace(settings={"seed": 3})) == {"seed": 3}
    frame = pd.DataFrame({"x": [1]})
    frame.attrs["settings"] = {"order": 2}
    assert analysis_audit._settings(frame) == {"order": 2}

    fallback = SimpleNamespace(k=2, seed=7, converged=True)
    assert analysis_audit._settings(fallback) == {"k": 2, "seed": 7, "converged": True}
    assert analysis_audit._seed(SimpleNamespace(seed=11)) == 11
    assert analysis_audit._seed(SimpleNamespace(settings={"seed": 13})) == 13


def test_distance_audit_validation_covers_all_failure_modes():
    invalid_numeric = SimpleNamespace(matrix="not numeric", labels=[])
    assert analysis_audit._validate_distance(invalid_numeric, 1e-8)[0]["code"] == "invalid_distance_matrix"

    non_square = SimpleNamespace(matrix=np.array([[0.0, 1.0, 2.0]]), labels=["s1"])
    assert analysis_audit._validate_distance(non_square, 1e-8)[0]["code"] == "invalid_distance_matrix"

    non_finite = SimpleNamespace(
        matrix=np.array([[0.0, np.nan], [np.nan, 0.0]]), labels=["s1", "s2"]
    )
    assert "non_finite_distance" in {
        issue["code"] for issue in analysis_audit._validate_distance(non_finite, 1e-8)
    }

    negative = SimpleNamespace(
        matrix=np.array([[0.0, -1.0], [-1.0, 0.0]]), labels=["s1", "s2"]
    )
    assert "negative_distance" in {
        issue["code"] for issue in analysis_audit._validate_distance(negative, 1e-8)
    }

    nonzero_diagonal = SimpleNamespace(
        matrix=np.array([[1.0, 0.0], [0.0, 0.0]]), labels=["s1", "s2"]
    )
    assert "nonzero_distance_diagonal" in {
        issue["code"] for issue in analysis_audit._validate_distance(nonzero_diagonal, 1e-8)
    }

    asymmetric = SimpleNamespace(
        matrix=np.array([[0.0, 1.0], [2.0, 0.0]]), labels=["s1", "s2"]
    )
    assert "asymmetric_distance" in {
        issue["code"] for issue in analysis_audit._validate_distance(asymmetric, 1e-8)
    }

    bad_ids = SimpleNamespace(
        matrix=np.array([[0.0, 1.0], [1.0, 0.0]]), labels=["", ""]
    )
    assert "distance_identifiers_invalid" in {
        issue["code"] for issue in analysis_audit._validate_distance(bad_ids, 1e-8)
    }

    good = SimpleNamespace(
        matrix=np.array([[0.0, 1.0], [1.0, 0.0]]), labels=["s1", "s2"]
    )
    assert analysis_audit._validate_distance(good, 1e-8) == []


def test_family_specific_validation_paths():
    for assignments in (
        None,
        pd.Series(dtype=int),
        pd.Series([1, 2], index=["dup", "dup"]),
    ):
        issues = analysis_audit._validate(
            SimpleNamespace(assignments=assignments), "clustering", 1e-8
        )
        assert issues[0]["code"] == "invalid_clustering_assignments"

    valid_assignments = SimpleNamespace(assignments=pd.Series([1, 2], index=["s1", "s2"]))
    assert analysis_audit._validate(valid_assignments, "cluster_ensemble", 1e-8) == []

    missing_transition_columns = pd.DataFrame({"context": ["A"]})
    issues = analysis_audit._validate(missing_transition_columns, "transition_network", 1e-8)
    assert issues[0]["code"] == "transition_columns_missing"

    bad_transition_values = pd.DataFrame(
        {"context": ["A"], "to_state": ["B"], "count": ["bad"], "weight": [1.0]}
    )
    issues = analysis_audit._validate(bad_transition_values, "transition_network", 1e-8)
    assert issues[0]["code"] == "transition_values_invalid"

    good_transition = pd.DataFrame(
        {"context": ["A"], "to_state": ["B"], "count": [1], "weight": [1.0]}
    )
    assert analysis_audit._validate(good_transition, "transition_network", 1e-8) == []

    bad_initial = SimpleNamespace(initial=np.array([np.nan]), transition=np.eye(1))
    issues = analysis_audit._validate(bad_initial, "hmm", 1e-8)
    assert issues[0]["field"] == "initial"

    bad_transition = SimpleNamespace(initial=None, transition=np.array([[np.nan]]))
    issues = analysis_audit._validate(bad_transition, "multichannel_hmm", 1e-8)
    assert issues[0]["field"] == "transition"

    good_hmm = SimpleNamespace(initial=np.array([1.0]), transition=np.array([[1.0]]))
    assert analysis_audit._validate(good_hmm, "covariate_hmm", 1e-8) == []

    invalid_status = SimpleNamespace(status="unknown")
    issues = analysis_audit._validate(invalid_status, "prepared_sequence_data", 1e-8)
    assert issues[0]["code"] == "invalid_status"
    assert analysis_audit._validate(SimpleNamespace(status="review"), "sequence_validation", 1e-8) == []
    assert analysis_audit._validate(object(), "generic", 1e-8) == []


def test_audit_review_provenance_and_strict_failure(monkeypatch):
    marker = object()
    monkeypatch.setattr(analysis_audit, "_family", lambda x: "cluster_bootstrap")
    monkeypatch.setattr(analysis_audit, "_sequence_ids", lambda x: [])
    monkeypatch.setattr(analysis_audit, "_state_levels", lambda x: [])
    review = analysis_audit.audit_sequence_analysis(marker)
    assert review.status == "review"
    assert review.issues.code.tolist() == ["sequence_ids_not_recoverable"]
    assert review.provenance["family"] == "cluster_bootstrap"
    assert review.summary.loc[0, "n_sequence_ids"] == 0

    monkeypatch.setattr(
        analysis_audit,
        "_validate",
        lambda x, family, tolerance: [
            analysis_audit._issue("forced", "error", "x", "forced failure")
        ],
    )
    with pytest.raises(ValueError, match="Sequence-analysis audit failed: forced failure"):
        analysis_audit.audit_sequence_analysis(marker, strict=True)


def test_normalisation_equality_and_row_helpers():
    @dataclass
    class Box:
        value: Any

    frame = pd.DataFrame({"x": [1, 2]}, index=[10, 11])
    series = pd.Series([3, 4], index=[20, 21])
    array = np.array([5, 6])

    assert analysis_audit._normalise_for_compare(frame) == (("x",), ("10", "11"), [[1], [2]])
    assert analysis_audit._normalise_for_compare(series) == (("20", "21"), [3, 4])
    assert analysis_audit._normalise_for_compare(array) == [5, 6]
    assert analysis_audit._normalise_for_compare(Box(array)) == {"value": [5, 6]}
    assert analysis_audit._normalise_for_compare({"x": (1, 2)}) == {"x": [1, 2]}
    assert analysis_audit._normalise_for_compare([array]) == [[5, 6]]
    assert analysis_audit._normalise_for_compare("x") == "x"

    assert analysis_audit._equal(1.0, 1.0 + 1e-10, 1e-8)
    assert analysis_audit._equal(np.array([1.0]), np.array([1.0 + 1e-10]), 1e-8)
    assert analysis_audit._equal(frame, frame.copy(), 1e-8)
    assert analysis_audit._equal(series, series.copy(), 1e-8)
    assert not analysis_audit._equal(frame, pd.DataFrame({"x": [9, 9]}), 1e-8)
    assert not analysis_audit._equal(series, pd.Series([9, 9], index=[20, 21]), 1e-8)
    assert analysis_audit._equal({"x": [1]}, {"x": [1]}, 1e-8)

    class ExplodingEquality:
        def __eq__(self, other):
            raise RuntimeError("boom")

    assert not analysis_audit._equal(ExplodingEquality(), ExplodingEquality(), 1e-8)
    assert analysis_audit._row("ids", ["a", "b"], ("a", "b"), True) == {
        "field": "ids",
        "x": "a | b",
        "y": "a | b",
        "equal": True,
    }
    assert analysis_audit._row("seed", 1, 2, False)["equal"] is False


def test_compare_contract_rows_without_value_comparison(monkeypatch):
    x = object()
    y = object()
    empty = pd.DataFrame(columns=["code", "severity", "field", "message"])
    summary = pd.DataFrame([{"status": "pass"}])
    xa = analysis_audit.SequenceAnalysisAudit(
        summary=summary,
        issues=empty,
        provenance={
            "method": "m1",
            "sequence_ids": ["s1"],
            "state_levels": ["A"],
            "seed": 1,
            "settings": {"k": 2},
        },
        contract={"family": "distance", "primary_class": "X"},
        status="pass",
    )
    ya = analysis_audit.SequenceAnalysisAudit(
        summary=summary,
        issues=empty,
        provenance={
            "method": "m2",
            "sequence_ids": ["s2"],
            "state_levels": ["B"],
            "seed": 2,
            "settings": {"k": 3},
        },
        contract={"family": "clustering", "primary_class": "Y"},
        status="pass",
    )

    monkeypatch.setattr(
        analysis_audit,
        "audit_sequence_analysis",
        lambda obj, tolerance=1e-8: xa if obj is x else ya,
    )
    result = analysis_audit.compare_sequence_analysis_results(x, y, compare_values=False)
    assert result.value_comparison is None
    assert result.all_equal is False
    assert result.comparisons.field.tolist() == [
        "family",
        "primary_class",
        "method",
        "sequence_ids",
        "state_levels",
        "seed",
        "settings",
    ]
    assert not result.comparisons["equal"].any()
