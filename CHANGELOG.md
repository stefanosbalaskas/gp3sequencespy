# Changelog

All notable changes to `gp3sequencespy` are documented here. The project is
currently alpha software and follows parity-first development against the frozen
R package `gp3sequences` 0.3.0.

## [Unreleased]

### Planned before 0.1.0

- Execute the deterministic R ↔ Python oracle against the frozen R 0.3.0 tarball.
- Review and close or explicitly retain every item in `PARITY_EXCEPTIONS.md`.
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
themselves establish exact numerical parity for R RNG streams, selected
clustering details, ecosystem-specific adapter objects, or the `mgcv`
time-varying model.
