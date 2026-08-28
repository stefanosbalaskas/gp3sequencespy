# gp3sequencespy

`gp3sequencespy` is the Python implementation of **gp3sequences 0.3.0**, providing transparent, reproducible, and auditable analysis of ordered categorical sequences and scanpaths.

The frozen R 0.3.0 tarball is the behavioral reference. Development is parity-first: preserve the frozen scientific contracts, validate them explicitly, and only then add Python-native extensions.

## Current alpha status

- **81 / 81** frozen R public function counterparts are present and exported.
- **130 / 130** frozen R `test_that()` blocks have dedicated Python translation tests recorded in `PARITY_TEST_MATRIX.md`.
- The current Python suite contains **158 tests**.
- The first GitHub Actions matrix passed on Linux, macOS, and Windows with Python 3.11–3.14, including a fresh-wheel smoke test.
- A cross-language oracle harness is available under `parity/`; exact R numerical comparison remains pending where documented in `PARITY_EXCEPTIONS.md`.

This remains an **alpha** package. API-surface coverage and translated behavioral tests are not, by themselves, proof of exact R numerical parity. In particular, backend-object translations, random-number streams, selected clustering details, and the time-varying `mgcv` model require the explicit treatment documented in `PARITY_EXCEPTIONS.md`.

## Scientific interpretation guardrail

Sequence structure does not independently establish emotion, cognition, comprehension, personality, intention, deception, diagnosis, or causality. Observational group contrasts are associational unless a valid randomized design supports a causal interpretation.
