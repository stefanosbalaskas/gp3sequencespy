# Parity exceptions and validation status

The frozen behavioral reference is **gp3sequences 0.3.0**. Python functions retain the frozen R public names, but R-specific runtime objects cannot always be represented identically in Python.

## Explicit backend-object translations

- `as_traminer_sequences()` returns a structured wide-sequence Python adapter rather than a TraMineR `stslist` S3 object.
- `as_seqhmm_sequences()` returns the same structured observations tagged for the seqHMM handoff rather than an R `stslist`.
- `as_arules_sequences()` returns itemsets plus cSPADE-compatible `sequenceID`/`eventID` metadata rather than an R `transactions` S4 object.
- `as_igraph_transition_network()` returns a NetworkX graph with the corresponding edge attributes rather than an R igraph object.

These are deliberate semantic translations. Their data contracts are tested; object identity with the R backend is not claimed.

## Numerical parity still requiring an executable R oracle

- Hierarchical clustering methods where SciPy and R `hclust()` implementation details may differ, especially `ward.D`, `ward.D2`, and `mcquitty`.
- Randomised algorithms because NumPy and R use different random-number generators and streams.
- Time-varying sequence models: the R reference uses `mgcv::gam()` with smooths and participant random effects; the current Python alpha uses a statsmodels binomial GLM with group-specific Patsy B-spline bases and optional participant fixed effects. This is a functional approximation, not numerical mgcv parity.

No stable release should claim exact cross-language numerical parity for these items until the R oracle suite is executable in CI or a validated parity environment.

## Frozen-test translation status

All **130 / 130** frozen R `test_that()` blocks now have one dedicated Python translation test. The mapping is machine-readable in `reference/test_parity_matrix.json` and human-readable in `PARITY_TEST_MATRIX.md`. These tests validate behavioral contracts in Python; they do not convert the explicitly listed numerical or backend-object exceptions into exact parity claims.

## Cross-language oracle harness

The `parity/` harness pins the authoritative R 0.3.0 tarball SHA-256 and provides deterministic R/Python output generation plus canonical CSV comparison for state summaries, transition summaries, formatted paths, motif summaries, consensus sequences, and Levenshtein distances. The current development container has no R executable, so the R side of that harness has **not** been executed here. Exact oracle results must therefore be reported only after an R-enabled validation run.
