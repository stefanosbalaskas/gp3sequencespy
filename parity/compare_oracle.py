from __future__ import annotations

import argparse
import sys
from pathlib import Path

from canonicalizers.csv_contracts import CONTRACTS, compare_frames, load_canonical


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare frozen-R and Python deterministic parity outputs.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--r-dir", type=Path, default=None)
    parser.add_argument("--python-dir", type=Path, default=None)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    r_dir = (args.r_dir or root / "parity" / "actual" / "r").resolve()
    py_dir = (args.python_dir or root / "parity" / "actual" / "python").resolve()

    failures: list[str] = []
    for name, contract in CONTRACTS.items():
        r_path, py_path = r_dir / f"{name}.csv", py_dir / f"{name}.csv"
        if not r_path.exists() or not py_path.exists():
            failures.append(f"{name}: missing output (R={r_path.exists()}, Python={py_path.exists()})")
            continue
        r_frame = load_canonical(r_path, contract)
        py_frame = load_canonical(py_path, contract)
        errors = compare_frames(r_frame, py_frame, contract.numeric_tolerance)
        failures.extend(f"{name}: {error}" for error in errors)

    report_dir = root / "parity" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "deterministic_oracle_report.txt"
    if failures:
        report.write_text("FAIL\n" + "\n".join(failures) + "\n", encoding="utf-8")
        print(report.read_text(encoding="utf-8"), end="")
        return 1
    report.write_text("PASS\nAll deterministic oracle CSV contracts matched.\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
