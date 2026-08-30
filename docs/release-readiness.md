# Release status

## gp3sequencespy 0.1.2

Version **0.1.2** is the current stable release candidate and a quality-completion / robustness maintenance release over the frozen scientific contracts.

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

## Publication model

Stable releases are built and validated before an annotated `vX.Y.Z` tag and GitHub Release are created. The exact GitHub Release wheel and source distribution are then published to PyPI through the registered Trusted Publisher; no package rebuild occurs in the publishing job.

## Archive

Zenodo DOI: [10.5281/zenodo.22166449](https://doi.org/10.5281/zenodo.22166449)

## Historical releases

The `v0.1.0` and `v0.1.1` tags and their published artifacts remain immutable.
