# Reproducibility

`gp3sequencespy` is developed with a frozen-reference and audit-first approach.

## Frozen reference

The scientific reference is `gp3sequences 0.3.0`. The Python release preserves
the frozen public-function contract while documenting legitimate Python-native
translations.

Current validated release status:

- **81 / 81** frozen public R function counterparts;
- **81 / 81** audited frozen public signatures;
- **130 / 130** translated frozen R `test_that()` blocks;
- **182** Python tests;
- deterministic R/Python oracle tranches for core summaries, hierarchical/PAM
  clustering, and the time-varying backend;
- explicit cross-language exceptions documented rather than hidden.

## Recommended reproducible workflow

1. Pin the package version.
2. Preserve the raw ordered event table.
3. Record validation and preparation policies.
4. Record method parameters and seeds.
5. Save analysis summaries and audit objects.
6. Preserve the Python environment / lockfile.
7. Report deliberate cross-language boundaries.

```bash
pip install gp3sequencespy==0.1.1
```

For `uv` projects:

```bash
uv add gp3sequencespy==0.1.1
uv lock
```

## Audit the input

```python
import gp3sequencespy as g

audit = g.audit_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
)
```

## Audit the analysis

```python
analysis_audit = g.audit_sequence_analysis(distance)
```

## Randomness

Randomized algorithms use NumPy's random-number generator rather than R's RNG.
The scientific contract is deterministic Python seeding and statistical
behavior, not bit-identical draws across languages.

Always record seeds for:

- bootstrap clustering;
- bootstrap group differences;
- bootstrap transition networks;
- HMM / mixture fitting;
- permutation-based group inference;
- any stochastic downstream analysis.

## Cross-language boundaries

The main deliberate boundaries are:

- R ecosystem object identity versus Python-native structured adapters;
- base-R graphics versus Matplotlib;
- R RNG streams versus NumPy RNG streams;
- R `mgcv` versus the validated `mssm` translation for time-varying models.

See [Parity & validation](parity.md) for the detailed contract.

## Release provenance

Version `0.1.1` is published on GitHub and PyPI. PyPI publication is performed
through GitHub Actions Trusted Publishing / OIDC, avoiding a stored package
upload token.

The original 0.1.0 scientific artifacts remain immutable. Version 0.1.1 does
not change the scientific algorithms or frozen public scientific API.

## Citation

- Repository: `stefanosbalaskas/gp3sequencespy`
- Release: `0.1.1`
- Zenodo DOI: `10.5281/zenodo.22166449`
