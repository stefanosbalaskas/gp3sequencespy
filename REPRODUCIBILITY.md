# Reproducibility and frozen reference

## Authoritative R reference

The initial Python parity target is `gp3sequences` **0.3.0**. The canonical frozen R artifact used during the port has SHA-256:

```text
1d2ca1d72ebd375292fc9bdd0f41848b8224f9e1ae9d34acbd9469f103bf5b8d
```

The corresponding R repository release commit is:

```text
4ebf0bebea2955c5f98f8ddf0fe03e81d0b7ac3a
```

A locally rebuilt final tarball from that release commit has SHA-256:

```text
4024a6657d4567e44615cdf87419654bd097822016c8b84bd929aa3db4dcd3a8
```

Because R source tarballs can differ at the archive/build-metadata level, source equivalence was verified file-by-file against the canonical artifact. After normalizing build-only `DESCRIPTION` fields (`Packaged`, `Repository`, `Date/Publication`, and `Roxygen`) and excluding generated `MD5` and `build/vignette.rds`, all **199 stable files** matched. The normalized manifest SHA-256 is:

```text
4dd1566e38cb20da1115fc466cc6db3b99f98413aa93876402f59221fc954e56
```

## Cross-language validation

The deterministic oracle was executed on Windows with **R 4.6.1**.

Validated core contracts:

- state summary
- transition summary
- formatted sequence paths
- motif summary
- consensus sequence
- Levenshtein distance

All six canonicalized CSV contracts matched.

An extended clustering oracle subsequently compared R and Python cluster co-membership and medoids across four shared distance fixtures, `k = 2..4` where defined, all eight frozen hierarchical linkages, and deterministic PAM. The resulting R-hclust regression behavior is covered by `tests/test_r_hclust_oracle_regressions.py`.

## Reproducing Python validation

```bash
uv sync --extra dev --extra time --extra docs --extra release
uv run ruff check src tests parity
uv run ruff format --check src tests parity
uv run mypy src/gp3sequencespy
uv run pytest -q
uv run mkdocs build --strict
uv build
uv run twine check --strict dist/*
```

## Time-varying model validation

The former statsmodels/Patsy approximation was benchmarked against frozen R 0.3.0 `mgcv::gam()` and replaced by `mssm` 1.2.5. The first benchmark covered four deterministic state/transition × random-effect scenarios; `mssm` had lower estimate MAE in 3/4 scenarios with a median mssm/current MAE ratio of **0.094519**, and reproduced the transition-model time-18 extrapolation (`R = 0.1906916`, `mssm = 0.19068331`) while Patsy failed outside its stored spline knots.

A second calibration covered **12 / 12** combinations of `k = 3, 4, 5`, state/transition outcomes, and participant random effect on/off. All fits succeeded. The `k=3` estimate MAEs were approximately 0.00320 for state models and 0.00143 for transition models; transition MAEs remained below 0.0036 for `k=4/5`. The Python implementation therefore uses `mssm` GAMMs as the closest validated Python-native analogue. Exact coefficient/penalty identity with `mgcv` is not claimed, and non-default `mgcv` smoothing criteria remain outside the validated Python contract. See `PARITY_EXCEPTIONS.md`.
