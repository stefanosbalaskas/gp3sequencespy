from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[1]


def test_frozen_r_block_ledger_is_complete_and_unique():
    matrix = json.loads(
        (ROOT / "reference" / "test_parity_matrix.json").read_text(encoding="utf-8")
    )
    assert len(matrix) == 130
    assert len({(row["r_test_file"], row["r_block_index"]) for row in matrix}) == 130
    assert len({row["python_test"] for row in matrix}) == 130
    for row in matrix:
        test_path, test_name = row["python_test"].split("::", 1)
        source = (ROOT / test_path).read_text(encoding="utf-8")
        assert f"def {test_name}(" in source


def test_python_oracle_fixture_generates_stable_contract_tables(tmp_path):
    generator = ROOT / "parity" / "generate_python_outputs.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(generator),
            "--repo-root",
            str(ROOT),
            "--out-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Wrote Python parity outputs to:" in completed.stdout

    expected = {
        "state_summary_overall.csv",
        "transition_summary_overall.csv",
        "formatted_paths.csv",
        "motif_summary_overall.csv",
        "consensus.csv",
        "distance_levenshtein.csv",
        "oracle_metadata.txt",
    }
    assert expected == {p.name for p in tmp_path.iterdir()}
    state = pd.read_csv(tmp_path / "state_summary_overall.csv")
    distance = pd.read_csv(tmp_path / "distance_levenshtein.csv")
    assert state.state.tolist() == ["A", "B", "C", "D"]
    assert distance.sequence_id.tolist() == ["s1", "s2", "s3", "s4"]
