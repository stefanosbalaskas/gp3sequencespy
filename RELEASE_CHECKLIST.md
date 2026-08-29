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
- [ ] Review every remaining entry in `PARITY_EXCEPTIONS.md`; retain only deliberate translations with explicit rationale.
- [x] Replace the statsmodels/Patsy time-model approximation with the validated `mssm` GAMM backend.
- [ ] Run exact built-artifact tests from the final `0.1.0` release candidate wheel/sdist.
- [ ] Freeze version `0.1.0`, release notes, and tag only after the above review.

## Publication

The repository's `Release checks` workflow deliberately **does not publish to PyPI**. PyPI publishing should be enabled only after the trusted-publishing relationship and release governance are configured and reviewed.
