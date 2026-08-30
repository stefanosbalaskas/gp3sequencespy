# Choosing a Sequence-Analysis Method

No single sequence method is universally preferable. Start from the structural
question, the sequence representation, the study design, and the assumptions
you can defend.

```python
import gp3sequencespy as g
```

## First decision: what are you trying to learn?

| Research question | Primary tool | Typical companion |
|---|---|---|
| Are the inputs valid and reproducible? | `audit_sequence_data()` | `prepare_sequence_data()` |
| Which states or transitions dominate? | `summarise_sequence_states()` | `summarise_sequence_transitions()` |
| Which adjacent patterns recur? | `extract_sequence_ngrams()` | `summarise_sequence_motifs()` |
| Which ordered but gapped patterns recur? | `extract_sequence_subsequences()` | `filter_sequence_subsequences()` |
| What is typical at aligned positions? | `create_consensus_sequence()` | `summarise_consensus_agreement()` |
| How dissimilar are complete sequences? | `compute_sequence_distance()` | `summarise_sequence_distance()` |
| Do trajectories form useful groups? | `cluster_sequences()` | validation + bootstrap stability |
| Which transitions structure the system? | `create_transition_network()` | centrality / communities |
| Does recent context improve next-state description? | `fit_higher_order_transition_model()` | `predict_next_state()` |
| Are latent categorical states useful? | `fit_sequence_hmm()` | decoding + fit summaries |
| Do latent dynamics vary by channel or covariate? | multichannel / covariate HMMs | dedicated HMM article |
| Is a group contrast inferential? | `declare_sequence_comparison_design()` | `test_sequence_group_difference()` |
| Does a structural outcome vary smoothly over time? | `fit_time_varying_sequence_model()` | prediction + plot |

A larger decision table is available in the [method map](../method-map.md).

## Contiguous motifs

Use motifs when the unit of interest is an exact adjacent state window. Declare
length, overlap handling, prevalence denominator, filters, ranking, and tie
policy. Do not describe a non-contiguous pattern as a motif unless that is the
predeclared representation.

## Consensus sequences

Use aligned-position consensus only when positions are meaningfully comparable
across sequences. Report the missing-position policy, weighting, state order,
and deterministic tie handling. Consensus is descriptive.

## Whole-sequence distance

`compute_sequence_distance()` supports several explicit geometries, including
Levenshtein, LCS, configurable optimal matching, and transition-profile
distance. Normalisation and costs can change the geometry materially, so they
belong in the methods section.

## Clustering and stability

Clustering describes a supplied distance representation. Declare `k`, method,
linkage, seed, and any sampling settings. Then evaluate the supplied solution
with validation metrics and, where useful, bootstrap stability. Stability does
not prove that clusters are natural or substantively real.

## Transition networks and higher-order models

Use a first-order network when nodes and directed edges are the representation
of interest. Use a higher-order model when recent context is part of the
question. Always report whether edge weights are counts, outgoing conditional
shares, or global shares, and inspect the order/context actually used for
prediction.

## Hidden Markov models

Use HMMs when a latent-state model is substantively and statistically justified.
Report state count, starting/seed strategy, convergence, likelihood-based fit
criteria, decoding method, and sensitivity to alternative starts. Hidden-state
numbers are exchangeable statistical labels, not psychological labels.

## Group inference

Descriptive group comparisons and randomization-based tests answer different
questions. For inferential work, declare the design explicitly:

```python
design = g.declare_sequence_comparison_design(
    group_col="group",
    unit_col="participant_id",
    design="randomized",
)
```

If assignment was observational, keep causal language out of the interpretation.

## Minimum analysis specification

Before running the analysis, record:

1. sequence unit and order variable;
2. state definitions and preprocessing policy;
3. whether positions are aligned and comparable;
4. structural estimand or descriptive target;
5. costs, thresholds, normalization, seeds, and model settings;
6. missing positions, ties, unseen contexts, and optional dependencies;
7. sensitivity / validation checks;
8. interpretation boundary separating observed structure from substantive claims.

## Next steps

- [Quickstart](../quickstart.md)
- [Examples](../examples.md)
- [Plot gallery](../plots.md)
- [Reporting guide](../reporting.md)
