# Release status

## gp3sequencespy 0.1.2

Version **0.1.2** is the current stable PyPI release and a quality-completion / robustness maintenance release over the frozen scientific contracts.

<div class="gp3-release-panel">
<span class="gp3-status gp3-status--good">292 tests</span>
<span class="gp3-status gp3-status--good">100% statements</span>
<span class="gp3-status gp3-status--good">100% branches</span>
<span class="gp3-status gp3-status--good">3/3 mutation smoke</span>
</div>

## Scientific contract

The release preserves the frozen R 0.3.0 behavioral reference and does not introduce a breaking public scientific API or signature change.

- frozen API: **81 / 81**
- frozen signatures: **81 / 81**
- translated R test blocks: **130 / 130**
- unexplained signature drift: **0**
- Python tests: **292**
- statement coverage: **100.00%**
- branch coverage: **100.00%**
- mutation smoke: **3 / 3 killed**
- deterministic R-oracle tranches: **PASS**
- strict MkDocs build: **PASS**
- fresh-wheel smoke: **PASS**

## Quality-completion changes

Version 0.1.2 adds complete behavioral coverage, mutation-smoke companion oracles, PyArrow/pandas robustness for cumulative preparation operations, NA-safe grouped plotting behavior, dead-branch cleanup, and expanded documentation.

## Publication identity

The stable release was created from Git commit `564dfb3f97dde9e9228819bf4792821584b02934` and annotated tag `v0.1.2` (tag object `c2ee786031c0badb9127529601e08893e90af70d`). The exact GitHub Release distributions were published to PyPI through the registered Trusted Publisher without rebuilding.

- wheel: `gp3sequencespy-0.1.2-py3-none-any.whl`
- wheel SHA-256: `3fd063414f0c8c37fb5ae9a6aacf103a89afd0e6e2135ab3b81248b38b9ba847`
- source distribution: `gp3sequencespy-0.1.2.tar.gz`
- source SHA-256: `58b5e81149accf95d1b1a7e205f8cdf7a21846f0138b8aae00cfddd5db4289d9`
- guarded stable-release workflow: **PASS** (`33342028606`)
- Trusted Publishing workflow: **PASS** (`33342198803`)
- post-PyPI hash and fresh-install verification: **PASS** (`33342235019`)

The independent post-publication verifier confirmed that PyPI's SHA-256 values exactly match both GitHub Release distribution hashes and that a clean `pip install gp3sequencespy==0.1.2` succeeds.

## Publication model

Stable releases are built and validated before an annotated `vX.Y.Z` tag and GitHub Release are created. The exact GitHub Release wheel and source distribution are then published to PyPI through the registered Trusted Publisher; no package rebuild occurs in the publishing job. A manual-dispatch fallback is retained for the GitHub `GITHUB_TOKEN` workflow-chaining limitation, and it is guarded by stable-release, filename, checksum, and Twine validation.

## Archive

Zenodo DOI: [10.5281/zenodo.22166449](https://doi.org/10.5281/zenodo.22166449)

## Historical releases

The `v0.1.0` and `v0.1.1` tags and their published artifacts remain unchanged.
