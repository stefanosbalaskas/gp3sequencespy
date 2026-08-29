# PyPI publishing

`gp3sequencespy 0.1.0` was first published to production PyPI on 2026-08-30
from the exact wheel and source distribution already frozen in the GitHub
`v0.1.0` Release.

## 0.1.0 publication identity

- Git commit:
  `28f06a571889bf9db760d00c47e1252d3836679a`
- Git tag: `v0.1.0`
- Wheel:
  `gp3sequencespy-0.1.0-py3-none-any.whl`
- Wheel SHA-256:
  `97725d0b34872b79c9f9cb4da57f14a788a8920880a0a415c13669d281a39525`
- Source distribution:
  `gp3sequencespy-0.1.0.tar.gz`
- Source SHA-256:
  `e01ff3ac4ec0cbede48b1019e4bcabddd38b9587df3fe541ce66aff585bf7e19`

PyPI's JSON API was queried after upload and both published hashes matched
the frozen GitHub release artifacts exactly.

## Trusted Publishing

The PyPI project has an active GitHub Actions Trusted Publisher for
`.github/workflows/publish-pypi.yml` using the `pypi` environment.

The workflow deliberately publishes **existing GitHub Release assets** rather
than rebuilding the package. This preserves the release model used for 0.1.0:
validate and freeze exact artifacts first, then publish those same artifacts.

### Active PyPI configuration

The registered GitHub Actions Trusted Publisher uses:

- **Owner:** `stefanosbalaskas`
- **Repository:** `gp3sequencespy`
- **Workflow name:** `publish-pypi.yml`
- **Environment name:** `pypi`

The workflow uses the dedicated GitHub `pypi` environment and grants
`id-token: write` only to the publishing job.

### Release behavior

The publishing workflow runs only for a published, non-prerelease GitHub
Release. The verification job:

1. downloads the exact wheel and sdist attached to the GitHub Release;
2. requires a stable `vX.Y.Z` tag;
3. requires filenames to match that tag;
4. runs `twine check --strict`;
5. passes the verified files to the publishing job as a short-lived Actions
   artifact.

The publishing job only downloads that verified artifact and invokes
`pypa/gh-action-pypi-publish@release/v1`.

No long-lived PyPI token is stored in the repository or workflow.

## API-token cleanup

The 0.1.0 first publication used a manually supplied PyPI API token because
the project did not yet exist on PyPI when release automation was prepared.
The Trusted Publisher was registered on 2026-08-30. After 0.1.1 confirms the
OIDC path end-to-end, any API token created solely for `gp3sequencespy` can
be revoked from PyPI.
