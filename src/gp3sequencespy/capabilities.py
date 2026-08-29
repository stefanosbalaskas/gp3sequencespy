from __future__ import annotations

from importlib import metadata, util

import pandas as pd

from ._advanced import scalar_logical

_ROWS = [
    ("Data contract", "Validation and preparation", "native", None, False),
    ("Distances", "Native sequence distances", "native", None, False),
    ("Distances", "Reference distance validation", "reference", "tslearn|stringdist", True),
    ("Clustering", "Native clustering and stability", "native", None, False),
    ("Patterns", "Frequent pattern reference validation", "reference", "prefixspan|seq2pat", True),
    ("Patterns", "String/AOI pattern interoperability", "adapter", "GrpString", False),
    ("HMMs", "Native categorical HMMs", "native", None, False),
    ("HMMs", "HMM reference validation", "reference", "hmmlearn|pomegranate", True),
    ("Networks", "Native transition networks", "native", None, False),
    ("Networks", "Graph interoperability", "adapter", "networkx", False),
    ("Networks", "Markov-chain interoperability", "planned_adapter", "pydtmc", False),
    (
        "Inference",
        "Permutation/distance reference validation",
        "reference",
        "scipy|scikit-learn",
        True,
    ),
    ("Missingness", "Sequence-imputation handoff", "handoff", "scikit-learn", True),
    (
        "Model-based clustering",
        "Specialist model-based clustering handoff",
        "handoff",
        "pomegranate",
        True,
    ),
    ("Graphics", "Sequence-plot handoff", "handoff", "matplotlib", True),
    ("Graphics", "Seriation/ordering handoff", "handoff", "scipy", True),
    ("Property testing", "Property-based testing", "development", "hypothesis", True),
    ("Performance", "Benchmarking", "development", "pytest-benchmark|numba", True),
]

_ALIASES = {
    "scikit-learn": "sklearn",
    "pytest-benchmark": "pytest_benchmark",
    "seq2pat": "sequential",
}


def _available(package: str) -> bool:
    return util.find_spec(_ALIASES.get(package, package.replace("-", "_"))) is not None


def _version(package: str) -> str:
    candidates = [package, package.replace("_", "-"), package.replace("-", "_")]
    for candidate in candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            pass
    return "<not installed>"


def sequence_capabilities(
    include_optional: bool = True, check_versions: bool = True
) -> pd.DataFrame:
    scalar_logical(include_optional, "include_optional")
    scalar_logical(check_versions, "check_versions")
    records = []
    for family, capability, role, backend, reference_only in _ROWS:
        packages = [] if backend is None else backend.split("|")
        available = all(_available(p) for p in packages) if packages else True
        installed_version = None
        if check_versions and packages:
            installed_version = "; ".join(
                f"{p} {_version(p)}" if _available(p) else f"{p} <not installed>" for p in packages
            )
        records.append(
            {
                "family": family,
                "capability": capability,
                "role": role,
                "native": role == "native",
                "backend": backend,
                "backend_required": role in {"adapter", "planned_adapter"},
                "available": bool(available),
                "installed_version": installed_version,
                "minimum_tested_version": None,
                "reference_only": bool(reference_only),
                "notes": "Available without the optional backend."
                if role == "native"
                else (
                    "Optional integration, reference validation, development QA, or "
                    "documented handoff."
                ),
            }
        )
    result = pd.DataFrame(records)
    if not include_optional:
        result = result.loc[result["role"] == "native"].copy()
    return result.sort_values(["family", "capability", "role"], kind="stable").reset_index(
        drop=True
    )
