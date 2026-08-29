# Release readiness

`gp3sequencespy` is frozen as **0.1.0** for the exact release-candidate artifact transaction. The deliberate parity boundaries have been reviewed and retained with explicit rationale; the final wheel and sdist must pass exact-artifact tests before the RC commit is pushed.

## Current verified contracts

- 81 / 81 frozen R 0.3.0 public API counterparts.
- 130 / 130 frozen R test blocks mapped to dedicated Python translations.
- 81 / 81 frozen R public signatures audited with zero unexplained drift.
- 15 / 15 frozen R vignette counterparts.
- Ruff, mypy, multi-platform tests, strict documentation builds, and fresh-wheel
  smoke tests in CI.

## Stable-release gate

The authoritative R 0.3.0 reference has been exercised by deterministic core, hierarchical/PAM, and time-model oracle tranches. Every remaining parity exception has been explicitly reviewed. The exact 0.1.0 wheel/sdist are tested from the committed candidate tree before push; tagging remains a separate post-CI step.

The full operational checklist is maintained in
[`RELEASE_CHECKLIST.md`](https://github.com/stefanosbalaskas/gp3sequencespy/blob/main/RELEASE_CHECKLIST.md).
Frozen-reference details are in
[`REPRODUCIBILITY.md`](https://github.com/stefanosbalaskas/gp3sequencespy/blob/main/REPRODUCIBILITY.md).

## Publication workflow

The repository's `Release checks` workflow validates metadata, static quality,
tests, documentation, distributions, wheel contents, and a clean wheel install.
It uploads the candidate artifacts to GitHub Actions but deliberately does not
publish them to PyPI.
