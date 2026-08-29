# Release checklist

This checklist separates **release readiness** from **R numerical parity**. A
green Python test suite is necessary but not sufficient for a stable parity
claim.

## Always required

- [ ] `ruff check src tests parity` passes.
- [ ] `ruff format --check src tests parity` passes.
- [ ] `mypy src/gp3sequencespy` passes.
- [ ] Full pytest suite passes on Python 3.11–3.14 across Linux, macOS, and Windows.
- [ ] 81 / 81 frozen public API functions are present.
- [ ] 130 / 130 frozen R test blocks remain mapped.
- [ ] `mkdocs build --strict` passes.
- [ ] Wheel and sdist build successfully.
- [ ] `twine check dist/*` passes.
- [ ] Fresh-wheel import succeeds in a clean environment.
- [ ] `CHANGELOG.md`, `CITATION.cff`, README, and documentation reflect the candidate version.

## Required before stable 0.1.0

- [ ] Locate and hash the authoritative `gp3sequences_0.3.0.tar.gz`.
- [ ] Execute `parity/r_scripts/generate_reference_outputs.R` with that exact tarball.
- [ ] Execute the Python deterministic oracle generator.
- [ ] Compare deterministic oracle outputs with the committed canonicalizer/tolerance rules.
- [ ] Investigate every deterministic mismatch.
- [ ] Review every entry in `PARITY_EXCEPTIONS.md`; close it or retain it with explicit rationale.
- [ ] Run exact built-artifact tests from the release candidate wheel/sdist.
- [ ] Freeze version `0.1.0`, release notes, and tag only after the above review.

## Publication

The repository's `Release checks` workflow deliberately **does not publish to
PyPI**. PyPI publishing should be enabled only after the trusted-publishing
relationship and release governance are configured and reviewed.
