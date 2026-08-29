# Parity and validation

The frozen behavioral reference is **gp3sequences 0.3.0**.

- **81 / 81** frozen R public functions have Python counterparts.
- **130 / 130** frozen R `test_that()` blocks have dedicated Python translation tests.
- The current suite contains **162 tests**: 158 behavioral/API/parity tests plus 4 documentation-contract tests.
- CI covers Python 3.11–3.14 on Linux, Windows, and macOS, plus static quality and a fresh-wheel build/import smoke test.

Exact numerical identity is not claimed for the documented exceptions: selected hierarchical-clustering details, random-number streams, R-backend object identity, and the time-varying model where the R reference uses `mgcv::gam()` while the Python alpha uses a statsmodels/Patsy approximation.

See the repository `PARITY_EXCEPTIONS.md` and `PARITY_TEST_MATRIX.md` for the auditable freeze.
