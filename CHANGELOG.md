# Changelog

All notable changes to `gp3sequencespy` are documented here. The project follows parity-first development against the frozen R package
`gp3sequences` 0.3.0.

## [Unreleased]

No changes yet.

## [0.1.2] - 2026-08-31

### Added

- Complete quality-completion test tranche covering every reachable statement and branch.
- Mutation-smoke companion oracles for pseudocount normalization, empty subsequences, and distance-diagonal validation.
- Dedicated coverage ledger and quality-snapshot workflows, plus expanded user-facing documentation, examples, method maps, plot guidance, reporting guidance, and reproducibility material.
- Guarded release orchestration and post-PyPI verification workflows for exact-artifact stable releases.

### Changed

- Hardened sequence preparation for PyArrow/pandas-backed cumulative operations.
- Made grouped plotting paths robust to missing grouping values while preserving the frozen plotting contracts.
- Removed unreachable defensive branches identified during full branch-coverage review.
- Canonically formatted the quality-completion test suite with Ruff.

### Validation

- **292 / 292** Python tests pass.
- **4,564 / 4,564** executable statements covered (**100.00%**).
- **1,702 / 1,702** branches covered (**100.00%**).
- Mutation smoke: **3 / 3** mutants killed (**100%**).
- Linux, macOS, and Windows CI passes across Python 3.11–3.14.
- Ruff lint/format, mypy, frozen API, frozen R-block ledger, frozen signature parity, strict MkDocs, wheel build, and fresh-wheel smoke all pass.

### Scientific/API status

- No breaking public scientific API or signature changes.
- Frozen R 0.3.0 reference remains unchanged.
- Frozen API remains **81 / 81**.
- Frozen R test-block ledger remains **130 / 130**.
- Frozen public signatures remain **81 / 81** with **0 unexplained drift**.

## [0.1.1] - 2026-08-30

### Added

- Registered PyPI Trusted Publishing workflow for stable GitHub Releases, using
  the dedicated `pypi` environment and job-scoped OIDC permissions.
- `PYPI_PUBLISHING.md` and a machine-readable 0.1.0 publication record.
- Zenodo archival DOI `10.5281/zenodo.22166449` in citation and project metadata.

### Changed

- Corrected the PyPI-facing README so the current release is no longer described
  as an unpublished release candidate.
- Upgraded and exactly pinned GitHub Actions used by CI, documentation, release
  validation, and trusted publication.
- Made `release-check.yml` derive the package version from `pyproject.toml`
  instead of hard-coding `0.1.0`.
- Updated release documentation to record the completed GitHub and PyPI 0.1.0
  publication and active Trusted Publisher configuration.

### Scientific/API status

- No scientific algorithms, public function signatures, plotting semantics, or
  frozen R 0.3.0 parity contracts changed.
- Frozen API remains **81 / 81**.
- Frozen R test-block ledger remains **130 / 130**.
- Frozen public signatures remain **81 / 81** with **0 unexplained drift**.
- The Python validation suite remains **182 tests**.

## [0.1.0] - 2026-08-30

### Added

- First non-prerelease Python release preserving all **81 / 81** frozen
  `gp3sequences 0.3.0` public function counterparts.
- **130 / 130** dedicated translations of the frozen R `test_that()` blocks.
- Fifteen Python-native article/vignette counterparts, MkDocs documentation,
  release governance, and multi-platform CI across Python 3.11–3.14.
- Machine-readable frozen API, test-block, signature, and oracle records.

### Changed

- Replaced the early statsmodels/Patsy time-model approximation with a validated
  `mssm` binomial GAMM backend using penalized by-group smooths and genuine
  participant random intercepts.
- Restored frozen plotting defaults and retained Matplotlib `ax=` only as a
  keyword-only Python extension.
- Aligned hierarchical clustering and medoid semantics with R `hclust()`/PAM,
  including `members=` behavior and tie-sensitive medoid scoring.

### Validation

- **182** Python tests pass locally before the release-candidate artifact freeze.
- Frozen API: **81 / 81**.
- Frozen R block ledger: **130 / 130**.
- Frozen public signatures: **81 / 81**, with **0 unexplained drift**.
- Deterministic six-contract R↔Python oracle: **PASS**.
- Extended clustering oracle: **3915 / 3915** partition rows and **108 / 108**
  medoid rows matched, plus fresh `members=` oracle **PASS**.
- Time-model calibration: **12 / 12** `k=3/4/5 × state/transition × random-effect`
  scenarios fit successfully within the validated R-error envelope; frozen-R
  transition extrapolation matched to an absolute difference of approximately
  `8.29e-06`.
- Exact final-version wheel and sdist must pass clean-environment artifact tests
  before this commit can be pushed by the RC transaction.

### Deliberate parity boundaries

The stable release retains the explicitly reviewed boundaries in
`PARITY_EXCEPTIONS.md`: ecosystem-specific R object identity, plotting-engine
identity, cross-language RNG stream identity, and bit-for-bit `mgcv` identity /
non-default smoothing criteria are not claimed.

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
