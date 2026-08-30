from __future__ import annotations

from types import SimpleNamespace

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

import gp3sequencespy as g
from gp3sequencespy import _advanced as adv
from gp3sequencespy import (
    adapters,
    analysis_audit,
    capabilities,
    inference,
    summaries,
    visualisations,
)
from gp3sequencespy import data as data_mod
from gp3sequencespy._exceptions import ValidationError
from gp3sequencespy._types import SequenceDistanceResult, ValidationResult


def _long() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sequence_id": ["s1", "s1", "s1", "s2", "s2", "s2"],
            "sequence_order": [1, 2, 3, 1, 2, 3],
            "state": ["A", "B", "A", "A", "C", "C"],
            "duration": [1.0, 2.0, 3.0, 1.5, 2.5, 1.0],
            "group": ["x", "x", "x", "y", "y", "y"],
            "unit": ["u1", "u1", "u1", "u2", "u2", "u2"],
        }
    )


def test_advanced_scalar_and_column_guards():
    with pytest.raises(ValidationError):
        adv.scalar_character(1, "x")
    assert adv.scalar_character(None, "x", allow_none=True) is None
    with pytest.raises(ValidationError):
        adv.scalar_logical(1, "flag")
    with pytest.raises(ValidationError):
        adv.match_cols(pd.DataFrame({"a": [1]}), ["missing"], "cols")
    with pytest.raises(ValidationError):
        adv.match_cols(pd.DataFrame({"a": [1]}), ["a", "a"], "cols")
    assert adv.match_cols(pd.DataFrame({"a": [1]}), None, "cols", allow_none=True) == []


def test_advanced_distance_helpers_cover_validation_and_ties():
    with pytest.raises(ValidationError):
        adv.validate_distance_matrix([[0, 1, 2]])
    with pytest.raises(ValidationError):
        adv.validate_distance_matrix([[0, np.nan], [np.nan, 0]])
    with pytest.raises(ValidationError):
        adv.validate_distance_matrix([[0, -1], [-1, 0]])
    with pytest.raises(ValidationError):
        adv.validate_distance_matrix([[1, 0], [0, 1]])
    with pytest.raises(ValidationError):
        adv.validate_distance_matrix([[0, 1], [2, 0]])
    arr, labels = adv.validate_distance_matrix([[0, 1], [1, 0]])
    np.testing.assert_allclose(arr, [[0, 1], [1, 0]])
    assert labels == ["1", "2"]

    assert adv.tie(["B", "A"], [1, 1], ["A", "B"], "first")["selected"] == "A"
    assert adv.tie(["B", "A"], [1, 1], ["A", "B"], "last")["selected"] == "B"
    assert adv.tie(["B", "A"], [1, 1], ["A", "B"], "missing")["selected"] is None
    assert adv.tie(["B", "A"], [1, 1], ["A", "B"], "all")["selected"] == "A | B"
    with pytest.raises(ValidationError):
        adv.tie(["A"], [1], ["A"], "bad")

    with pytest.raises(ValidationError):
        adv.edit_distance(["A"], ["B"], 1, 1, np.ones((2, 2)), None)
    matrix = pd.DataFrame([[0.0]], index=["A"], columns=["A"])
    with pytest.raises(ValidationError):
        adv.edit_distance(["A"], ["B"], 1, 1, matrix, ["A"])


def test_result_mapping_protocol_is_exercised():
    result = ValidationResult(
        valid=True,
        status="pass",
        n_errors=0,
        n_reviews=0,
        n_info=0,
        audit=pd.DataFrame(),
        mapping=pd.DataFrame(),
        n_rows=2,
        n_sequences=1,
        state_levels=["A"],
    )
    assert result["valid"] is True
    assert "status" in list(iter(result))
    assert len(result) == len(result.to_dict())


def test_data_helper_guards_and_value_formatting():
    with pytest.raises(ValidationError):
        data_mod._assert_column_name(None, "x")
    data_mod._assert_column_name(None, "x", allow_none=True)
    with pytest.raises(ValidationError):
        data_mod._normalize_cols(42, "metadata")
    with pytest.raises(ValidationError):
        data_mod._normalize_cols(["x", "x"], "metadata")
    assert data_mod._normalize_cols("x", "metadata") == ["x"]
    assert data_mod._value_text([]) is None
    assert data_mod._value_text([None, pd.NA, np.nan, "A"]) == "<NA> | <NA> | <NA> | A"
    assert data_mod._format_order_key("abc") == "abc"


def test_audit_sequence_data_error_and_review_paths():
    with pytest.raises(ValidationError):
        data_mod.audit_sequence_data([], "id", "order", "state")

    duplicate_cols = pd.DataFrame([[1, 2]], columns=["id", "id"])
    audit = data_mod.audit_sequence_data(duplicate_cols, "id", "order", "state")
    assert "duplicate_column_names" in set(audit.issue_code)

    missing = data_mod.audit_sequence_data(pd.DataFrame({"id": ["s1"]}), "id", "order", "state")
    assert "missing_required_column" in set(missing.issue_code)

    empty = pd.DataFrame(columns=["id", "order", "state"])
    assert "empty_data" in set(
        data_mod.audit_sequence_data(empty, "id", "order", "state").issue_code
    )

    bad = pd.DataFrame(
        {
            "id": ["s1", None, "s1", "s1"],
            "order": [2.0, 1.0, 2.0, np.inf],
            "state": ["A", "", "B", "Z"],
            "duration": [1.0, 0.0, -1.0, np.nan],
            "meta": ["x", "x", "y", "x"],
        }
    )
    audit = data_mod.audit_sequence_data(
        bad, "id", "order", "state", "duration", ["meta"], expected_states=["A", "B"]
    )
    codes = set(audit.issue_code)
    assert {
        "missing_sequence_id",
        "missing_state",
        "duplicated_position",
        "non_finite_order",
    } <= codes
    assert any(code in codes for code in {"unknown_state", "negative_duration", "zero_duration"})


def test_prepare_sequence_data_policy_error_paths():
    base = pd.DataFrame(
        {
            "id": ["s1", "s1", "s1", "s1"],
            "order": [1, 2, 2, 3],
            "state": ["A", None, "B", "B"],
            "duration": [1.0, 2.0, 0.0, 3.0],
        }
    )
    unresolved = g.prepare_sequence_data(base, "id", "order", "state", "duration")
    assert unresolved.status == "fail"
    with pytest.raises(ValidationError):
        g.prepare_sequence_data(
            base, "id", "order", "state", "duration", missing_state_policy="bad"
        )
    with pytest.raises(ValidationError):
        g.prepare_sequence_data(
            base, "id", "order", "state", "duration", duplicate_position_policy="bad"
        )
    with pytest.raises(ValidationError):
        g.prepare_sequence_data(
            base, "id", "order", "state", "duration", repeated_state_policy="bad"
        )
    with pytest.raises(ValidationError):
        g.prepare_sequence_data(
            base, "id", "order", "state", "duration", zero_duration_policy="bad"
        )
    with pytest.raises(ValidationError):
        g.prepare_sequence_data(
            base, "id", "order", "state", "duration", unknown_state_policy="bad"
        )


def test_adapter_inference_and_error_paths():
    x = _long()
    wrapped = SimpleNamespace(data=x)
    assert g.prepare_gp3tools_sequences(wrapped).data is not None
    assert g.prepare_gp3tools_sequences({"data": x}).data is not None
    with pytest.raises(ValidationError):
        g.prepare_gp3tools_sequences(object())

    ambiguous = x.rename(columns={"sequence_id": "trial_id"}).assign(scanpath_id="s")
    with pytest.raises(ValidationError):
        g.prepare_gp3tools_sequences(ambiguous)
    with pytest.raises(ValidationError):
        adapters._infer_column(x, "missing", ["sequence_id"], "id")
    with pytest.raises(ValidationError):
        adapters._infer_column(pd.DataFrame({"x": [1]}), None, ["a", "b"], "id")
    with pytest.raises(ValidationError):
        adapters._infer_column(pd.DataFrame({"a": [1], "b": [2]}), None, ["a", "b"], "id")

    with pytest.raises(ValidationError):
        g.as_grpstring_data(x, alphabet=["A"])
    network = pd.DataFrame({"x": [1]})
    with pytest.raises(ValidationError):
        g.as_igraph_transition_network(network)
    with pytest.raises(ValidationError):
        g.as_igraph_transition_network("bad")


def test_analysis_audit_family_validation_and_compare_paths():
    d = SequenceDistanceResult(
        matrix=np.array([[0.0, 1.0], [1.0, 0.0]]),
        labels=["s1", "s2"],
        method="levenshtein",
        normalise="none",
        settings={"seed": 2},
    )
    good = analysis_audit.audit_sequence_analysis(d)
    assert good.status == "pass"
    assert good.provenance["seed"] == 2

    bad = SequenceDistanceResult(
        matrix=np.array([[1.0, -2.0], [3.0, np.nan]]),
        labels=["", ""],
        method="x",
        normalise="none",
        settings={},
    )
    audit = analysis_audit.audit_sequence_analysis(bad)
    assert audit.status == "fail"
    with pytest.raises(ValueError):
        analysis_audit.audit_sequence_analysis(bad, strict=True)

    not_square = SequenceDistanceResult(
        matrix=np.array([[0.0, 1.0, 2.0]]), labels=["s1"], method="x", normalise="none", settings={}
    )
    assert analysis_audit.audit_sequence_analysis(not_square).status == "fail"

    cmp = analysis_audit.compare_sequence_analysis_results(d, d, compare_values=True)
    assert cmp.all_equal is True
    changed = SequenceDistanceResult(
        matrix=np.array([[0.0, 2.0], [2.0, 0.0]]),
        labels=["s1", "s2"],
        method="levenshtein",
        normalise="none",
        settings={"seed": 2},
    )
    assert (
        analysis_audit.compare_sequence_analysis_results(d, changed, compare_values=True).all_equal
        is False
    )

    assert analysis_audit._equal(np.array([1.0]), np.array([1.0 + 1e-10]), 1e-8)
    assert not analysis_audit._equal(pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]}), 1e-8)
    assert not analysis_audit._equal(pd.Series([1]), pd.Series([2]), 1e-8)
    assert analysis_audit._normalise_for_compare({"x": np.array([1])}) == {"x": [1]}


def test_capabilities_missing_version_path(monkeypatch):
    monkeypatch.setattr(
        capabilities.metadata,
        "version",
        lambda _: (_ for _ in ()).throw(capabilities.metadata.PackageNotFoundError()),
    )
    assert capabilities._version("definitely-not-installed-gp3seq") == "<not installed>"
    native = capabilities.sequence_capabilities(include_optional=False, check_versions=False)
    assert set(native.role) == {"native"}


def test_summary_validation_and_encoding_edges():
    with pytest.raises(ValidationError):
        summaries._assert_text_scalar("", "x")
    with pytest.raises(ValidationError):
        summaries._assert_flag(1, "x")
    with pytest.raises(ValidationError):
        summaries._assert_output_names(["state"], {"state"}, "x")

    x = _long()
    with pytest.raises(ValidationError):
        g.encode_sequence_data(x, "sequence_id", "sequence_order", "state", prefix="")
    with pytest.raises(ValidationError):
        g.encode_sequence_data(x, "sequence_id", "sequence_order", "state", state_levels=["A"])
    with pytest.raises(ValidationError):
        g.encode_sequence_data(
            x, "sequence_id", "sequence_order", "state", state_levels=["A", "A", "B", "C"]
        )
    with pytest.raises(ValidationError):
        g.encode_sequence_data(x, "sequence_id", "sequence_order", "state", width=0)
    encoded = g.encode_sequence_data(
        x, "sequence_id", "sequence_order", "state", state_levels=["C", "B", "A"], width=2
    )
    assert encoded.dictionary.state_code.tolist() == ["S01", "S02", "S03"]


def test_inference_design_and_permutation_edge_paths():
    with pytest.raises(ValidationError):
        inference.declare_sequence_comparison_design("g", "u", "bad")
    with pytest.raises(ValidationError):
        inference.declare_sequence_comparison_design("g", "u", "paired_randomized")

    design = inference.declare_sequence_comparison_design("group", "unit")
    assert inference._subseq_present(["A", "B", "C"], ["B", "C"])
    assert not inference._subseq_present(["A"], [])
    assert not inference._subseq_present(["A"], ["A", "B"])

    with pytest.raises(ValidationError):
        g.test_sequence_group_difference(_long(), object())
    with pytest.raises(ValidationError):
        g.test_sequence_group_difference(_long(), design, metric="bad")
    with pytest.raises(ValidationError):
        g.test_sequence_group_difference(_long(), design, alternative="bad")
    with pytest.raises(ValidationError):
        g.test_sequence_group_difference(_long(), design, metric="state_prevalence")
    with pytest.raises(ValidationError):
        g.test_sequence_group_difference(_long(), design, metric="subsequence_presence")

    paired = inference.declare_sequence_comparison_design(
        "group", "unit", "paired_randomized", "pair"
    )
    unit = pd.DataFrame(
        {"group": ["x", "x"], "unit": ["u1", "u2"], "pair": ["p", "p"], "metric": [1, 2]}
    )
    with pytest.raises(ValidationError):
        inference._permute(unit, paired, ["x", "y"], np.random.default_rng(1))


def test_visualisation_input_guards():
    with pytest.raises(ValidationError):
        visualisations._palette_cmap([])
    with pytest.raises(ValidationError):
        visualisations._palette_cmap(["not-a-colour"])
    with pytest.raises((ValidationError, ValueError)):
        g.plot_sequence_distance_heatmap("bad")
    with pytest.raises(ValidationError):
        g.plot_transition_network(pd.DataFrame())


def test_vector_normalise_pseudocount_contract():
    observed = adv.vector_normalise(np.array([2.0, 0.0]), pseudocount=1.0)
    baseline = adv.vector_normalise(np.array([2.0, 0.0]), pseudocount=0.0)

    np.testing.assert_allclose(observed, np.array([0.75, 0.25]))
    np.testing.assert_allclose(baseline, np.array([1.0, 0.0]))
    assert not np.allclose(observed, baseline)
