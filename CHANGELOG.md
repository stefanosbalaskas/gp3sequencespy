# Changelog

All notable changes to `gp3sequencespy` are documented here. The project is
currently alpha software and follows parity-first development against the frozen
R package `gp3sequences` 0.3.0.

## [Unreleased]

### Changed

- Replaced the statsmodels/Patsy time-varying-model approximation with an `mssm` binomial GAMM backend using penalized by-group smooths and genuine participant random intercepts.
- Population-level time-model prediction now excludes participant random effects and supports the same finite out-of-support time inputs accepted by the frozen R API.
- Preserved the frozen public `k >= 3` contract with validated `k=3/4/5` mssm mappings.

### Validation

- Audited all 81 frozen R public signatures, repaired plotting-default drift, and froze the executable signature matrix with zero unexplained differences.
- Added six focused mssm time-backend regression tests.
- Validated 12 / 12 small-k state/transition × random-effect scenarios against frozen R `mgcv::gam()` outputs.
- Validated transition extrapolation against frozen R (`0.1906916` vs `0.19068331` in the benchmark fixture).

### Planned before 0.1.0

- Review and close or explicitly retain every remaining item in `PARITY_EXCEPTIONS.md`.
- Perform an exact-artifact release candidate install and documentation build.
- Freeze the final 0.1.0 metadata, tag, and release notes.

## [0.1.0a1] - 2026-08-29

### Added

- 81 / 81 frozen R 0.3.0 public API counterparts.
- 130 / 130 frozen R `test_that()` block translations.
- Data validation, preparation, summaries, sequence distances, clustering,
  consensus, motifs, transition networks, higher-order models, HMM families,
  panel workflows, subsequence mining, inference, time-varying models, adapters,
  audits, and visualisations.
- Cross-language parity harness with deterministic oracle fixtures.
- Ruff and mypy release-quality gates.
- Linux, macOS, and Windows CI on Python 3.11–3.14.
- Fifteen Python-native ports of the frozen R vignette set.
- MkDocs documentation and GitHub Pages deployment.

### Validation

- 162 tests passing before the release-readiness tranche.
- 81 / 81 public API contract.
- 130 / 130 frozen R test-block ledger.
- Wheel and source distribution build smoke tests.

### Known parity boundaries

See `PARITY_EXCEPTIONS.md`. API and behavioral-contract coverage do not by
themselves establish exact numerical parity for R RNG streams, cross-language RNG streams, ecosystem-specific adapter objects, or explicitly documented backend boundaries.
