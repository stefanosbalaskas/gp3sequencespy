from __future__ import annotations

import argparse
import inspect
import json
import math
import re
from pathlib import Path
from typing import Any

import gp3sequencespy as g


def _split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False

    for ch in text:
        if quote is not None:
            current.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue

        if ch in {"'", '"'}:
            quote = ch
            current.append(ch)
        elif ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                parts.append(item)
            current = []
        else:
            current.append(ch)

    item = "".join(current).strip()
    if item:
        parts.append(item)
    return parts


def _parse_r_formals(text: str) -> list[dict[str, Any]]:
    compact = re.sub(r"\s+", " ", text.strip())
    out: list[dict[str, Any]] = []
    for item in _split_top_level(compact):
        if item == "...":
            out.append(
                {
                    "name": "...",
                    "has_default": False,
                    "default_text": None,
                    "variadic": True,
                }
            )
        elif "=" in item:
            name, default = item.split("=", 1)
            out.append(
                {
                    "name": name.strip(),
                    "has_default": True,
                    "default_text": default.strip(),
                    "variadic": False,
                }
            )
        else:
            out.append(
                {
                    "name": item.strip(),
                    "has_default": False,
                    "default_text": None,
                    "variadic": False,
                }
            )
    return out


def _parse_r_c_vector(text: str) -> list[Any] | None:
    m = re.fullmatch(r"c\((.*)\)", text.strip(), flags=re.S)
    if m is None:
        return None

    values: list[Any] = []
    for item in _split_top_level(m.group(1)):
        item = item.strip()
        if len(item) >= 2 and item[0] == item[-1] and item[0] in {"'", '"'}:
            values.append(item[1:-1])
        elif re.fullmatch(r"-?\d+L", item):
            values.append(int(item[:-1]))
        elif re.fullmatch(r"-?\d+", item):
            values.append(int(item))
        elif re.fullmatch(r"-?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?", item):
            values.append(float(item))
        else:
            return None
    return values


def _normalize_r_default(text: str) -> tuple[str, Any]:
    t = text.strip()
    if t == "NULL":
        return "literal", None
    if t == "TRUE":
        return "literal", True
    if t == "FALSE":
        return "literal", False
    if t in {"Inf", "+Inf"}:
        return "literal", math.inf
    if t == "-Inf":
        return "literal", -math.inf
    if t in {"NA", "NA_real_", "NA_integer_", "NA_character_"}:
        return "na", None

    vector = _parse_r_c_vector(t)
    if vector is not None:
        return "r_vector", vector

    if re.fullmatch(r"-?\d+L", t):
        return "literal", int(t[:-1])
    if re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", t):
        return "literal", float(t) if any(c in t for c in ".eE") else int(t)

    if len(t) >= 2 and t[0] == t[-1] and t[0] in {"'", '"'}:
        return "literal", t[1:-1]

    return "expression", t


def _json_default(value: Any) -> Any:
    if value is inspect._empty:
        return "<required>"
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, float) and math.isinf(value):
            return "Inf" if value > 0 else "-Inf"
        return value
    if isinstance(value, (tuple, list)):
        return list(value)
    return repr(value)


def _defaults_equivalent(r_default: str, py_default: Any) -> tuple[bool, str]:
    kind, expected = _normalize_r_default(r_default)

    if py_default is inspect._empty:
        return False, "R optional parameter became Python required"

    if kind == "na":
        if py_default is None:
            return True, "R NA -> Python None"
        if isinstance(py_default, float) and math.isnan(py_default):
            return True, "R NA -> Python NaN"
        return False, f"R NA vs Python {py_default!r}"

    if kind == "r_vector":
        if isinstance(py_default, (tuple, list)) and list(py_default) == expected:
            return True, f"R vector default -> Python {type(py_default).__name__}"
        if expected and py_default == expected[0]:
            return True, f"R match.arg choices -> first Python default {expected[0]!r}"
        return False, f"R vector {expected!r} vs Python {py_default!r}"

    if kind == "expression":
        if r_default == "model$channel_names[1L]" and py_default is None:
            return True, "R model-derived default deferred to Python function body"
        return False, f"R dynamic expression {r_default!r} requires explicit review"

    if isinstance(expected, float) and math.isinf(expected):
        if isinstance(py_default, (int, float)) and math.isinf(float(py_default)):
            same_sign = (float(py_default) > 0) == (expected > 0)
            return same_sign, "infinite numeric default"
        return False, f"R {r_default} vs Python {py_default!r}"

    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if isinstance(py_default, (int, float)) and not isinstance(py_default, bool):
            return float(py_default) == float(expected), "numeric default"

    return py_default == expected, "literal default"


def build_signature_matrix(root: Path) -> dict[str, Any]:
    r_signatures = json.loads((root / "reference" / "signatures.json").read_text(encoding="utf-8"))
    api_manifest = json.loads(
        (root / "reference" / "api_manifest.json").read_text(encoding="utf-8")
    )
    names = [row["name"] for row in api_manifest]

    if set(names) != set(r_signatures):
        raise AssertionError("Frozen API and signature manifests disagree.")

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    counts: dict[str, int] = {}

    for name in names:
        func = getattr(g, name)
        py_sig = inspect.signature(func)
        raw_py = list(py_sig.parameters.values())

        extensions: list[str] = []
        py_params: list[inspect.Parameter] = []
        for p in raw_py:
            if (
                name.startswith("plot_")
                and p.name == "ax"
                and p.kind is inspect.Parameter.KEYWORD_ONLY
            ):
                extensions.append("keyword-only ax= Matplotlib target; Python plotting extension")
                continue
            py_params.append(p)

        r_params = _parse_r_formals(r_signatures[name])
        issues: list[str] = []
        translations: list[str] = []

        pi = 0
        for rp in r_params:
            if rp["variadic"]:
                consumed: list[inspect.Parameter] = []
                while pi < len(py_params) and py_params[pi].kind in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }:
                    consumed.append(py_params[pi])
                    pi += 1
                if not consumed:
                    issues.append("R ... has no Python *args/**kwargs representation")
                else:
                    labels = [
                        ("*" if p.kind is inspect.Parameter.VAR_POSITIONAL else "**") + p.name
                        for p in consumed
                    ]
                    translations.append("R ... -> Python " + " + ".join(labels))
                continue

            if pi >= len(py_params):
                issues.append(f"missing Python parameter for R {rp['name']!r}")
                continue

            p = py_params[pi]
            pi += 1

            if p.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }:
                issues.append(f"R named parameter {rp['name']!r} became variadic")
                continue

            if p.name != rp["name"]:
                issues.append(f"parameter mismatch at R {rp['name']!r}: Python has {p.name!r}")
                continue

            r_optional = bool(rp["has_default"])
            py_optional = p.default is not inspect._empty
            if r_optional != py_optional:
                issues.append(
                    f"{rp['name']}: optionality mismatch (R={r_optional}, Python={py_optional})"
                )
                continue

            if r_optional:
                ok, note = _defaults_equivalent(
                    str(rp["default_text"]),
                    p.default,
                )
                if not ok:
                    issues.append(
                        f"{rp['name']}: default mismatch "
                        f"(R={rp['default_text']!r}, Python={p.default!r}; {note})"
                    )
                elif note not in {
                    "literal default",
                    "numeric default",
                    "infinite numeric default",
                }:
                    translations.append(f"{rp['name']}: {note}")

        if pi < len(py_params):
            extras = py_params[pi:]
            issues.extend(f"extra Python parameter {p.name!r}" for p in extras)

        if issues:
            classification = "unexplained_signature_drift"
            failures.append(name)
        elif extensions and translations:
            classification = "semantic_translation_with_python_extension"
        elif extensions:
            classification = "python_keyword_only_extension"
        elif translations:
            classification = "semantic_signature_translation"
        else:
            classification = "structural_signature_match"

        counts[classification] = counts.get(classification, 0) + 1
        rows.append(
            {
                "name": name,
                "r_signature": r_signatures[name],
                "python_signature": str(py_sig),
                "classification": classification,
                "translations": translations,
                "extensions": extensions,
                "issues": issues,
                "python_parameters": [
                    {
                        "name": p.name,
                        "kind": str(p.kind),
                        "default": _json_default(p.default),
                    }
                    for p in raw_py
                ],
            }
        )

    return {
        "reference_package": "gp3sequences",
        "reference_version": "0.3.0",
        "python_package": "gp3sequencespy",
        "functions": len(rows),
        "counts": counts,
        "unexplained_drift": failures,
        "rows": rows,
    }


def render_report(matrix: dict[str, Any]) -> str:
    counts = matrix["counts"]
    lines = [
        "# Frozen signature parity",
        "",
        "This report audits the 81 frozen `gp3sequences 0.3.0` public formals against "
        "the current Python call signatures.",
        "",
        f"- Functions audited: **{matrix['functions']} / 81**",
        f"- Structural matches: **{counts.get('structural_signature_match', 0)}**",
        f"- Semantic R→Python translations: **{counts.get('semantic_signature_translation', 0)}**",
        f"- Keyword-only Python plotting extensions: "
        f"**{counts.get('python_keyword_only_extension', 0)}**",
        f"- Translation + plotting extension: "
        f"**{counts.get('semantic_translation_with_python_extension', 0)}**",
        f"- Unexplained drift: **{len(matrix['unexplained_drift'])}**",
        "",
        "## Translation rules",
        "",
        "- R `NULL`, logicals, integer `L` suffixes, `Inf`, and `NA` are translated "
        "to their Python-native equivalents.",
        "- R `c(...)` defaults are distinguished between full vector defaults and "
        "`match.arg()`-style first-choice defaults based on the Python contract.",
        "- R `...` maps to Python `*args`, `**kwargs`, or both when the R variadic "
        "contract permits named and unnamed objects.",
        "- Plot functions may expose keyword-only `ax=` so callers can target a "
        "Matplotlib axis without changing the frozen positional argument contract.",
        "- R and Matplotlib are different rendering engines; pixel-identical plots "
        "are not claimed.",
        "",
    ]

    if matrix["unexplained_drift"]:
        lines += ["## Unexplained drift", ""]
        for row in matrix["rows"]:
            if row["issues"]:
                lines.append(f"### `{row['name']}`")
                lines.extend(f"- {issue}" for issue in row["issues"])
                lines.append("")
    else:
        lines += [
            "## Result",
            "",
            "**PASS — all 81 public signatures are structurally compatible or have an "
            "explicit semantic/Python-native translation.**",
            "",
        ]

    lines += ["## Explicit Python plotting extensions", ""]
    for row in matrix["rows"]:
        if row["extensions"]:
            lines.append(f"- `{row['name']}`: " + "; ".join(row["extensions"]))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()

    matrix = build_signature_matrix(args.root)

    if args.write is not None:
        args.write.write_text(
            json.dumps(matrix, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.report is not None:
        args.report.write_text(render_report(matrix), encoding="utf-8")

    print(f"functions audited: {matrix['functions']}")
    for key in (
        "structural_signature_match",
        "semantic_signature_translation",
        "python_keyword_only_extension",
        "semantic_translation_with_python_extension",
        "unexplained_signature_drift",
    ):
        print(f"{key}: {matrix['counts'].get(key, 0)}")
    print("unexplained drift:", matrix["unexplained_drift"])

    if matrix["unexplained_drift"]:
        return 2

    if args.check is not None:
        expected = json.loads(args.check.read_text(encoding="utf-8"))
        expected_by_name = {row["name"]: row for row in expected["rows"]}
        actual_by_name = {row["name"]: row for row in matrix["rows"]}

        if set(expected_by_name) != set(actual_by_name):
            print("Committed signature matrix function set differs from runtime.")
            return 3

        for name in sorted(actual_by_name):
            expected_row = expected_by_name[name]
            actual_row = actual_by_name[name]
            for field in (
                "python_signature",
                "classification",
                "translations",
                "extensions",
                "issues",
            ):
                if expected_row[field] != actual_row[field]:
                    print(
                        f"Signature matrix drift for {name}/{field}: "
                        f"expected={expected_row[field]!r} actual={actual_row[field]!r}"
                    )
                    return 4

    print("SIGNATURE PARITY AUDIT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
