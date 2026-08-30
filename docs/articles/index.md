# Articles

The documentation includes the complete set of **15 Python-native ports** of the
frozen `gp3sequences 0.3.0` vignette topics. Use this page as a methodological
reading path rather than a flat list.

<div class="gp3-article-banner">
<strong>New to the package?</strong>
Start with <a href="getting-started-with-gp3sequences/">Getting Started</a>,
then use <a href="choosing-a-sequence-analysis-method/">Choosing a
Sequence-Analysis Method</a>.
</div>

## Foundations

<div class="gp3-card-grid gp3-card-grid--compact">

<div class="gp3-card">
<h3><a href="getting-started-with-gp3sequences/">Getting Started</a></h3>
<p>End-to-end structural workflow: audit, preparation, summaries, motifs, distance, clustering, consensus, groups, and transitions.</p>
</div>

<div class="gp3-card">
<h3><a href="choosing-a-sequence-analysis-method/">Choosing a Method</a></h3>
<p>Map structural research questions to motifs, consensus, distances, networks, HMMs, panels, or design-aware inference.</p>
</div>

<div class="gp3-card">
<h3><a href="sequence-data-validation-and-preparation/">Validation & Preparation</a></h3>
<p>Make sequence order, missingness, duration, repeated states, and preprocessing decisions explicit.</p>
</div>

<div class="gp3-card">
<h3><a href="reproducible-sequence-analysis-case-study/">Synthetic Case Study</a></h3>
<p>Combine the package layers in one reproducible analysis without treating every method as mandatory.</p>
</div>

</div>

## Pattern discovery and descriptive comparison

- [Contiguous Motif Workflow](contiguous-motif-workflow.md) — exact adjacent
  patterns, motif positions, prevalence, filtering, and reporting.
- [Bounded Non-Contiguous Subsequence Mining](noncontiguous-subsequence-mining.md)
  — ordered patterns with explicit gap / span constraints.
- [Consensus Sequences and Descriptive Group Comparisons](consensus-and-group-comparisons.md)
  — aligned modal structure and descriptive contrasts.

## Whole-sequence geometry

- [Sequence Distances, Clustering, and Stability](distances-clustering-and-stability.md)
  — distance families, clustering, representatives, validation, bootstrap
  stability, and ensemble logic.

## Transition structure and latent models

- [Transition Networks and Higher-Order Models](transition-networks-and-higher-order-models.md)
  — first-order directed networks, centrality, communities, higher-order
  contexts, backoff, and prediction.
- [Latent Sequence Models and Optional Adapters](latent-models-and-optional-adapters.md)
  — categorical and mixture HMMs plus optional ecosystem handoffs.
- [Multichannel and Covariate-Dependent HMMs](multichannel-and-covariate-hmms.md)
  — joint channels and covariate-dependent transition structure.

## Inference, longitudinal structure, and time

- [Design-Aware Sequence Group Inference](sequence-inference-and-randomization.md)
  — declared designs and randomization-based group testing.
- [Longitudinal and Panel Sequence Workflows](longitudinal-panel-sequences.md)
  — repeated sequence panels, change summaries, and panel comparisons.
- [Time-Varying Condition Comparisons](time-varying-condition-models.md)
  — changing transition probabilities and validated `mssm`-based smooth models.

## Visualisation

- [Extended Sequence Visualisations](extended-sequence-visualisations.md) —
  sequence index, state distribution, entropy, distance heatmap, cluster
  silhouette, and transition network views.
- [Plot gallery](../plots.md) — visual inventory plus exact plotting calls.

## Porting contract

Each methodology article retains the frozen vignette topic and methodological
scope while using Python scientific objects. R-only backend identities are
represented through documented semantic adapters rather than by pretending to
recreate S3/S4 object identity.

The article set is part of the frozen documentation contract: all 15 article
names are tested by the documentation suite.
