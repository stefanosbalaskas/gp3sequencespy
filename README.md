# gp3sequencespy

`gp3sequencespy` is the Python implementation of **gp3sequences 0.3.0**, providing transparent, reproducible, and auditable analysis of ordered categorical sequences and scanpaths.

The frozen R 0.3.0 tarball is the behavioral reference. Development is parity-first: preserve the frozen scientific contracts, validate them explicitly, and only then add Python-native extensions.

## Version 0.1.0 status

- **81 / 81** frozen R public function counterparts are present and exported.
- **81 / 81** frozen R public signatures have been audited; every difference is either structurally matched or explicitly classified as an R→Python semantic/plotting translation.
- **130 / 130** frozen R `test_that()` blocks have dedicated Python translation tests recorded in `PARITY_TEST_MATRIX.md`.
- The current Python suite contains **182 tests**, including documentation, release-contract, and R-hclust oracle-regression tests.
- GitHub Actions covers Linux, macOS, and Windows with Python 3.11–3.14, a dedicated Ruff/mypy/frozen-contract quality job, and a fresh-wheel smoke build.
- Fifteen Python-native articles port the full frozen R vignette set, with MkDocs documentation under `docs/`.
- The deterministic core, hierarchical/PAM, and time-varying-model cross-language oracle tranches have been executed against frozen R 0.3.0; remaining deliberate boundaries are documented in `PARITY_EXCEPTIONS.md`.

Documentation: https://stefanosbalaskas.github.io/gp3sequencespy/

Version **0.1.0** is the first non-prerelease Python release candidate. Its parity claims are deliberately bounded: backend-object translations, cross-language random-number streams, Matplotlib rendering, and the validated `mssm` translation of the R `mgcv` model remain explicitly documented in `PARITY_EXCEPTIONS.md`.

## Installation

For development installs from the repository:

```bash
uv sync --extra time
```

For a built wheel:

```bash
pip install gp3sequencespy-0.1.0-py3-none-any.whl
```

The exact 0.1.0 wheel and sdist are validated before tagging. PyPI publication remains separate from release validation and is not performed by repository workflows.

## Reproducibility and release governance

- Frozen-reference details: `REPRODUCIBILITY.md`
- Known parity boundaries: `PARITY_EXCEPTIONS.md`
- Release gates: `RELEASE_CHECKLIST.md`
- Changelog: `CHANGELOG.md`
- Citation metadata: `CITATION.cff`
- Contribution guidance: `CONTRIBUTING.md`

## Scientific interpretation guardrail

Sequence structure does not independently establish emotion, cognition, comprehension, personality, intention, deception, diagnosis, or causality. Observational group contrasts are associational unless a valid randomized design supports a causal interpretation.
