# Cross-language parity harness

This directory separates **translated behavioral tests** from **actual R↔Python oracle comparisons**.

- `fixtures/`: deterministic, vendor-neutral sequence fixtures shared by R and Python.
- `r_scripts/`: scripts that install the frozen R 0.3.0 tarball into a temporary library and emit canonical reference tables.
- `generate_python_outputs.py`: emits the equivalent Python tables.
- `canonicalizers/`: comparison rules that sort by semantic keys and compare numeric values with explicit tolerances.
- `actual/`: generated run outputs; these should not be treated as source-of-truth artifacts.
- `reports/`: generated comparison reports.
- `expected/`: provenance instructions for the authoritative frozen R artifact.

The first oracle tranche covers state summaries, transition summaries, formatted paths, motif summaries, consensus sequences, and Levenshtein distances. Stochastic models and known backend-specific exceptions remain outside exact numerical comparison until separate canonicalisation rules are validated.
