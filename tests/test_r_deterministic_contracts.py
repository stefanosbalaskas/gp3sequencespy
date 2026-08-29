import importlib

import numpy as np
import pandas as pd
import pytest

import gp3sequencespy as g
from gp3sequencespy._advanced import validate_distance_matrix
from gp3sequencespy._exceptions import ValidationError


def valid_data():
    return pd.DataFrame(
        {
            "id": ["s1"] * 3 + ["s2"] * 3,
            "position": [1, 2, 3, 1, 2, 3],
            "state": ["home", "search", "product", "home", "category", "product"],
            "duration_ms": [100, 200, 300, 120, 180, 260],
            "participant": ["p1"] * 3 + ["p2"] * 3,
        }
    )


def encoding_data():
    return pd.DataFrame(
        {
            "id": ["s1"] * 4 + ["s2"] * 3,
            "position": [1, 2, 3, 4, 1, 2, 3],
            "state": ["A", "B", "A", "C", "B", "C", "A"],
            "duration_ms": [1, 2, 3, 4, 2, 2, 6],
            "group": ["g1"] * 4 + ["g2"] * 3,
        }
    )


def motif_data():
    return pd.DataFrame(
        {
            "id": ["s1"] * 5 + ["s2"] * 4,
            "position": [1, 2, 3, 4, 5, 1, 2, 3, 4],
            "state": ["A", "B", "A", "B", "A", "A", "B", "A", "C"],
            "group": ["g1"] * 5 + ["g2"] * 4,
        }
    )


def minimal_case():
    return pd.DataFrame(
        {
            "sequence_id": np.repeat(["s1", "s2", "s3", "s4"], 4),
            "sequence_order": np.tile(np.arange(1, 5), 4),
            "state": [
                "A",
                "B",
                "C",
                "D",
                "A",
                "B",
                "C",
                "C",
                "D",
                "C",
                "B",
                "A",
                "D",
                "C",
                "A",
                "A",
            ],
            "duration": np.tile([1, 2, 1, 3], 4),
            "group": np.repeat(["g1", "g2"], 8),
        }
    )


# ---- sequence-data.R -----------------------------------------------------


def test_r_data_audit_empty_contract():
    audit = g.audit_sequence_data(
        valid_data(), "id", "position", "state", "duration_ms", ["participant"]
    )
    assert list(audit.columns) == [
        "sequence_id",
        "row",
        "column",
        "issue_code",
        "severity",
        "value",
        "message",
        "action",
    ]
    assert audit.empty


def test_r_data_validation_normal_and_empty():
    result = g.validate_sequence_data(valid_data(), "id", "position", "state")
    assert (
        result.valid and result.status == "pass" and result.n_sequences == 2 and result.n_rows == 6
    )
    empty = valid_data().iloc[0:0].copy()
    result = g.validate_sequence_data(empty, "id", "position", "state")
    assert not result.valid and result.status == "fail"
    assert "empty_data" in set(result.audit.issue_code)


def test_r_data_missing_columns_and_states():
    missing = g.validate_sequence_data(valid_data(), "id", "missing_position", "state")
    assert not missing.valid and "missing_required_column" in set(missing.audit.issue_code)
    data = valid_data()
    data.loc[1, "state"] = None
    missing_state = g.validate_sequence_data(data, "id", "position", "state")
    assert not missing_state.valid and "missing_state" in set(missing_state.audit.issue_code)


def test_r_data_order_gaps_and_duplicate_positions_audited():
    data = valid_data().iloc[[1, 0, 2, 3, 4, 5]].reset_index(drop=True)
    audit = g.audit_sequence_data(data, "id", "position", "state")
    assert "unordered_rows" in set(audit.issue_code)
    gap = valid_data()
    gap.loc[2, "position"] = 4
    gap_audit = g.audit_sequence_data(gap, "id", "position", "state")
    assert "missing_positions" in set(gap_audit.issue_code)
    dup = pd.concat([valid_data(), valid_data().iloc[[1]]], ignore_index=True)
    dup_audit = g.audit_sequence_data(dup, "id", "position", "state")
    assert "duplicated_position" in set(dup_audit.issue_code)


def test_r_data_duration_and_metadata_errors():
    data = valid_data()
    data.loc[1, "duration_ms"] = -1
    audit = g.audit_sequence_data(data, "id", "position", "state", "duration_ms")
    assert "negative_duration" in set(audit.issue_code)
    data = valid_data()
    data.loc[1, "participant"] = "different"
    audit = g.audit_sequence_data(data, "id", "position", "state", metadata_cols=["participant"])
    assert "inconsistent_metadata" in set(audit.issue_code)


def test_r_data_preparation_sort_and_identifiers():
    data = valid_data().iloc[[5, 1, 0, 4, 2, 3]].reset_index(drop=True)
    prepared = g.prepare_sequence_data(
        data, "id", "position", "state", "duration_ms", ["participant"]
    )
    assert prepared.status == "pass"
    assert list(prepared.data.columns[:5]) == [
        "sequence_id",
        "sequence_order",
        "state",
        "original_row",
        "duration",
    ]
    assert prepared.data.sequence_id.astype(str).tolist() == ["s1"] * 3 + ["s2"] * 3
    assert prepared.data.sequence_order.tolist() == [1, 2, 3, 1, 2, 3]
    assert prepared.data.original_row.tolist() == [3, 2, 5, 6, 4, 1]
    assert "participant" in prepared.data.columns


def test_r_data_explicit_drop_policies():
    data = valid_data()
    data.loc[1, "state"] = None
    data.loc[4, "state"] = "unknown"
    prepared = g.prepare_sequence_data(
        data,
        "id",
        "position",
        "state",
        expected_states=["home", "search", "category", "product"],
        missing_state_policy="drop",
        unknown_state_policy="drop",
    )
    assert prepared.status == "review"
    assert not prepared.data.state.isna().any()
    assert "unknown" not in prepared.data.state.tolist()
    assert prepared.prepared_n_rows == 4


def test_r_data_duplicate_and_repeat_policies():
    data = pd.DataFrame(
        {
            "id": ["s1"] * 5,
            "position": [1, 2, 2, 3, 4],
            "state": ["A", "B", "C", "C", "D"],
            "duration_ms": [1, 2, 3, 4, 5],
        }
    )
    prepared = g.prepare_sequence_data(
        data,
        "id",
        "position",
        "state",
        "duration_ms",
        duplicate_position_policy="last",
        repeated_state_policy="collapse",
    )
    assert prepared.status == "review"
    assert prepared.data.state.astype(str).tolist() == ["A", "C", "D"]
    assert prepared.data.sequence_order.tolist() == [1, 2, 4]
    assert prepared.data.duration.tolist() == [1, 7, 5]
    assert prepared.data.original_row.tolist() == [1, 3, 5]
    out = prepared.audit
    assert (
        (out.stage == "output")
        & (out.issue_code == "missing_positions")
        & (out.severity == "review")
    ).any()
    dup = prepared.decisions.loc[prepared.decisions.step == "duplicated_positions"].iloc[0]
    rep = prepared.decisions.loc[prepared.decisions.step == "consecutive_repeats"].iloc[0]
    assert dup.policy == "last" and dup.affected_rows == 1
    assert rep.policy == "collapse" and rep.affected_rows == 1


def test_r_data_unresolved_errors_suppress_output():
    data = valid_data()
    data.loc[1, "duration_ms"] = 0
    zero = g.prepare_sequence_data(
        data, "id", "position", "state", "duration_ms", zero_duration_policy="error"
    )
    assert zero.status == "fail" and zero.data is None
    assert "zero_duration_disallowed" in set(zero.audit.issue_code)
    data = valid_data()
    data.loc[1, "duration_ms"] = -1
    neg = g.prepare_sequence_data(data, "id", "position", "state", "duration_ms")
    assert neg.status == "fail" and neg.data is None
    assert "negative_duration" in set(neg.audit.issue_code)


def test_r_data_single_state_and_unused_levels_reviewable():
    data = pd.DataFrame(
        {"id": ["s1"], "position": [1], "state": pd.Categorical(["A"], categories=["A", "B"])}
    )
    result = g.validate_sequence_data(data, "id", "position", "state")
    assert result.valid and result.status == "review"
    assert "single_state_sequence" in set(result.audit.issue_code)
    assert "unused_state_levels" in set(result.audit.issue_code)


# ---- sequence-encoding-summaries.R -------------------------------------


def test_r_encoding_deterministic_across_row_order():
    data = encoding_data()
    shuffled = data.iloc[[6, 1, 4, 0, 3, 2, 5]].reset_index(drop=True)
    first = g.encode_sequence_data(data, "id", "position", "state")
    second = g.encode_sequence_data(shuffled, "id", "position", "state")
    assert first.status == "pass"
    pd.testing.assert_frame_equal(first.dictionary, second.dictionary)
    assert first.dictionary.state.tolist() == ["A", "B", "C"]
    assert first.dictionary.state_index.tolist() == [1, 2, 3]
    assert first.dictionary.state_code.tolist() == ["S1", "S2", "S3"]
    cols = ["sequence_id", "sequence_order", "state", "state_index", "state_code"]
    pd.testing.assert_frame_equal(
        first.data[cols].reset_index(drop=True), second.data[cols].reset_index(drop=True)
    )


def test_r_encoding_custom_levels_and_labels():
    encoded = g.encode_sequence_data(
        encoding_data(),
        "id",
        "position",
        "state",
        state_levels=["C", "B", "A", "Z"],
        prefix="Q",
        width=2,
    )
    assert encoded.dictionary.state.tolist() == ["C", "B", "A", "Z"]
    assert encoded.dictionary.state_code.tolist() == ["Q01", "Q02", "Q03", "Q04"]
    assert encoded.dictionary.observed.tolist() == [True, True, True, False]
    assert encoded.settings["width"] == 2
    with pytest.raises(ValidationError, match="omits observed states"):
        g.encode_sequence_data(encoding_data(), "id", "position", "state", state_levels=["A", "B"])


def test_r_encoding_categorical_levels_define_order():
    data = encoding_data()
    data["state"] = pd.Categorical(data.state, categories=["C", "A", "B", "Z"])
    encoded = g.encode_sequence_data(data, "id", "position", "state")
    assert encoded.dictionary.state.tolist() == ["C", "A", "B", "Z"]
    assert not bool(encoded.dictionary.loc[encoded.dictionary.state == "Z", "observed"].iloc[0])


def test_r_state_summary_exact_counts_and_proportions():
    result = g.summarise_sequence_states(
        encoding_data(), "id", "position", "state", "duration_ms", ["group"]
    )
    assert result.status == "pass"
    s1a = result.by_sequence.query("sequence_id == 's1' and state == 'A'").iloc[0]
    assert s1a.group == "g1" and s1a.n_observations == 2
    assert s1a.observation_proportion == pytest.approx(0.5)
    assert s1a.duration_sum == pytest.approx(4) and s1a.duration_proportion == pytest.approx(0.4)
    assert s1a.mean_duration == pytest.approx(2)
    oa = result.overall.query("state == 'A'").iloc[0]
    assert oa.n_sequences == 2 and oa.sequence_proportion == pytest.approx(1)
    assert oa.n_observations == 3 and oa.observation_proportion == pytest.approx(3 / 7)
    assert oa.duration_sum == pytest.approx(10) and oa.duration_proportion == pytest.approx(0.5)
    assert oa.mean_duration == pytest.approx(10 / 3)


def test_r_state_summary_deterministic_across_input_order():
    data = encoding_data()
    shuffled = data.iloc[[5, 0, 6, 3, 1, 4, 2]].reset_index(drop=True)
    a = g.summarise_sequence_states(data, "id", "position", "state")
    b = g.summarise_sequence_states(shuffled, "id", "position", "state")
    pd.testing.assert_frame_equal(a.by_sequence, b.by_sequence)
    pd.testing.assert_frame_equal(a.overall, b.overall)


def test_r_transition_summary_exact_adjacent_counts():
    result = g.summarise_sequence_transitions(encoding_data(), "id", "position", "state", ["group"])
    assert result.status == "pass"
    ab = result.by_sequence.query(
        "sequence_id == 's1' and from_state == 'A' and to_state == 'B'"
    ).iloc[0]
    assert ab.group == "g1" and ab.n_transitions == 1
    assert ab.sequence_transition_proportion == pytest.approx(1 / 3)
    assert ab.origin_transition_proportion == pytest.approx(0.5)
    ba = result.overall.query("from_state == 'B' and to_state == 'A'").iloc[0]
    assert ba.n_sequences == 1 and ba.sequence_proportion == pytest.approx(0.5)
    assert ba.n_transitions == 1 and ba.transition_proportion == pytest.approx(0.2)
    assert ba.origin_transition_proportion == pytest.approx(0.5)


def test_r_transition_self_filtering_explicit():
    data = pd.DataFrame({"id": ["s1"] * 3, "position": [1, 2, 3], "state": ["A", "A", "B"]})
    retained = g.summarise_sequence_transitions(data, "id", "position", "state", include_self=True)
    removed = g.summarise_sequence_transitions(data, "id", "position", "state", include_self=False)
    assert retained.status == "review"
    assert ((retained.overall.from_state == "A") & (retained.overall.to_state == "A")).any()
    assert not (removed.overall.from_state == removed.overall.to_state).any()
    assert removed.overall.n_transitions.tolist() == [1]


def test_r_transition_single_state_empty_schema():
    result = g.summarise_sequence_transitions(
        pd.DataFrame({"id": ["s1"], "position": [1], "state": ["A"]}), "id", "position", "state"
    )
    assert result.status == "review" and result.by_sequence.empty and result.overall.empty
    assert list(result.overall.columns) == [
        "from_state",
        "to_state",
        "n_sequences",
        "sequence_proportion",
        "n_transitions",
        "transition_proportion",
        "origin_transition_proportion",
    ]


def test_r_paths_ordered_and_metadata_retained():
    data = encoding_data()
    shuffled = data.iloc[[6, 3, 1, 5, 0, 4, 2]].reset_index(drop=True)
    result = g.format_sequence_paths(shuffled, "id", "position", "state", ["group"])
    assert result.status == "review"
    assert (
        (result.audit.issue_code == "unordered_rows") & (result.audit.severity == "review")
    ).any()
    assert result.paths.sequence_id.tolist() == ["s1", "s2"]
    assert result.paths.group.tolist() == ["g1", "g2"]
    assert result.paths.path.tolist() == ["A > B > A > C", "B > C > A"]
    assert result.paths.n_observations.tolist() == [4, 3]
    assert result.paths.n_states.tolist() == [4, 3]
    ordered = g.format_sequence_paths(data, "id", "position", "state", ["group"])
    assert ordered.status == "pass" and ordered.audit.empty
    pd.testing.assert_frame_equal(ordered.paths, result.paths)


def test_r_paths_collapse_consecutive_repeats():
    data = pd.DataFrame(
        {"id": ["s1"] * 5, "position": range(1, 6), "state": ["A", "A", "B", "B", "C"]}
    )
    result = g.format_sequence_paths(
        data, "id", "position", "state", separator="/", collapse_repeats=True
    )
    assert result.status == "review"
    row = result.paths.iloc[0]
    assert row.n_observations == 5 and row.n_states == 3 and row.n_unique_states == 3
    assert row.start_state == "A" and row.end_state == "C" and row.path == "A/B/C"


def test_r_summary_functions_reject_unresolved_validation_errors():
    data = encoding_data()
    data.loc[1, "position"] = 1
    for func in [
        g.encode_sequence_data,
        g.summarise_sequence_states,
        g.summarise_sequence_transitions,
        g.format_sequence_paths,
    ]:
        with pytest.raises(ValidationError, match="failed validation"):
            func(data, "id", "position", "state")


# ---- sequence-motifs.R --------------------------------------------------


def test_r_motifs_contiguous_stable_positions():
    result = g.extract_sequence_ngrams(
        motif_data(),
        "id",
        "position",
        "state",
        metadata_cols=["group"],
        min_length=2,
        max_length=3,
        overlap="allow",
    )
    assert result.status == "pass" and len(result.occurrences) == 12
    assert result.sequences.n_candidate_occurrences.tolist() == [7, 5]
    assert result.sequences.n_retained_occurrences.tolist() == [7, 5]
    assert np.all(
        result.occurrences.end_index - result.occurrences.start_index + 1
        == result.occurrences.motif_length
    )
    assert (
        result.occurrences.loc[result.occurrences.sequence_id == "s1", "group"].tolist()
        == ["g1"] * 7
    )
    aba = result.occurrences.query("sequence_id == 's1' and motif == 'A > B > A'")
    assert aba.start_index.tolist() == [1, 3] and aba.end_index.tolist() == [3, 5]
    assert aba.occurrence_index.tolist() == [1, 2]


def test_r_motifs_overlap_policy_deterministic():
    allowed = g.extract_sequence_ngrams(
        motif_data(), "id", "position", "state", min_length=3, max_length=3, overlap="allow"
    )
    disallowed = g.extract_sequence_ngrams(
        motif_data(), "id", "position", "state", min_length=3, max_length=3, overlap="disallow"
    )
    assert len(allowed.occurrences.query("motif == 'A > B > A'")) == 3
    dab = disallowed.occurrences.query("motif == 'A > B > A'")
    assert len(dab) == 2 and dab.start_index.tolist() == [1, 1]
    assert disallowed.settings["overlap_rule"] == "left_to_right_greedy"
    repeated = pd.DataFrame({"id": ["s1"] * 4, "position": range(1, 5), "state": ["A"] * 4})
    rep = g.extract_sequence_ngrams(
        repeated, "id", "position", "state", min_length=2, max_length=2, overlap="disallow"
    )
    assert rep.status == "review" and rep.occurrences.start_index.tolist() == [1, 3]


def test_r_motifs_row_order_corrected_with_review():
    data = motif_data()
    shuffled = data.iloc[[6, 1, 8, 0, 5, 3, 2, 7, 4]].reset_index(drop=True)
    ordered = g.extract_sequence_ngrams(data, "id", "position", "state", min_length=2, max_length=3)
    reordered = g.extract_sequence_ngrams(
        shuffled, "id", "position", "state", min_length=2, max_length=3
    )
    assert ordered.status == "pass" and reordered.status == "review"
    assert "unordered_rows" in set(reordered.audit.issue_code)
    cols = [
        "sequence_id",
        "motif_id",
        "motif",
        "motif_length",
        "start_index",
        "end_index",
        "start_order",
        "end_order",
        "occurrence_index",
    ]
    pd.testing.assert_frame_equal(
        ordered.occurrences[cols].reset_index(drop=True),
        reordered.occurrences[cols].reset_index(drop=True),
    )


def test_r_motifs_separator_labels_keep_identity():
    data = pd.DataFrame(
        {"id": ["single", "pair", "pair"], "position": [1, 1, 2], "state": ["A > B", "A", "B"]}
    )
    result = g.extract_sequence_ngrams(
        data, "id", "position", "state", min_length=1, max_length=2, separator=" > "
    )
    same = result.occurrences.loc[
        result.occurrences.motif == "A > B", ["motif_id", "motif_key", "motif_length"]
    ]
    assert len(same) == 2 and same.motif_id.nunique() == 2 and same.motif_key.nunique() == 2
    assert sorted(same.motif_length.tolist()) == [1, 2]


def test_r_motif_summary_exact_counts_prevalence():
    summary = g.summarise_sequence_motifs(
        g.extract_sequence_ngrams(
            motif_data(), "id", "position", "state", min_length=2, max_length=3
        )
    )
    aba = summary.overall.query("motif == 'A > B > A'").iloc[0]
    assert summary.n_sequences == 2 and summary.n_occurrences == 12
    assert aba.n_occurrences == 3 and aba.n_sequences == 2
    assert aba.sequence_prevalence == pytest.approx(1) and aba.occurrence_share == pytest.approx(
        3 / 12
    )
    assert aba.mean_occurrences_per_sequence == pytest.approx(1.5)
    assert aba.mean_occurrences_when_present == pytest.approx(1.5)
    s1 = summary.by_sequence.query("sequence_id == 's1' and motif == 'A > B > A'").iloc[0]
    assert s1.n_occurrences == 2 and s1.first_start_index == 1 and s1.last_start_index == 3


def test_r_motif_prevalence_denominator_includes_short_sequences():
    extra = pd.DataFrame({"id": ["s3"], "position": [1], "state": ["A"], "group": ["g3"]})
    data = pd.concat([motif_data(), extra], ignore_index=True)
    extracted = g.extract_sequence_ngrams(
        data, "id", "position", "state", metadata_cols=["group"], min_length=3, max_length=3
    )
    summary = g.summarise_sequence_motifs(extracted)
    aba = summary.overall.query("motif == 'A > B > A'").iloc[0]
    assert extracted.status == "review" and summary.n_sequences == 3
    assert aba.sequence_prevalence == pytest.approx(2 / 3)
    assert extracted.sequences.n_candidate_occurrences.tolist() == [3, 2, 0]


def test_r_motif_filter_thresholds():
    summary = g.summarise_sequence_motifs(
        g.extract_sequence_ngrams(
            motif_data(), "id", "position", "state", min_length=2, max_length=3
        )
    )
    filtered = g.filter_sequence_motifs(
        summary, min_occurrences=3, min_sequences=2, min_prevalence=1, motif_lengths=[2]
    )
    assert filtered.motifs.motif.tolist() == ["A > B", "B > A"]
    assert filtered.n_available == 6 and filtered.n_retained == 2
    assert set(filtered.by_sequence.motif_id).issubset(set(filtered.motifs.motif_id))


def test_r_motif_top_n_ties():
    summary = g.summarise_sequence_motifs(
        g.extract_sequence_ngrams(
            motif_data(), "id", "position", "state", min_length=2, max_length=3
        )
    )
    included = g.filter_sequence_motifs(summary, top_n=1, rank_by="n_occurrences", ties="include")
    first = g.filter_sequence_motifs(summary, top_n=1, rank_by="n_occurrences", ties="first")
    assert included.n_retained == 3 and (included.motifs.n_occurrences == 3).all()
    assert first.n_retained == 1 and first.motifs.motif.tolist() == ["A > B"]


def test_r_motif_format_units_and_rank_ties():
    summary = g.summarise_sequence_motifs(
        g.extract_sequence_ngrams(
            motif_data(), "id", "position", "state", min_length=2, max_length=3
        )
    )
    formatted = g.format_sequence_motifs(
        summary, prevalence="percent", digits=1, rank_by="n_occurrences", ties="min"
    )
    assert (
        "sequence_prevalence_percent" in formatted.table
        and "occurrence_share_percent" in formatted.table
    )
    assert formatted.table["rank"].iloc[:3].tolist() == [1, 1, 1]
    assert formatted.table.sequence_prevalence_percent.iloc[:3].tolist() == [100, 100, 100]
    noids = g.format_sequence_motifs(summary, include_ids=False, include_rank=False)
    assert not {"motif_id", "motif_key", "rank"} & set(noids.table.columns)


def test_r_motif_empty_outputs_stable_schemas():
    extracted = g.extract_sequence_ngrams(
        motif_data(), "id", "position", "state", min_length=6, max_length=6
    )
    summary = g.summarise_sequence_motifs(extracted)
    filtered = g.filter_sequence_motifs(summary, min_occurrences=2)
    formatted = g.format_sequence_motifs(filtered)
    assert (
        extracted.occurrences.empty
        and extracted.motifs.empty
        and summary.by_sequence.empty
        and summary.overall.empty
    )
    assert filtered.motifs.empty and formatted.table.empty
    assert "rank" in formatted.table.columns and "sequence_prevalence" in formatted.table.columns


def test_r_motif_categorical_levels_define_codes():
    data = motif_data()
    data["state"] = pd.Categorical(data.state, categories=["C", "A", "B", "Z"])
    result = g.extract_sequence_ngrams(data, "id", "position", "state", min_length=2, max_length=2)
    assert result.state_dictionary.state.tolist() == ["C", "A", "B", "Z"]
    assert not bool(
        result.state_dictionary.loc[result.state_dictionary.state == "Z", "observed"].iloc[0]
    )
    ab = result.motifs.loc[result.motifs.motif == "A > B"].iloc[0]
    assert ab.motif_key == "S2|S3"


def test_r_motif_invalid_settings_rejected():
    data = motif_data()
    with pytest.raises(ValidationError, match="max_length"):
        g.extract_sequence_ngrams(data, "id", "position", "state", min_length=3, max_length=2)
    with pytest.raises(ValidationError, match="overlap"):
        g.extract_sequence_ngrams(data, "id", "position", "state", overlap="sometimes")
    duplicated = data.copy()
    duplicated.loc[1, "position"] = 1
    with pytest.raises(ValidationError, match="failed validation"):
        g.extract_sequence_ngrams(duplicated, "id", "position", "state")
    extracted = g.extract_sequence_ngrams(data, "id", "position", "state")
    with pytest.raises(ValidationError, match="between 0 and 1"):
        g.filter_sequence_motifs(extracted, min_prevalence=1.1)
    with pytest.raises(ValidationError, match="positive whole numbers"):
        g.filter_sequence_motifs(extracted, motif_lengths=[2, 2.5])
    with pytest.raises(ValidationError, match="must not exceed 15"):
        g.format_sequence_motifs(extracted, digits=16)


# ---- invariant/adversarial/metamorphic contracts ------------------------


def test_r_distance_core_mathematical_invariants():
    distance = g.compute_sequence_distance(minimal_case(), method="levenshtein")
    assert np.all(distance.matrix >= 0)
    assert np.allclose(np.diag(distance.matrix), 0)
    assert np.allclose(distance.matrix, distance.matrix.T)
    assert distance.labels == distance.labels
    arr, labels = validate_distance_matrix(distance.matrix)
    assert arr.shape == (4, 4) and len(labels) == 4


def test_r_metamorphic_distance_invariant_to_row_order():
    data = minimal_case()
    shuffled = data.sample(frac=1, random_state=2026).reset_index(drop=True)
    a = g.compute_sequence_distance(data, method="levenshtein")
    b = g.compute_sequence_distance(shuffled, method="levenshtein")
    assert np.array_equal(a.matrix, b.matrix)
    assert set(a.sequences.state.astype(str)) == set(b.sequences.state.astype(str))


def test_r_metamorphic_irrelevant_metadata_no_distance_change():
    data = minimal_case()
    other = data.copy()
    other["irrelevant_metadata"] = [f"row{i}" for i in range(len(other))]
    a = g.compute_sequence_distance(data, method="lcs")
    b = g.compute_sequence_distance(other, method="lcs")
    assert np.array_equal(a.matrix, b.matrix)


def test_r_metamorphic_state_relabelling_preserves_levenshtein_geometry():
    data = minimal_case()
    other = data.copy()
    mapping = {"A": "north", "B": "south", "C": "east", "D": "west"}
    other["state"] = other.state.map(mapping)
    a = g.compute_sequence_distance(data, method="levenshtein")
    b = g.compute_sequence_distance(other, method="levenshtein")
    assert np.array_equal(a.matrix, b.matrix)


def test_r_adversarial_failures_are_explicit():
    base = minimal_case()
    cases = []
    cases.append(base.iloc[0:0].copy())
    dup = base.copy()
    dup.loc[1, "sequence_order"] = dup.loc[0, "sequence_order"]
    cases.append(dup)
    neg = base.copy()
    neg.loc[1, "duration"] = -1
    cases.append(neg)
    for data in cases:
        result = g.validate_sequence_data(
            data, "sequence_id", "sequence_order", "state", "duration"
        )
        assert result.status == "fail"


def test_r_adversarial_review_cases_not_silently_destroyed():
    base = minimal_case()
    gaps = base.copy()
    gaps.loc[gaps.sequence_id == "s1", "sequence_order"] = [1, 2, 4, 5]
    zero = base.copy()
    zero.loc[1, "duration"] = 0
    rep = base.copy()
    rep["state"] = np.tile(["A", "A", "A", "B"], 4)
    for data in [gaps, zero, rep]:
        result = g.validate_sequence_data(
            data, "sequence_id", "sequence_order", "state", "duration"
        )
        assert result.status in {"review", "fail"}


def test_r_package_namespace_available():
    assert importlib.import_module("gp3sequencespy") is g
