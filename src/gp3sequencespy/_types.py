from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any, cast

import pandas as pd


class ResultMapping(Mapping[str, Any]):
    """Mapping-compatible base class for structured gp3sequencespy results."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(cast(Any, self))

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dataclass_fields__)  # type: ignore[attr-defined]

    def __len__(self) -> int:
        return len(self.__dataclass_fields__)  # type: ignore[attr-defined]


@dataclass(slots=True)
class ValidationResult(ResultMapping):
    valid: bool
    status: str
    n_errors: int
    n_reviews: int
    n_info: int
    audit: pd.DataFrame
    mapping: pd.DataFrame
    n_rows: int
    n_sequences: int
    state_levels: list[str]


@dataclass(slots=True)
class PrepareResult(ResultMapping):
    data: pd.DataFrame | None
    audit: pd.DataFrame
    decisions: pd.DataFrame
    mapping: pd.DataFrame
    status: str
    original_n_rows: int
    prepared_n_rows: int
    state_levels: list[str]


@dataclass(slots=True)
class EncodingResult(ResultMapping):
    data: pd.DataFrame
    dictionary: pd.DataFrame
    mapping: pd.DataFrame
    status: str
    audit: pd.DataFrame
    state_levels: list[str]
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SequenceDistanceResult(ResultMapping):
    matrix: Any
    labels: list[str]
    method: str
    normalise: str
    settings: dict[str, Any]
    sequences: pd.DataFrame | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ClusterResult(ResultMapping):
    cluster: pd.Series
    medoids: list[int] | None
    method: str
    k: int
    distance: SequenceDistanceResult | Any
    settings: dict[str, Any]
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HMMResult(ResultMapping):
    n_states: int
    state_levels: list[str]
    initial: Any
    transition: Any
    emission: Any
    log_likelihood: float
    converged: bool
    iterations: int
    history: list[float]
    settings: dict[str, Any]
    training_data: pd.DataFrame | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StateSummaryResult(ResultMapping):
    by_sequence: pd.DataFrame
    overall: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame


@dataclass(slots=True)
class TransitionSummaryResult(ResultMapping):
    by_sequence: pd.DataFrame
    overall: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame
    include_self: bool


@dataclass(slots=True)
class PathFormatResult(ResultMapping):
    paths: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame
    settings: dict[str, Any]


@dataclass(slots=True)
class MotifExtractionResult(ResultMapping):
    occurrences: pd.DataFrame
    motifs: pd.DataFrame
    sequences: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame
    state_dictionary: pd.DataFrame
    settings: dict[str, Any]


@dataclass(slots=True)
class MotifSummaryResult(ResultMapping):
    by_sequence: pd.DataFrame
    overall: pd.DataFrame
    sequences: pd.DataFrame
    state_dictionary: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame
    extraction_settings: dict[str, Any]
    n_sequences: int
    n_occurrences: int
    n_motifs: int


@dataclass(slots=True)
class MotifFilterResult(ResultMapping):
    motifs: pd.DataFrame
    by_sequence: pd.DataFrame
    sequences: pd.DataFrame
    state_dictionary: pd.DataFrame
    audit: pd.DataFrame
    status: str
    mapping: pd.DataFrame
    extraction_settings: dict[str, Any]
    settings: dict[str, Any]
    n_available: int
    n_retained: int


@dataclass(slots=True)
class FormattedTableResult(ResultMapping):
    table: pd.DataFrame
    audit: pd.DataFrame | None
    status: str | None
    mapping: pd.DataFrame | None
    settings: dict[str, Any]


@dataclass(slots=True)
class GroupComparisonResult(ResultMapping):
    groups: pd.DataFrame
    state_summary: pd.DataFrame | None
    state_contrasts: pd.DataFrame | None
    transition_summary: pd.DataFrame | None
    transition_contrasts: pd.DataFrame | None
    length_summary: pd.DataFrame | None
    length_contrasts: pd.DataFrame | None
    settings: dict[str, Any]
