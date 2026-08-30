# PyPI publishing

`gp3sequencespy` uses exact-artifact publication: stable wheel and source distributions are first built, validated, checksummed, and attached to a GitHub Release, then those same files are published to PyPI without rebuilding.

## 0.1.0 publication identity

- Git commit: `28f06a571889bf9db760d00c47e1252d3836679a`
- Git tag: `v0.1.0`
- Wheel: `gp3sequencespy-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `97725d0b34872b79c9f9cb4da57f14a788a8920880a0a415c13669d281a39525`
- Source distribution: `gp3sequencespy-0.1.0.tar.gz`
- Source SHA-256: `e01ff3ac4ec0cbede48b1019e4bcabddd38b9587df3fe541ce66aff585bf7e19`

PyPI's JSON API was queried after upload and both published hashes matched the frozen GitHub Release artifacts exactly.

## 0.1.2 publication identity

Version **0.1.2** was published on 2026-08-31 through PyPI Trusted Publishing after the complete quality-completion release gate passed.

- Release commit: `564dfb3f97dde9e9228819bf4792821584b02934`
- Annotated tag: `v0.1.2`
- Annotated tag object: `c2ee786031c0badb9127529601e08893e90af70d`
- GitHub Release ID: `379432726`
- Wheel: `gp3sequencespy-0.1.2-py3-none-any.whl`
- Wheel SHA-256: `3fd063414f0c8c37fb5ae9a6aacf103a89afd0e6e2135ab3b81248b38b9ba847`
- Source distribution: `gp3sequencespy-0.1.2.tar.gz`
- Source SHA-256: `58b5e81149accf95d1b1a7e205f8cdf7a21846f0138b8aae00cfddd5db4289d9`
- Stable-release workflow run: `33342028606` — **PASS**
- Trusted Publishing workflow run: `33342198803` — **PASS**
- Post-PyPI verification run: `33342235019` — **PASS**
- Verification artifact: `9740897782`

The independent verifier compared the GitHub Release SHA-256 values against PyPI's published-file SHA-256 values and confirmed exact equality for both distributions. It then created a clean virtual environment and successfully installed `gp3sequencespy==0.1.2` from PyPI.

The full machine-readable publication ledger is stored in `reference/release_publication_0.1.2.json`.

## Trusted Publishing

The PyPI project has an active GitHub Actions Trusted Publisher for `.github/workflows/publish-pypi.yml` using the `pypi` environment.

### Active PyPI configuration

- **Owner:** `stefanosbalaskas`
- **Repository:** `gp3sequencespy`
- **Workflow name:** `publish-pypi.yml`
- **Environment name:** `pypi`

The publishing job alone receives `id-token: write`; no long-lived PyPI credential is required by the automated path.

### Release behavior

The permanent workflow supports two guarded entry points:

1. a published stable GitHub Release; or
2. an explicit manual dispatch naming an existing stable `vX.Y.Z` GitHub Release.

The manual-dispatch path exists because GitHub intentionally suppresses workflow chaining when one workflow creates a Release using `GITHUB_TOKEN`.

For either entry point the verification job:

1. resolves and validates the stable `vX.Y.Z` tag;
2. requires an existing non-draft, non-prerelease GitHub Release;
3. downloads the exact wheel, sdist, and `SHA256SUMS.txt` attached to that Release;
4. verifies the release checksums;
5. requires filenames to match the stable tag;
6. runs `twine check --strict`;
7. passes only the verified wheel and sdist to the publishing job as a short-lived Actions artifact.

The publishing job downloads that verified artifact and invokes `pypa/gh-action-pypi-publish@release/v1`. It does not build package distributions.

## API-token cleanup

The 0.1.0 first publication used a manually supplied PyPI API token because the project did not yet exist on PyPI when release automation was prepared. The Trusted Publisher was registered on 2026-08-30. Version 0.1.1 confirmed the OIDC path end-to-end, and version 0.1.2 independently reconfirmed exact-artifact Trusted Publishing plus post-publication hash and clean-install verification.

Any API token created solely for `gp3sequencespy` is therefore no longer required by the automated release path and can be revoked in PyPI account/project settings if it still exists.
