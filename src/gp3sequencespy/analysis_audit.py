from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, cast

import numpy as np
import pandas as pd

from ._advanced import scalar_logical, scalar_number
from ._types import HMMResult, PrepareResult, SequenceDistanceResult, ValidationResult
from .covariate_hmm import CovariateSequenceHMM
from .distances import SequenceClusterBootstrap, SequenceClusterEnsemble, SequenceClustering
from .multichannel_hmm import MultichannelSequenceHMM
from .networks import HigherOrderTransitionModel


@dataclass(slots=True)
class SequenceAnalysisAudit:
    summary: pd.DataFrame
    issues: pd.DataFrame
    provenance: dict[str, Any]
    contract: dict[str, Any]
    status: str


@dataclass(slots=True)
class SequenceAnalysisComparison:
    comparisons: pd.DataFrame
    x_audit: SequenceAnalysisAudit
    y_audit: SequenceAnalysisAudit
    value_comparison: Any
    all_equal: bool


def _issue(code: str, severity: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "field": field, "message": message}


def _family(x: Any) -> str:
    if isinstance(x, SequenceDistanceResult):
        return "distance"
    if isinstance(x, SequenceClustering):
        return "clustering"
    if isinstance(x, SequenceClusterBootstrap):
        return "cluster_bootstrap"
    if isinstance(x, SequenceClusterEnsemble):
        return "cluster_ensemble"
    if isinstance(x, pd.DataFrame) and x.attrs.get("gp3_class") == "gp3_transition_network":
        return "transition_network"
    if isinstance(x, HigherOrderTransitionModel):
        return "higher_order_transition"
    if isinstance(x, HMMResult):
        return "hmm"
    if isinstance(x, MultichannelSequenceHMM):
        return "multichannel_hmm"
    if isinstance(x, CovariateSequenceHMM):
        return "covariate_hmm"
    if isinstance(x, PrepareResult):
        return "prepared_sequence_data"
    if isinstance(x, ValidationResult):
        return "sequence_validation"
    return "generic"


def _primary_class(x: Any) -> str:
    if isinstance(x, pd.DataFrame) and x.attrs.get("gp3_class"):
        return str(x.attrs["gp3_class"])
    return type(x).__name__


def _sequence_ids(x: Any) -> list[str]:
    if isinstance(x, SequenceDistanceResult):
        return [str(v) for v in x.labels]
    if isinstance(x, SequenceClustering):
        return [str(v) for v in x.assignments.index]
    if isinstance(x, SequenceClusterEnsemble):
        return [str(v) for v in x.assignments.index]
    if (
        isinstance(x, HMMResult)
        and x.training_data is not None
        and "sequence_id" in x.training_data
    ):
        return list(dict.fromkeys(x.training_data["sequence_id"].astype(str).tolist()))
    for attr in ("training_data", "data"):
        value = getattr(x, attr, None)
        if isinstance(value, pd.DataFrame) and "sequence_id" in value:
            return list(dict.fromkeys(value["sequence_id"].astype(str).tolist()))
    if isinstance(x, PrepareResult) and x.data is not None:
        return list(dict.fromkeys(x.data["sequence_id"].astype(str).tolist()))
    return []


def _state_levels(x: Any) -> list[str]:
    states = getattr(x, "state_levels", None)
    if states is not None:
        return [str(v) for v in states]
    if isinstance(x, SequenceDistanceResult) and x.sequences is not None and "state" in x.sequences:
        return list(dict.fromkeys(x.sequences["state"].dropna().astype(str).tolist()))
    data = getattr(x, "training_data", None)
    if isinstance(data, pd.DataFrame) and "state" in data:
        return list(dict.fromkeys(data["state"].dropna().astype(str).tolist()))
    return []


def _method(x: Any, family: str) -> Any:
    value = getattr(x, "method", None)
    if value is not None:
        return value
    if family == "hmm":
        return "categorical_hmm"
    if family == "transition_network":
        return "transition_network"
    return None


def _settings(x: Any) -> dict[str, Any]:
    value = getattr(x, "settings", None)
    if isinstance(value, dict):
        return value
    if isinstance(x, pd.DataFrame):
        value = x.attrs.get("settings")
        if isinstance(value, dict):
            return value
    out = {}
    for key in (
        "k",
        "linkage",
        "seed",
        "order",
        "smoothing",
        "backoff",
        "tolerance",
        "iterations",
        "converged",
    ):
        if hasattr(x, key):
            out[key] = getattr(x, key)
    return out


def _seed(x: Any) -> Any:
    if hasattr(x, "seed"):
        return x.seed
    settings = _settings(x)
    return settings.get("seed")


def _validate_distance(x: SequenceDistanceResult, tolerance: float) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    try:
        arr = np.asarray(x.matrix, dtype=float)
    except Exception:
        return [
            _issue(
                "invalid_distance_matrix",
                "error",
                "distance",
                "A distance result must be a non-empty numeric square matrix.",
            )
        ]
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[0] != arr.shape[1]:
        return [
            _issue(
                "invalid_distance_matrix",
                "error",
                "distance",
                "A distance result must be a non-empty numeric square matrix.",
            )
        ]
    if not np.isfinite(arr).all():
        issues.append(
            _issue(
                "non_finite_distance",
                "error",
                "distance",
                "Distance matrices must contain finite values.",
            )
        )
    if np.any(arr < -tolerance):
        issues.append(
            _issue(
                "negative_distance",
                "error",
                "distance",
                "Distances must be non-negative within tolerance.",
            )
        )
    if np.any(np.abs(np.diag(arr)) > tolerance):
        issues.append(
            _issue(
                "nonzero_distance_diagonal",
                "error",
                "distance",
                "The distance diagonal must be zero within tolerance.",
            )
        )
    if np.max(np.abs(arr - arr.T)) > tolerance:
        issues.append(
            _issue(
                "asymmetric_distance",
                "error",
                "distance",
                "The distance matrix must be symmetric within tolerance.",
            )
        )
    if (
        len(x.labels) != len(arr)
        or len(set(map(str, x.labels))) != len(x.labels)
        or any(str(v) == "" for v in x.labels)
    ):
        issues.append(
            _issue(
                "distance_identifiers_invalid",
                "review",
                "distance",
                "Distance identifiers should be unique, non-missing, and complete.",
            )
        )
    return issues


def _validate(x: Any, family: str, tolerance: float) -> list[dict[str, str]]:
    if family == "distance":
        return _validate_distance(x, tolerance)
    if family in {"clustering", "cluster_ensemble"}:
        assignments = getattr(x, "assignments", None)
        if (
            not isinstance(assignments, pd.Series)
            or assignments.empty
            or assignments.index.has_duplicates
        ):
            return [
                _issue(
                    "invalid_clustering_assignments",
                    "error",
                    "assignments",
                    "Clustering assignments must be a non-empty named series.",
                )
            ]
        return []
    if family == "transition_network":
        required = {"context", "to_state", "count", "weight"}
        if not required.issubset(x.columns):
            return [
                _issue(
                    "transition_columns_missing",
                    "error",
                    "network",
                    "Required transition-network columns are missing.",
                )
            ]
        if x[["count", "weight"]].apply(pd.to_numeric, errors="coerce").isna().any().any():
            return [
                _issue(
                    "transition_values_invalid",
                    "error",
                    "network",
                    "Transition count and weight columns must be numeric.",
                )
            ]
        return []
    if family in {"hmm", "multichannel_hmm", "covariate_hmm"}:
        for name in ("initial", "transition"):
            value = getattr(x, name, None)
            if value is not None and not np.isfinite(np.asarray(value, dtype=float)).all():
                return [
                    _issue(
                        "invalid_hmm_probabilities",
                        "error",
                        name,
                        "HMM probability arrays must be finite.",
                    )
                ]
        return []
    if family in {"prepared_sequence_data", "sequence_validation"}:
        if getattr(x, "status", None) not in {"pass", "review", "fail"}:
            return [
                _issue("invalid_status", "error", "status", "Status must be pass, review, or fail.")
            ]
    return []


def audit_sequence_analysis(
    x: Any, strict: bool = False, tolerance: float = 1e-8
) -> SequenceAnalysisAudit:
    scalar_logical(strict, "strict")
    scalar_number(tolerance, "tolerance", lower=np.nextafter(0.0, 1.0))
    family = _family(x)
    issues_list = _validate(x, family, float(tolerance))
    ids = _sequence_ids(x)
    states = _state_levels(x)
    if not ids and family in {
        "distance",
        "clustering",
        "cluster_bootstrap",
        "cluster_ensemble",
        "hmm",
    }:
        issues_list.append(
            _issue(
                "sequence_ids_not_recoverable",
                "review",
                "sequence_ids",
                "Sequence identifiers could not be recovered from this analysis object.",
            )
        )
    issues = pd.DataFrame(issues_list, columns=["code", "severity", "field", "message"])
    if any(i["severity"] == "error" for i in issues_list):
        status = "fail"
    elif any(i["severity"] == "review" for i in issues_list):
        status = "review"
    else:
        status = "pass"
    provenance = {
        "package": "gp3sequencespy",
        "package_version": "0.1.0a1",
        "contract_version": "0.3.0-python-alpha",
        "family": family,
        "method": _method(x, family),
        "sequence_ids": ids,
        "state_levels": states,
        "seed": _seed(x),
        "settings": _settings(x),
    }
    contract = {
        "contract_version": provenance["contract_version"],
        "family": family,
        "primary_class": _primary_class(x),
    }
    summary = pd.DataFrame(
        [
            {
                "family": family,
                "primary_class": contract["primary_class"],
                "package_version": provenance["package_version"],
                "contract_version": provenance["contract_version"],
                "method": provenance["method"],
                "n_sequence_ids": len(ids),
                "n_state_levels": len(states),
                "seed_recorded": provenance["seed"] is not None,
                "n_issues": len(issues),
                "status": status,
            }
        ]
    )
    result = SequenceAnalysisAudit(summary, issues, provenance, contract, status)
    if strict and status == "fail":
        messages = " ".join(
            issues.loc[issues["severity"] == "error", "message"].astype(str).unique()
        )
        raise ValueError("Sequence-analysis audit failed: " + messages)
    return result


def _normalise_for_compare(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return (tuple(value.columns), tuple(value.index.astype(str)), value.to_numpy().tolist())
    if isinstance(value, pd.Series):
        return (tuple(value.index.astype(str)), value.to_list())
    if isinstance(value, np.ndarray):
        return value.tolist()
    if is_dataclass(value):
        return {k: _normalise_for_compare(v) for k, v in asdict(cast(Any, value)).items()}
    if isinstance(value, dict):
        return {str(k): _normalise_for_compare(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise_for_compare(v) for v in value]
    return value


def _equal(a: Any, b: Any, tolerance: float) -> bool:
    try:
        if isinstance(a, (float, int, np.number)) and isinstance(b, (float, int, np.number)):
            return bool(
                np.isclose(float(a), float(b), atol=tolerance, rtol=tolerance, equal_nan=True)
            )
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            return bool(
                np.allclose(
                    np.asarray(a, dtype=float),
                    np.asarray(b, dtype=float),
                    atol=tolerance,
                    rtol=tolerance,
                    equal_nan=True,
                )
            )
        if isinstance(a, pd.DataFrame) and isinstance(b, pd.DataFrame):
            try:
                pd.testing.assert_frame_equal(
                    a, b, check_exact=False, rtol=tolerance, atol=tolerance
                )
                return True
            except AssertionError:
                return False
        if isinstance(a, pd.Series) and isinstance(b, pd.Series):
            try:
                pd.testing.assert_series_equal(
                    a, b, check_exact=False, rtol=tolerance, atol=tolerance
                )
                return True
            except AssertionError:
                return False
        return _normalise_for_compare(a) == _normalise_for_compare(b)
    except Exception:
        return False


def _row(field: str, x: Any, y: Any, equal: bool) -> dict[str, Any]:
    def text(v: Any) -> str:
        if isinstance(v, (list, tuple)):
            return " | ".join(map(str, v))
        return str(v)

    return {"field": field, "x": text(x), "y": text(y), "equal": bool(equal)}


def compare_sequence_analysis_results(
    x: Any, y: Any, tolerance: float = 1e-8, compare_values: bool = False
) -> SequenceAnalysisComparison:
    scalar_number(tolerance, "tolerance", lower=np.nextafter(0.0, 1.0))
    scalar_logical(compare_values, "compare_values")
    xa = audit_sequence_analysis(x, tolerance=tolerance)
    ya = audit_sequence_analysis(y, tolerance=tolerance)
    xp, yp = xa.provenance, ya.provenance
    rows = [
        _row(
            "family",
            xa.contract["family"],
            ya.contract["family"],
            xa.contract["family"] == ya.contract["family"],
        ),
        _row(
            "primary_class",
            xa.contract["primary_class"],
            ya.contract["primary_class"],
            xa.contract["primary_class"] == ya.contract["primary_class"],
        ),
        _row("method", xp["method"], yp["method"], _equal(xp["method"], yp["method"], tolerance)),
        _row(
            "sequence_ids",
            xp["sequence_ids"],
            yp["sequence_ids"],
            list(map(str, xp["sequence_ids"])) == list(map(str, yp["sequence_ids"])),
        ),
        _row(
            "state_levels",
            xp["state_levels"],
            yp["state_levels"],
            list(map(str, xp["state_levels"])) == list(map(str, yp["state_levels"])),
        ),
        _row("seed", xp["seed"], yp["seed"], _equal(xp["seed"], yp["seed"], tolerance)),
        _row(
            "settings",
            xp["settings"],
            yp["settings"],
            _equal(xp["settings"], yp["settings"], tolerance),
        ),
    ]
    comparisons = pd.DataFrame(rows)
    value_comparison = _equal(x, y, tolerance) if compare_values else None
    all_equal = bool(comparisons["equal"].all() and (value_comparison if compare_values else True))
    return SequenceAnalysisComparison(comparisons, xa, ya, value_comparison, all_equal)
