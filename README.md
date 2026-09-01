<p align="center">
  <img src="https://raw.githubusercontent.com/stefanosbalaskas/gp3sequencespy/main/docs/assets/python-suite-logo.png" width="260" alt="Python Suite research packages logo">
</p>

<h1 align="center">gp3sequencespy</h1>

<p align="center">
  <strong>Transparent, reproducible sequence analysis in Python.</strong><br>
  Audit ordered categorical data, discover recurring structure, compare trajectories,
  model transitions and latent states, test group differences, and report every analytical choice.
</p>

<p align="center">
  <a href="https://pypi.org/project/gp3sequencespy/"><img alt="PyPI" src="https://img.shields.io/pypi/v/gp3sequencespy?logo=pypi&logoColor=white"></a>
  <a href="https://pypi.org/project/gp3sequencespy/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/gp3sequencespy?logo=python&logoColor=white"></a>
  <a href="https://github.com/stefanosbalaskas/gp3sequencespy/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/stefanosbalaskas/gp3sequencespy/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/stefanosbalaskas/gp3sequencespy/actions/workflows/docs.yml"><img alt="Docs" src="https://github.com/stefanosbalaskas/gp3sequencespy/actions/workflows/docs.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/stefanosbalaskas/gp3sequencespy/actions/workflows/quality-completion.yml"><img alt="Quality" src="https://github.com/stefanosbalaskas/gp3sequencespy/actions/workflows/quality-completion.yml/badge.svg?branch=main"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-4c1.svg"></a>
  <a href="https://doi.org/10.5281/zenodo.22166449"><img alt="DOI" src="https://zenodo.org/badge/DOI/10.5281/zenodo.22166449.svg"></a>
</p>

<p align="center">
  <a href="https://stefanosbalaskas.github.io/gp3sequencespy/"><strong>Documentation</strong></a>
  · <a href="https://stefanosbalaskas.github.io/gp3sequencespy/quickstart/">Quickstart</a>
  · <a href="https://stefanosbalaskas.github.io/gp3sequencespy/method-map/">Method map</a>
  · <a href="https://stefanosbalaskas.github.io/gp3sequencespy/plots/">Plot gallery</a>
  · <a href="https://stefanosbalaskas.github.io/gp3sequencespy/reference/">API reference</a>
  · <a href="https://github.com/stefanosbalaskas/gp3sequencespy/releases/tag/v0.1.2">v0.1.2</a>
</p>

---

`gp3sequencespy` is the Python implementation of **gp3sequences 0.3.0** for ordered categorical sequences and scanpaths. The frozen R 0.3.0 tarball is the behavioral reference: scientific contracts are preserved and tested explicitly, while deliberate R→Python translations are documented rather than hidden.

The package is designed for research workflows where **data preparation, method choice, reproducibility, and interpretation need to remain visible from input to report**.

## Install

```bash
pip install gp3sequencespy==0.1.2
```

With `uv`:

```bash
uv add gp3sequencespy==0.1.2
```

Python **3.11–3.14** is supported. Optional extras are available for HMM backends, Arrow/Polars data interoperability, performance helpers, time-varying models, documentation, and development.

```bash
pip install "gp3sequencespy[hmm]"
pip install "gp3sequencespy[data]"
pip install "gp3sequencespy[time]"
```

## A 60-second workflow

```python
import pandas as pd
import gp3sequencespy as g

# One row per observed state occurrence.
data = pd.DataFrame(
    {
        "sequence_id": ["s1", "s1", "s1", "s2", "s2", "s2"],
        "sequence_order": [1, 2, 3, 1, 2, 3],
        "state": ["home", "search", "checkout", "home", "product", "checkout"],
    }
)

# Audit and prepare explicitly.
validation = g.validate_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
)
prepared = g.prepare_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
)

# Compare complete trajectories.
distance = g.compute_sequence_distance(
    prepared.data,
    method="lcs",
    normalise="max_length",
)

# Inspect transition structure.
network = g.create_transition_network(
    prepared.data,
    normalise="from",
)

# Visualise complete paths.
ax = g.plot_sequence_index(prepared.data)
```

For the complete path from raw long-format data to summaries, motifs, clustering, networks, plots, and analysis auditing, see the **[Quickstart](https://stefanosbalaskas.github.io/gp3sequencespy/quickstart/)**.

## What you can do

| Research task | Capabilities | Start here |
| --- | --- | --- |
| **Audit & prepare** | ordering, missing states, duplicate positions, durations, state policies, preparation provenance | [Validation & preparation](https://stefanosbalaskas.github.io/gp3sequencespy/articles/sequence-data-validation-and-preparation/) |
| **Describe sequences** | state occupancy, transitions, paths, consensus, representatives | [Examples](https://stefanosbalaskas.github.io/gp3sequencespy/examples/) |
| **Find recurring structure** | contiguous motifs, bounded non-contiguous subsequences, motif filtering and visualisation | [Motif workflow](https://stefanosbalaskas.github.io/gp3sequencespy/articles/contiguous-motif-workflow/) |
| **Compare trajectories** | Levenshtein, LCS, optimal matching, transition-profile distances, clustering and stability | [Distances & clustering](https://stefanosbalaskas.github.io/gp3sequencespy/articles/distances-clustering-and-stability/) |
| **Model transitions** | transition networks, centrality, communities, higher-order transition structure | [Networks & higher-order models](https://stefanosbalaskas.github.io/gp3sequencespy/articles/transition-networks-and-higher-order-models/) |
| **Fit latent models** | categorical, multichannel, covariate-dependent and time-varying HMM workflows | [Latent models](https://stefanosbalaskas.github.io/gp3sequencespy/articles/latent-models-and-optional-adapters/) |
| **Test group structure** | design-aware randomization and sequence-group inference | [Inference & randomization](https://stefanosbalaskas.github.io/gp3sequencespy/articles/sequence-inference-and-randomization/) |
| **Visualise & report** | sequence index, state distributions, distance heatmaps, transition networks, audit trails | [Plot gallery](https://stefanosbalaskas.github.io/gp3sequencespy/plots/) |

Not sure which family fits your question? Use the **[method map](https://stefanosbalaskas.github.io/gp3sequencespy/method-map/)** to move from research question → assumptions → method family.

## Parity and validation

Version **0.1.2** is the current stable quality-completion release.

| Validation contract | Status |
| --- | ---: |
| Frozen R public counterparts | **81 / 81** |
| Frozen R public signatures audited | **81 / 81** |
| Frozen R `test_that()` blocks translated | **130 / 130** |
| Python tests | **292** |
| Statement coverage | **100%** |
| Branch coverage | **100%** |
| Mutation smoke | **3 / 3 killed** |
| CI platforms | **Linux · macOS · Windows** |
| CI Python versions | **3.11 · 3.12 · 3.13 · 3.14** |
| Python-native articles | **15** |

The deterministic core, hierarchical/PAM, and time-varying-model cross-language oracle tranches have been executed against frozen R 0.3.0. Remaining deliberate boundaries are recorded in [`PARITY_EXCEPTIONS.md`](PARITY_EXCEPTIONS.md), with broader parity evidence in [`PARITY_TEST_MATRIX.md`](PARITY_TEST_MATRIX.md) and the [online parity guide](https://stefanosbalaskas.github.io/gp3sequencespy/parity/).

## Documentation routes

| If you want to… | Go to |
| --- | --- |
| get from install to first analysis quickly | [Quickstart](https://stefanosbalaskas.github.io/gp3sequencespy/quickstart/) |
| choose a method by research question | [Method map](https://stefanosbalaskas.github.io/gp3sequencespy/method-map/) |
| copy complete analysis recipes | [Examples](https://stefanosbalaskas.github.io/gp3sequencespy/examples/) |
| inspect available figure families | [Plot gallery](https://stefanosbalaskas.github.io/gp3sequencespy/plots/) |
| read the full methodological guides | [Articles](https://stefanosbalaskas.github.io/gp3sequencespy/articles/) |
| translate from the R package | [R → Python](https://stefanosbalaskas.github.io/gp3sequencespy/r-to-python/) |
| browse functions and signatures | [API reference](https://stefanosbalaskas.github.io/gp3sequencespy/reference/) |
| document a reproducible analysis | [Reproducibility](https://stefanosbalaskas.github.io/gp3sequencespy/reproducibility/) · [Reporting guide](https://stefanosbalaskas.github.io/gp3sequencespy/reporting/) |

## Reproducibility and release governance

The package treats release and parity evidence as part of the scientific software contract.

- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) — frozen-reference and reproducibility policy
- [`PARITY_EXCEPTIONS.md`](PARITY_EXCEPTIONS.md) — deliberate R→Python boundaries
- [`SIGNATURE_PARITY.md`](SIGNATURE_PARITY.md) — frozen public-signature audit
- [`QUALITY_COMPLETION.md`](QUALITY_COMPLETION.md) — 100% coverage and mutation-hardening evidence
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — stable-release gates
- [`PYPI_PUBLISHING.md`](PYPI_PUBLISHING.md) — Trusted Publishing and artifact verification
- [`CHANGELOG.md`](CHANGELOG.md) — release history

Stable releases publish the exact validated GitHub Release wheel and source distribution to PyPI through GitHub OIDC Trusted Publishing. Release **0.1.2** was independently checked after publication against the GitHub Release SHA-256 hashes and a clean PyPI installation.

## Development

```bash
uv sync --all-extras --python 3.12
uv run pytest -q
```

Full quality gate:

```bash
uv run pytest -q \
  --cov=gp3sequencespy \
  --cov-branch \
  --cov-report=term-missing \
  --cov-fail-under=100

uv run python scripts/run_mutation_smoke.py
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution guidance and [`SECURITY.md`](SECURITY.md) for the security policy.

## Citation

If `gp3sequencespy` contributes to your research, use the repository citation metadata in [`CITATION.cff`](CITATION.cff) and the archived Zenodo record:

**DOI: [10.5281/zenodo.22166449](https://doi.org/10.5281/zenodo.22166449)**

## Scientific interpretation guardrail

> Sequence structure does not independently establish emotion, cognition, comprehension, personality, intention, deception, diagnosis, or causality. Observational group contrasts are associational unless a valid randomized design supports a causal interpretation.

---

<p align="center">
  <a href="https://stefanosbalaskas.github.io/gp3sequencespy/">Documentation</a>
  · <a href="https://pypi.org/project/gp3sequencespy/">PyPI</a>
  · <a href="https://github.com/stefanosbalaskas/gp3sequencespy/releases">Releases</a>
  · <a href="https://doi.org/10.5281/zenodo.22166449">Zenodo</a>
</p>
