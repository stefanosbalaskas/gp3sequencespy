from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "gp3sequencespy"

MUTATIONS = [
    (
        "vector-normalisation-removes-pseudocount",
        "_advanced.py",
        "x = np.asarray(x, float) + pseudocount",
        "x = np.asarray(x, float) + 0.0",
        ["tests/test_property_invariants.py"],
    ),
    (
        "subsequence-empty-pattern-becomes-present",
        "inference.py",
        "if not pattern or len(pattern) > len(sequence):\n        return False",
        "if len(pattern) > len(sequence):\n        return False",
        ["tests/test_quality_edge_contracts.py"],
    ),
    (
        "distance-diagonal-validation-disabled",
        "_advanced.py",
        "if np.max(np.abs(np.diag(mat))) > tol:",
        "if False and np.max(np.abs(np.diag(mat))) > tol:",
        ["tests/test_quality_edge_contracts.py"],
    ),
]


def main() -> int:
    killed = 0
    with tempfile.TemporaryDirectory(prefix="gp3seq-mut-") as tmp:
        base = Path(tmp) / "src" / "gp3sequencespy"
        shutil.copytree(SRC, base)
        for name, rel, old, new, tests in MUTATIONS:
            target = base / rel
            original = target.read_text(encoding="utf-8")
            if old not in original:
                print(f"ERROR {name}: source pattern not found", file=sys.stderr)
                return 2
            target.write_text(original.replace(old, new, 1), encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(tmp) / "src") + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *tests],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            target.write_text(original, encoding="utf-8")
            if proc.returncode != 0:
                killed += 1
                print(f"KILLED {name}")
            else:
                print(f"SURVIVED {name}")
                print(proc.stdout)
    total = len(MUTATIONS)
    print(f"mutation smoke score: {killed}/{total} = {100 * killed / total:.1f}%")
    return 0 if killed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
