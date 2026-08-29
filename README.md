# gp3sequencespy

`gp3sequencespy` is the Python implementation of **gp3sequences 0.3.0**, providing transparent, reproducible, and auditable analysis of ordered categorical sequences and scanpaths.

The frozen R 0.3.0 tarball is the behavioral reference. Development is parity-first: preserve the frozen scientific contracts, validate them explicitly, and only then add Python-native extensions.

## Current alpha status

- **81 / 81** frozen R public function counterparts are present and exported.
- **130 / 130** frozen R `test_that()` blocks have dedicated Python translation tests recorded in `PARITY_TEST_MATRIX.md`.
- The current Python suite contains **162 tests**, including four documentation-contract tests.
- GitHub Actions covers Linux, macOS, and Windows with Python 3.11–3.14, a dedicated Ruff/mypy/frozen-contract quality job, and a fresh-wheel smoke build.
- Fifteen Python-native articles port the full frozen R vignette set, with MkDocs documentation under `docs/`.
- A cross-language oracle harness is available under `parity/`; exact R numerical comparison remains pending where documented in `PARITY_EXCEPTIONS.md`.

Documentation: https://stefanosbalaskas.github.io/gp3sequencespy/

This remains an **alpha** package. API-surface coverage and translated behavioral tests are not, by themselves, proof of exact R numerical parity. In particular, backend-object translations, random-number streams, selected clustering details, and the time-varying `mgcv` model require the explicit treatment documented in `PARITY_EXCEPTIONS.md`.

## Scientific interpretation guardrail

Sequence structure does not independently establish emotion, cognition, comprehension, personality, intention, deception, diagnosis, or causality. Observational group contrasts are associational unless a valid randomized design supports a causal interpretation.
