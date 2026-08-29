# Release readiness

`gp3sequencespy` **0.1.1** is a metadata/release-infrastructure maintenance release over the completed 0.1.0 scientific freeze. The 81-function API, frozen R 0.3.0 contracts, and deliberate parity boundaries are unchanged.

## Current verified contracts

- 81 / 81 frozen R 0.3.0 public API counterparts.
- 130 / 130 frozen R test blocks mapped to dedicated Python translations.
- 81 / 81 frozen R public signatures audited with zero unexplained drift.
- 15 / 15 frozen R vignette counterparts.
- Ruff, mypy, multi-platform tests, strict documentation builds, and fresh-wheel
  smoke tests in CI.

## Stable-release gate

The authoritative R 0.3.0 reference has been exercised by deterministic core, hierarchical/PAM, and time-model oracle tranches. Every remaining parity exception has been explicitly reviewed. The exact 0.1.0 wheel/sdist passed committed-source, GitHub release, and PyPI identity checks.

The full operational checklist is maintained in
[`RELEASE_CHECKLIST.md`](https://github.com/stefanosbalaskas/gp3sequencespy/blob/main/RELEASE_CHECKLIST.md).
Frozen-reference details are in
[`REPRODUCIBILITY.md`](https://github.com/stefanosbalaskas/gp3sequencespy/blob/main/REPRODUCIBILITY.md).

## Publication workflow

The repository's `Release checks` workflow remains validation-only: it validates
metadata, static quality, tests, documentation, distributions, wheel contents,
and a clean wheel install.

The registered `.github/workflows/publish-pypi.yml` Trusted Publisher verifies
the exact distributions attached to the published GitHub Release, then gives
OIDC `id-token: write` only to the dedicated publishing job. Version 0.1.1 is
the first release intended to exercise this token-free path end-to-end. See
`PYPI_PUBLISHING.md`.
