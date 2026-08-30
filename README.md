# gp3sequencespy

Zenodo archive DOI: [10.5281/zenodo.22166449](https://doi.org/10.5281/zenodo.22166449)

`gp3sequencespy` is the Python implementation of **gp3sequences 0.3.0**, providing transparent, reproducible, and auditable analysis of ordered categorical sequences and scanpaths.

The frozen R 0.3.0 tarball is the behavioral reference. Development is parity-first: preserve the frozen scientific contracts, validate them explicitly, and only then add Python-native extensions.

## Version 0.1.2 status

- **81 / 81** frozen R public function counterparts are present and exported.
- **81 / 81** frozen R public signatures have been audited; every difference is either structurally matched or explicitly classified as an R→Python semantic/plotting translation.
- **130 / 130** frozen R `test_that()` blocks have dedicated Python translation tests recorded in `PARITY_TEST_MATRIX.md`.
- The current Python suite contains **292 tests**, including documentation, release-contract, and R-hclust oracle-regression tests.
- GitHub Actions covers Linux, macOS, and Windows with Python 3.11–3.14, a dedicated Ruff/mypy/frozen-contract quality job, and a fresh-wheel smoke build.
- Fifteen Python-native articles port the full frozen R vignette set, with MkDocs documentation under `docs/`.
- The deterministic core, hierarchical/PAM, and time-varying-model cross-language oracle tranches have been executed against frozen R 0.3.0; remaining deliberate boundaries are documented in `PARITY_EXCEPTIONS.md`.

Documentation: https://stefanosbalaskas.github.io/gp3sequencespy/

Version **0.1.2** is a quality-completion and robustness maintenance release. It preserves the frozen 81-function scientific API and R 0.3.0 parity contracts while raising the Python validation suite to 292 tests, 100% statement and branch coverage, and a 3/3 mutation-smoke gate. It also expands the documentation and hardens PyArrow/pandas preparation and grouped plotting edge cases.

## Installation

For development installs from the repository:

```bash
uv sync --extra time
```

From PyPI:

```bash
pip install gp3sequencespy==0.1.2
```

The original `v0.1.0` scientific release remains immutable. Stable releases from `0.1.1` onward publish the exact GitHub Release wheel and source distribution to PyPI through the registered Trusted Publisher described in `PYPI_PUBLISHING.md`.

## Reproducibility and release governance

- Frozen-reference details: `REPRODUCIBILITY.md`
- Known parity boundaries: `PARITY_EXCEPTIONS.md`
- Release gates: `RELEASE_CHECKLIST.md`
- Changelog: `CHANGELOG.md`
- Citation metadata: `CITATION.cff`
- Contribution guidance: `CONTRIBUTING.md`
- PyPI publishing and Trusted Publishing: `PYPI_PUBLISHING.md`

## Scientific interpretation guardrail

Sequence structure does not independently establish emotion, cognition, comprehension, personality, intention, deception, diagnosis, or causality. Observational group contrasts are associational unless a valid randomized design supports a causal interpretation.
