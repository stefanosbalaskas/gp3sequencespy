# Parity & validation

`gp3sequencespy` is a **parity-first Python implementation** of the frozen
`gp3sequences 0.3.0` scientific contract.

<div class="gp3-stats">
  <div><strong>81 / 81</strong><span>frozen public functions</span></div>
  <div><strong>81 / 81</strong><span>audited signatures</span></div>
  <div><strong>130 / 130</strong><span>translated R test blocks</span></div>
  <div><strong>0</strong><span>unexplained signature drift</span></div>
</div>

## What “parity” means here

Parity does **not** mean that Python pretends to be R. It means that the frozen
scientific behavior is translated and validated wherever a scientifically
meaningful equivalent exists, while irreducible ecosystem differences are
declared explicitly.

## Closed parity tranches

- deterministic state-summary oracle;
- deterministic transition-summary oracle;
- path-formatting oracle;
- motif-summary oracle;
- consensus oracle;
- Levenshtein distance oracle;
- hierarchical clustering semantics including R `hclust` edge cases;
- PAM medoid semantics;
- deterministic partition / medoid fixture coverage;
- validated time-varying model prediction comparison against the frozen R
  reference.

## Signature audit

The frozen 81-function API is classified into:

- exact structural signature matches;
- semantic R→Python signature translations;
- Python-only keyword-only plotting extensions (`ax=`) where documented.

There are **zero unexplained signature differences** in the frozen release
audit.

## Deliberate cross-language boundaries

### R ecosystem objects

Python adapters return Python-native structured data:

- TraMineR-style sequence matrices rather than an R `stslist`;
- seqHMM-compatible observation structures rather than R objects;
- arulesSequences-compatible itemset / metadata structures rather than S4
  transactions;
- NetworkX graphs rather than `igraph` objects.

### Graphics

Python uses Matplotlib rather than base R graphics. The scientific data contract,
labels, defaults, and call semantics are tested; pixel identity is not claimed.

### Random-number streams

Randomized algorithms use NumPy RNG semantics. Reproducibility means stable
Python seeding and validated statistical behavior, not bit-identical R random
draws.

### Time-varying model backend

The validated Python implementation uses `mssm 1.2.5` as a close semantic GAMM
translation of the R `mgcv` workflow. The frozen default REML contract is
supported; unsupported non-default smoothing criteria remain an explicit
boundary.

## Validation evidence

The stable release has:

- **182 Python tests**;
- cross-platform CI on Linux, macOS, and Windows;
- Python 3.11–3.14 coverage;
- strict documentation builds;
- fresh-wheel smoke tests;
- exact-artifact release validation;
- PyPI Trusted Publishing / OIDC.

## Interpretation boundary

Parity validates implementation behavior. It does not validate a substantive
scientific interpretation of a sequence pattern, cluster, graph community,
latent state, or group contrast.

For the engineering details, see the repository files:

- `SIGNATURE_PARITY.md`
- `PARITY_TEST_MATRIX.md`
- `PARITY_EXCEPTIONS.md`
- `REPRODUCIBILITY.md`
