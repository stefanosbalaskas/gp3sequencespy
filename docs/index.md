<div class="gp3-hero">
  <div class="gp3-hero-copy">
    <span class="gp3-eyebrow">gp3sequencespy 0.1.2 · stable PyPI release</span>
    <h1>Ordered categorical sequence analysis, built for transparent research.</h1>
    <p class="gp3-lead">
      Validate sequence data, describe paths and motifs, compare whole-sequence
      structure, cluster trajectories, model transitions and latent states, run
      design-aware inference, and communicate results with publication-ready plots.
    </p>
    <div class="gp3-actions">
      <a class="md-button md-button--primary" href="quickstart/">Start in 5 minutes</a>
      <a class="md-button" href="method-map/">Choose a method</a>
      <a class="md-button" href="plots/">See the plot gallery</a>
    </div>
  </div>

  <div class="gp3-sequence-card" aria-label="Illustrative categorical sequence paths">
    <div class="gp3-sequence-title">Sequence structure at a glance</div>
    <div class="gp3-sequence-row"><span class="s-a">A</span><span class="s-b">B</span><span class="s-c">C</span><span class="s-d">D</span><span class="s-d">D</span></div>
    <div class="gp3-sequence-row"><span class="s-a">A</span><span class="s-a">A</span><span class="s-c">C</span><span class="s-c">C</span><span class="s-d">D</span></div>
    <div class="gp3-sequence-row"><span class="s-d">D</span><span class="s-c">C</span><span class="s-b">B</span><span class="s-b">B</span><span class="s-a">A</span></div>
    <div class="gp3-sequence-row"><span class="s-a">A</span><span class="s-b">B</span><span class="s-b">B</span><span class="s-c">C</span><span class="s-d">D</span></div>
    <div class="gp3-sequence-caption">states → motifs → distances → transitions → models</div>
  </div>
</div>

<div class="gp3-stats">
  <div><strong>81 / 81</strong><span>frozen R function counterparts</span></div>
  <div><strong>130 / 130</strong><span>translated frozen R test blocks</span></div>
  <div><strong>292</strong><span>Python validation tests</span></div>
  <div><strong>15</strong><span>Python-native methodology articles</span></div>
</div>

`gp3sequencespy` is the Python implementation of the frozen **gp3sequences 0.3.0**
public contract. Version **0.1.2** is available from PyPI and preserves the
frozen scientific/API contracts while adding complete statement/branch coverage,
mutation-smoke protection, robustness repairs, and expanded documentation. The package is designed around explicit assumptions, auditable
transformations, reproducible parameter choices, and bounded interpretation.

```bash
pip install gp3sequencespy==0.1.2
```

## Start with your research question

<div class="gp3-card-grid">

<div class="gp3-card">
<h3>Prepare & validate</h3>
<p>Audit order, missing states, durations, duplicated positions, metadata, and explicit preparation policies before analysis.</p>
<p><a href="articles/sequence-data-validation-and-preparation/">Data preparation article →</a></p>
</div>

<div class="gp3-card">
<h3>Describe sequence structure</h3>
<p>Summarise state occupancy, transitions, complete paths, consensus structure, contiguous motifs, and non-contiguous subsequences.</p>
<p><a href="examples/">Practical examples →</a></p>
</div>

<div class="gp3-card">
<h3>Compare whole sequences</h3>
<p>Compute edit-, LCS-, optimal-matching-, or transition-profile distances; cluster; validate; bootstrap; and identify representatives.</p>
<p><a href="articles/distances-clustering-and-stability/">Distance & clustering article →</a></p>
</div>

<div class="gp3-card">
<h3>Model transitions</h3>
<p>Build transition networks, inspect centrality and communities, fit higher-order transition models, and predict next-state structure.</p>
<p><a href="articles/transition-networks-and-higher-order-models/">Transition models article →</a></p>
</div>

<div class="gp3-card">
<h3>Fit latent models</h3>
<p>Use categorical, mixture, multichannel, and covariate-dependent HMM workflows with explicit convergence and interpretation boundaries.</p>
<p><a href="articles/latent-models-and-optional-adapters/">Latent-model article →</a></p>
</div>

<div class="gp3-card">
<h3>Run design-aware inference</h3>
<p>Declare the comparison design and use randomization-aware group testing rather than treating descriptive differences as causal evidence.</p>
<p><a href="articles/sequence-inference-and-randomization/">Inference article →</a></p>
</div>

</div>

## A complete structural workflow

<div class="gp3-pipeline">
  <div><b>1</b><span>Audit</span><small>data integrity</small></div>
  <div><b>2</b><span>Prepare</span><small>explicit policies</small></div>
  <div><b>3</b><span>Describe</span><small>states · paths · motifs</small></div>
  <div><b>4</b><span>Compare</span><small>distance · groups</small></div>
  <div><b>5</b><span>Model</span><small>networks · HMMs</small></div>
  <div><b>6</b><span>Validate</span><small>stability · inference</small></div>
  <div><b>7</b><span>Report</span><small>plots · audit trail</small></div>
</div>

```python
import pandas as pd
import gp3sequencespy as g

data = pd.DataFrame(
    {
        "sequence_id": ["s1", "s1", "s1", "s2", "s2", "s2"],
        "sequence_order": [1, 2, 3, 1, 2, 3],
        "state": ["home", "search", "product", "home", "category", "product"],
    }
)

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

states = g.summarise_sequence_states(prepared.data)
distance = g.compute_sequence_distance(prepared.data, method="lcs")
network = g.create_transition_network(prepared.data, normalise="from")
```

<div class="gp3-inline-links">
  <a href="quickstart/">Quickstart</a>
  <a href="method-map/">Method map</a>
  <a href="examples/">Examples</a>
  <a href="plots/">Plot gallery</a>
  <a href="articles/">All articles</a>
  <a href="reference/">API reference</a>
</div>

## Visualise what changes across a sequence

<div class="gp3-gallery-two">
  <a href="plots/#sequence-index"><img src="assets/figures/sequence-index.svg" alt="Illustrative sequence index plot"></a>
  <a href="plots/#state-distribution"><img src="assets/figures/state-distribution.svg" alt="Illustrative state distribution plot"></a>
  <a href="plots/#distance-heatmap"><img src="assets/figures/distance-heatmap.svg" alt="Illustrative sequence distance heatmap"></a>
  <a href="plots/#transition-network"><img src="assets/figures/transition-network.svg" alt="Illustrative transition network"></a>
</div>

The thumbnails are documentation illustrations of the supported plot families.
Use the [plot gallery](plots.md) for the exact package calls and interpretation
notes.

## What makes the package different

<div class="gp3-card-grid gp3-card-grid--compact">

<div class="gp3-card">
<h3>Parity-first</h3>
<p>The frozen R 0.3.0 release remains the behavioral reference. Public signatures, deterministic oracles, and deliberate translation boundaries are documented rather than hidden.</p>
</div>

<div class="gp3-card">
<h3>Audit-first</h3>
<p>Validation and preparation are explicit objects and policies, so preprocessing choices can be inspected and reported instead of being implicit.</p>
</div>

<div class="gp3-card">
<h3>Research-design aware</h3>
<p>Descriptive sequence differences, randomization-based inference, and causal interpretation are kept conceptually separate.</p>
</div>

<div class="gp3-card">
<h3>Python-native</h3>
<p>Outputs integrate with pandas, NumPy, SciPy, Matplotlib, and NetworkX while preserving the frozen scientific contracts.</p>
</div>

</div>

## Interpretation boundary

!!! warning "Sequence structure is not a psychological state"
    Sequence structure does not independently establish attention, cognition,
    emotion, comprehension, personality, intention, deception, diagnosis, or
    causality. Observational group contrasts remain associational unless a
    defensible randomized design supports causal interpretation.

## Release and reproducibility status

Version **0.1.2** is published through GitHub Releases and PyPI. The frozen
scientific/API contracts remain **81 / 81** public R counterparts, **81 / 81**
audited signatures, and **130 / 130** translated frozen R test blocks; the Python
quality suite now contains **292** tests with 100% statement and branch coverage. Cross-language boundaries that cannot be
made bit-identical are listed in [Parity & validation](parity.md).

- [Reproducibility guide](reproducibility.md)
- [Reporting checklist](reporting.md)
- [Release status](release-readiness.md)
- [Frozen public API](reference/api.md)
- [Zenodo DOI](https://doi.org/10.5281/zenodo.22166449)
