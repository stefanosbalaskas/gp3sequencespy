from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import gp3sequencespy as g


def write_table(frame: pd.DataFrame, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_dir / f"{name}.csv", index=False, na_rep="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic gp3sequencespy parity outputs.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    out_dir = (args.out_dir or root / "parity" / "actual" / "python").resolve()
    data = pd.read_csv(root / "parity" / "fixtures" / "minimal.csv")

    states = g.summarise_sequence_states(data, "sequence_id", "sequence_order", "state")
    write_table(states.overall, out_dir, "state_summary_overall")

    transitions = g.summarise_sequence_transitions(data, "sequence_id", "sequence_order", "state")
    write_table(transitions.overall, out_dir, "transition_summary_overall")

    paths = g.format_sequence_paths(
        data,
        "sequence_id",
        "sequence_order",
        "state",
        metadata_cols="group",
    )
    write_table(paths.paths, out_dir, "formatted_paths")

    extracted = g.extract_sequence_ngrams(
        data,
        "sequence_id",
        "sequence_order",
        "state",
        min_length=2,
        max_length=3,
        overlap="allow",
    )
    motifs = g.summarise_sequence_motifs(extracted)
    write_table(motifs.overall, out_dir, "motif_summary_overall")

    consensus = g.create_consensus_sequence(data)
    write_table(consensus, out_dir, "consensus")

    distance = g.compute_sequence_distance(data, method="levenshtein")
    distance_out = pd.DataFrame(distance.matrix, index=distance.labels, columns=distance.labels)
    distance_out.insert(0, "sequence_id", distance.labels)
    write_table(distance_out.reset_index(drop=True), out_dir, "distance_levenshtein")

    (out_dir / "oracle_metadata.txt").write_text(
        f"package=gp3sequencespy\nversion={g.__version__}\n",
        encoding="utf-8",
    )
    print(f"Wrote Python parity outputs to: {out_dir}")


if __name__ == "__main__":
    main()
