# gp3sequencespy

**Transparent, reproducible, and auditable analysis of ordered categorical sequences in Python.**

`gp3sequencespy` is the Python port of the frozen `gp3sequences 0.3.0` public contract. The current alpha exposes all 81 frozen R counterparts and carries a one-to-one behavioral test ledger for all 130 frozen R `test_that()` blocks.

## What the package covers

- validation and explicit preparation of long-format sequences
- state, transition, path, motif, and subsequence summaries
- whole-sequence distances, clustering, validation, representatives, ensembles, and stability
- consensus sequences and descriptive group comparison
- transition networks and higher-order Markov structure
- categorical, mixture, multichannel, and covariate-dependent HMMs
- design-aware randomization inference
- longitudinal panels and time-varying sequence models
- Python-native adapters, plots, audit objects, and parity tooling

## Interpretation boundary

Outputs are structural or statistical. They do not independently establish attention, cognition, emotion, comprehension, intention, diagnosis, causality, or other psychological attributes. Causal claims additionally require a defensible study design and assignment mechanism.

## Start here

Read [Getting Started](articles/getting-started-with-gp3sequences.md), then use [Choosing a Sequence Analysis Method](articles/choosing-a-sequence-analysis-method.md) to select a workflow.

## Release status

See [Release readiness](release-readiness.md) for the current alpha freeze, packaging gates, and the explicit deterministic R-oracle requirement before stable `0.1.0`.
