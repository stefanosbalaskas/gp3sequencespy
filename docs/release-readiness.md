# Release readiness

`gp3sequencespy` is currently **0.1.0a1**. The repository is publication-ready
from a Python packaging and documentation perspective, but the stable `0.1.0`
parity claim is now gated on the final exception review and exact built-artifact release candidate.

## Current verified contracts

- 81 / 81 frozen R 0.3.0 public API counterparts.
- 130 / 130 frozen R test blocks mapped to dedicated Python translations.
- 15 / 15 frozen R vignette counterparts.
- Ruff, mypy, multi-platform tests, strict documentation builds, and fresh-wheel
  smoke tests in CI.

## Stable-release gate

The authoritative R 0.3.0 reference has now been exercised by deterministic core, hierarchical/PAM, and time-model oracle tranches. Before `0.1.0`, every remaining documented parity exception must be reviewed and the exact wheel/sdist release candidate must pass the full artifact matrix.

The full operational checklist is maintained in
[`RELEASE_CHECKLIST.md`](https://github.com/stefanosbalaskas/gp3sequencespy/blob/main/RELEASE_CHECKLIST.md).
Frozen-reference details are in
[`REPRODUCIBILITY.md`](https://github.com/stefanosbalaskas/gp3sequencespy/blob/main/REPRODUCIBILITY.md).

## Publication workflow

The repository's `Release checks` workflow validates metadata, static quality,
tests, documentation, distributions, wheel contents, and a clean wheel install.
It uploads the candidate artifacts to GitHub Actions but deliberately does not
publish them to PyPI.
