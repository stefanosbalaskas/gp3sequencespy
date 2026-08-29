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

## Frozen signature parity

All **81 / 81** frozen R public formals were audited against the current Python
call signatures. The executable audit is `parity/signature_audit.py`, its
machine-readable freeze is `reference/signature_parity_matrix.json`, and the
human-readable report is `SIGNATURE_PARITY.md`.

The audit reports **0 unexplained signature drifts**. R-specific language
constructs such as `NULL`, `NA`, `c(...)`, and `...` are translated explicitly.
Matplotlib plot helpers retain a Python-native **keyword-only** `ax=` extension
without changing the frozen positional argument contract. Frozen defaults that
had drifted (`scale`, `Viridis`, and `Dark 3`) were restored.

Classification counts:

```text
structural_signature_match = 37
semantic_signature_translation = 29
python_keyword_only_extension = 0
semantic_translation_with_python_extension = 15
unexplained_signature_drift = 0
```

## Stable 0.1.0 release-candidate policy

On 2026-08-30, the remaining deliberate parity boundaries were reviewed and retained
with rationale in `PARITY_EXCEPTIONS.md`. The 0.1.0 transaction commits the final
versioned source **before** building release artifacts, then validates the exact
wheel and sdist produced from that commit in fresh environments. Artifact SHA-256
hashes and the candidate commit are exported in an external release-candidate
manifest so the source tree does not self-reference hashes of artifacts that
contain that source.

The `v0.1.0` tag and PyPI publication were intentionally separate actions.

## Stable 0.1.0 publication identity

The release cycle completed on 2026-08-30. The annotated `v0.1.0` tag resolves to:

```text
28f06a571889bf9db760d00c47e1252d3836679a
```

The exact GitHub Release artifacts were then published to production PyPI.
PyPI's JSON API independently reported the same SHA-256 values:

```text
gp3sequencespy-0.1.0-py3-none-any.whl
97725d0b34872b79c9f9cb4da57f14a788a8920880a0a415c13669d281a39525

gp3sequencespy-0.1.0.tar.gz
e01ff3ac4ec0cbede48b1019e4bcabddd38b9587df3fe541ce66aff585bf7e19
```

The historical `reference/release_candidate_contract_0.1.0.json` is retained as
the pre-tag/pre-PyPI RC record. Final publication state is recorded separately
in `reference/release_publication_0.1.0.json`.

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
