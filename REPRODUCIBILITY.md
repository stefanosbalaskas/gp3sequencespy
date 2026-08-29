# Reproducibility and frozen reference

## Authoritative R reference

The initial Python parity target is `gp3sequences` **0.3.0**. The authoritative
R tarball used during the port has SHA-256:

```text
1d2ca1d72ebd375292fc9bdd0f41848b8224f9e1ae9d34acbd9469f103bf5b8d
```

The corresponding R repository release commit recorded during the port is:

```text
4ebf0bebea2955c5f98f8ddf0fe03e81d0b7ac3a
```

The Python repository stores API, signature, source, article, test, and parity
manifests under `reference/`. The test translation ledger is
`reference/test_parity_matrix.json`.

## Reproducing Python validation

```bash
uv sync --extra dev --extra time --extra docs --extra release
uv run ruff check src tests parity
uv run ruff format --check src tests parity
uv run mypy src/gp3sequencespy
uv run pytest -q
uv run mkdocs build --strict
uv build
uv run twine check dist/*
```

## Cross-language oracle

The deterministic R/Python oracle harness lives under `parity/`. The R generator
requires the exact frozen tarball and verifies its hash before installing it into
a temporary R library. Exact numerical parity must not be claimed for a contract
until the relevant oracle comparison has been run or the deliberate translation
is recorded in `PARITY_EXCEPTIONS.md`.
