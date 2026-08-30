from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the gp3sequencespy coverage deficit ledger."
    )
    parser.add_argument("coverage_json", type=Path)
    parser.add_argument("--markdown", type=Path, default=Path("coverage-ledger.md"))
    parser.add_argument("--json", dest="json_out", type=Path, default=Path("coverage-ledger.json"))
    parser.add_argument("--require-statements", type=float, default=None)
    parser.add_argument("--require-branches", type=float, default=None)
    args = parser.parse_args()

    raw = json.loads(args.coverage_json.read_text(encoding="utf-8"))
    totals = raw["totals"]
    rows = []
    for path, rec in raw["files"].items():
        if not path.startswith("src/gp3sequencespy/"):
            continue
        summary = rec["summary"]
        rows.append(
            {
                "path": path,
                "statement_percent": summary.get("percent_statements_covered", 100.0),
                "branch_percent": summary.get("percent_branches_covered", 100.0),
                "combined_percent": summary.get("percent_covered", 100.0),
                "missing_lines": summary.get("missing_lines", 0),
                "missing_branches": summary.get("missing_branches", 0),
                "missing_line_numbers": rec.get("missing_lines", []),
                "missing_branch_arcs": rec.get("missing_branches", []),
            }
        )
    rows.sort(key=lambda row: (row["combined_percent"], row["path"]))

    ledger = {
        "totals": totals,
        "targets": {
            "statements": args.require_statements,
            "branches": args.require_branches,
        },
        "files": rows,
    }
    args.json_out.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Coverage deficit ledger",
        "",
        f"- Statement coverage: **{totals['percent_statements_covered']:.3f}%**",
        f"- Branch coverage: **{totals['percent_branches_covered']:.3f}%**",
        f"- Missing statements: **{totals['missing_lines']}**",
        f"- Missing branches: **{totals['missing_branches']}**",
        "",
        "| Module | Statements | Branches | Missing lines | Missing branches |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        md.append(
            f"| `{row['path']}` | {row['statement_percent']:.2f}% | "
            f"{row['branch_percent']:.2f}% | {row['missing_lines']} | {row['missing_branches']} |"
        )
    args.markdown.write_text("\n".join(md) + "\n", encoding="utf-8")

    failed = False
    if (
        args.require_statements is not None
        and totals["percent_statements_covered"] + 1e-12 < args.require_statements
    ):
        failed = True
    if (
        args.require_branches is not None
        and totals["percent_branches_covered"] + 1e-12 < args.require_branches
    ):
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
