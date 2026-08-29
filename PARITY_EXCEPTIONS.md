# Parity exceptions and validation status

The frozen behavioral reference is **gp3sequences 0.3.0**. Python functions retain the frozen R public names, but R-specific runtime objects cannot always be represented identically in Python.

## Validated deterministic cross-language parity

The deterministic oracle was executed on Windows with **R 4.6.1** against a locally rebuilt final `gp3sequences 0.3.0` tarball from release commit `4ebf0bebea2955c5f98f8ddf0fe03e81d0b7ac3a`.

The local final tarball has archive SHA-256:

```text
4024a6657d4567e44615cdf87419654bd097822016c8b84bd929aa3db4dcd3a8
```

It was proven source-equivalent to the canonical frozen artifact after normalizing build-only `DESCRIPTION` fields and excluding generated build artifacts. The normalized 199-file source manifest has SHA-256:

```text
4dd1566e38cb20da1115fc466cc6db3b99f98413aa93876402f59221fc954e56
```

The core deterministic oracle matched all six canonical CSV contracts: state summaries, transition summaries, formatted paths, motif summaries, consensus sequences, and Levenshtein distances.

The extended clustering oracle also validates R-compatible hierarchical partitions and medoids for `single`, `complete`, `average`, `mcquitty`, `median`, `centroid`, `ward.D`, and `ward.D2` across four tie-resistant fixtures and multiple `k` values, plus deterministic PAM behavior. Regression tests preserve the discovered R `hclust()` semantics.

## Explicit backend-object translations

- `as_traminer_sequences()` returns a structured wide-sequence Python adapter rather than a TraMineR `stslist` S3 object.
- `as_seqhmm_sequences()` returns the same structured observations tagged for the seqHMM handoff rather than an R `stslist`.
- `as_arules_sequences()` returns itemsets plus cSPADE-compatible `sequenceID`/`eventID` metadata rather than an R `transactions` S4 object.
- `as_igraph_transition_network()` returns a NetworkX graph with the corresponding edge attributes rather than an R igraph object.

These are deliberate semantic translations. Their data contracts are tested; object identity with the R backend is not claimed.

## Remaining deliberate/non-exact numerical boundaries

- **Randomised algorithms:** NumPy and R use different random-number generators and streams. The parity target is deterministic behavior for a declared Python seed, global-RNG isolation, and equivalent statistical/algorithmic contracts—not bit-for-bit identity of cross-language random draws.
- **Time-varying sequence models:** the statsmodels/Patsy approximation has been replaced by `mssm` 1.2.5, using a binomial GAMM with a group main effect, separate penalized time smooths by group, and a genuine participant random intercept when requested. The documented `mgcv k -> mssm nk=k-1` mapping is used, with an adaptive spline degree at the frozen public minimum `k=3`. Population prediction excludes the participant random effect, as frozen R `predict.gam(..., exclude='s(.participant)')` does. Cross-language calibration covered state/transition outcomes, random effect on/off, `k=3/4/5`, and out-of-support transition prediction. This is a validated close semantic translation, not a claim of bit-for-bit `mgcv` identity. The Python backend intentionally supports the verified frozen default `method='REML'`; other `mgcv::gam()` smoothing criteria remain an explicit unsupported non-default boundary.

## Frozen-test translation status

All **130 / 130** frozen R `test_that()` blocks have one dedicated Python translation test. The mapping is machine-readable in `reference/test_parity_matrix.json` and human-readable in `PARITY_TEST_MATRIX.md`.

Behavioral-contract coverage, deterministic oracle coverage, and deliberate backend translations are reported separately so that one does not overstate the other.
