# Release checklist

This checklist separates **release readiness** from **R numerical parity**. A green Python test suite is necessary but not sufficient for a stable parity claim.

## Always required

- [ ] `ruff check src tests parity` passes.
- [ ] `ruff format --check src tests parity` passes.
- [ ] `mypy src/gp3sequencespy` passes.
- [ ] Full pytest suite passes on Python 3.11–3.14 across Linux, macOS, and Windows.
- [ ] 81 / 81 frozen public API functions are present.
- [ ] 130 / 130 frozen R test blocks remain mapped.
- [ ] `mkdocs build --strict` passes.
- [ ] Wheel and sdist build successfully.
- [ ] `twine check --strict dist/*` passes.
- [ ] Fresh-wheel import succeeds in a clean environment.
- [ ] `CHANGELOG.md`, `CITATION.cff`, README, and documentation reflect the candidate version.

## Required before stable 0.1.0

- [x] Identify the canonical frozen `gp3sequences 0.3.0` artifact/hash.
- [x] Prove source equivalence of the locally rebuilt final 0.3.0 tarball.
- [x] Execute `parity/r_scripts/generate_reference_outputs.R` under R 4.6.1 against the validated frozen 0.3.0 source.
- [x] Execute the Python deterministic oracle generator.
- [x] Compare the six deterministic core contracts.
- [x] Investigate and repair deterministic hierarchical-clustering mismatches.
- [x] Validate all eight hierarchical linkage families and deterministic PAM against the extended R oracle fixtures.
- [x] Benchmark frozen R `mgcv::gam()` against the old Python backend and `mssm 1.2.5` on state/transition × random-effect on/off scenarios.
- [x] Validate the `mssm` mapping for `k=3`, `k=4`, and `k=5` across all 12 state/transition × random-effect scenarios.
- [x] Validate population prediction and out-of-support transition prediction against frozen R.
- [x] Audit all 81 frozen R public formals against Python signatures and classify every R→Python translation.
- [x] Repair frozen plotting defaults and make the Python-only `ax=` hook keyword-only.
- [x] Review every remaining entry in `PARITY_EXCEPTIONS.md`; retain only deliberate translations with explicit rationale.
- [x] Replace the statsmodels/Patsy time-model approximation with the validated `mssm` GAMM backend.
- [x] Run exact built-artifact tests from the final `0.1.0` release candidate wheel/sdist.
- [x] Freeze version `0.1.0` and release notes after parity-exception review.
- [x] Create tag `v0.1.0` only after the exact RC commit is green in GitHub CI and the `Release checks` workflow.

## Publication

### 0.1.0

- [x] Publish the exact frozen `0.1.0` wheel and sdist to production PyPI.
- [x] Re-query PyPI and verify the published wheel and sdist SHA-256 values match
  the frozen GitHub Release artifacts.
- [x] Preserve the GitHub `v0.1.0` tag and assets unchanged after PyPI publication.

### 0.1.1 metadata maintenance release

- [x] Preserve the frozen 81-function scientific API and R 0.3.0 parity contracts.
- [x] Correct stale PyPI-facing release-candidate wording.
- [x] Record the Zenodo archival DOI in citation/project metadata.
- [x] Keep the original `v0.1.0` tag and PyPI 0.1.0 artifacts immutable.
- [x] Configure GitHub `pypi` environment and PyPI Trusted Publisher.
- [x] Publish `v0.1.1` only after exact source, artifact, CI, Docs, and Release-check gates pass.
- [x] Confirm the first Trusted Publishing/OIDC upload succeeds with exact GitHub Release artifacts.

### 0.1.2 quality-completion release

- [x] Preserve frozen R 0.3.0 behavioral reference and 81 / 81 frozen public API counterparts.
- [x] Reach 100% executable statement coverage and 100% branch coverage.
- [x] Kill all 3 mutation-smoke mutants.
- [x] Pass 292 tests locally and in the quality branch.
- [x] Pass Linux/macOS/Windows CI across Python 3.11–3.14.
- [x] Pass Ruff lint/format, mypy, frozen API/signature/R-block gates, strict docs, wheel build, and fresh-wheel smoke.
- [ ] Create and publish exact `v0.1.2` GitHub Release artifacts only after the release PR is green.
- [ ] Publish those exact GitHub Release artifacts to PyPI through Trusted Publishing.
- [ ] Verify PyPI hashes and a fresh `pip install gp3sequencespy==0.1.2`.

### Future releases

- [x] Add a dedicated `.github/workflows/publish-pypi.yml` Trusted Publishing workflow.
- [x] Use a dedicated GitHub environment named `pypi`.
- [x] Register the GitHub Actions Trusted Publisher in the PyPI project settings.
- [ ] For the next release, confirm PyPI reports Trusted Publishing/provenance for
  the published files.
- [ ] Revoke a manually created API token if it was dedicated solely to
  `gp3sequencespy` and is no longer needed.

The `Release checks` workflow remains validation-only. The separate
`Publish to PyPI` workflow receives OIDC permission only in its publishing job
and publishes exact GitHub Release distributions without rebuilding them.
