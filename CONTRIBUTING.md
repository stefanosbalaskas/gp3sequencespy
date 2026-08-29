# Contributing to gp3sequencespy

`gp3sequencespy` is developed parity-first against the frozen R package
`gp3sequences` 0.3.0. Contributions are welcome when they preserve the frozen
scientific contracts and make deviations explicit.

## Development setup

```bash
uv sync --extra dev --extra time --extra docs --extra release
```

Run the local quality gates before opening a pull request:

```bash
uv run ruff check src tests parity
uv run ruff format --check src tests parity
uv run mypy src/gp3sequencespy
uv run pytest -q
uv run mkdocs build --strict
uv build
uv run twine check dist/*
```

## Parity rules

1. Do not change an R-corresponding public contract silently.
2. Add or update a parity test whenever a frozen behavior changes or is clarified.
3. Record deliberate R → Python ecosystem translations in `PARITY_EXCEPTIONS.md`.
4. Keep stochastic behavior reproducible without mutating the caller's global RNG.
5. Do not infer psychological, medical, biometric, or causal meaning from sequence
   structure unless the study design and method explicitly support that inference.

## Pull requests

Keep changes focused. Describe the scientific contract affected, tests added,
backward-compatibility implications, and whether exact R numerical parity is
expected, translated, or still oracle-pending.
