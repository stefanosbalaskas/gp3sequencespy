# Choosing a Sequence-Analysis Method

```python
import pandas as pd
import gp3sequencespypy as g
```

## Start with the research question

No single sequence method is universally preferable. Method choice should be
driven by the declared structural question, the sequence representation, the
intended comparison, and the assumptions that can be defended. Every workflow
should begin with `audit_sequence_data()`, `validate_sequence_data()`, and, when
needed, `prepare_sequence_data()`.

```python
method_guide = pd.DataFrame({
    "question": [
        "Which exact contiguous patterns recur?",
        "What path is most typical at aligned positions?",
        "How dissimilar are whole sequences?",
        "Which state transitions dominate?",
        "Is latent-state modeling justified?",
    ],
    "primary_tool": [
        "extract_sequence_ngrams",
        "create_consensus_sequence",
        "compute_sequence_distance",
        "create_transition_network",
        "fit_sequence_hmm",
    ],
})
method_guide
```

## Contiguous motifs

Use motifs when the unit of interest is an exact adjacent state window. Declare
minimum and maximum length, overlap handling, prevalence denominators,
filtering thresholds, and tie rules. Motifs do not capture non-contiguous
subsequences unless an external specialist method is used.

## Consensus sequences

Use aligned-position consensus when positions are meaningfully comparable
across sequences. Declare the missing-position policy, weighting, state order,
and deterministic tie method. A consensus is a modal structural summary, not a
normative or ideal pathway.

## Descriptive group comparison

Use `compare_sequence_groups()` when the objective is to compare observed state
shares, transition shares, prevalence, or sequence lengths across declared
groups. The function is deliberately descriptive and does not automatically
perform significance tests or causal attribution.

## Distances

`compute_sequence_distance()` supports four explicit families:

- Levenshtein distance for unit-cost edits;
- LCS distance for differences based on longest common subsequences;
- configurable optimal matching for declared insertion/deletion and
  substitution costs;
- transition-profile Euclidean distance for first-order transition
  distributions.

Normalisation and cost choices can materially change the geometry. Report them
and avoid selecting a distance solely because it produces visually convenient
clusters.

## Clustering, representatives, ensembles, and stability

Clustering is a downstream description of a chosen distance matrix. Declare
`k`, the clustering method, linkage, seed, and any optional-package settings.
Use validation and resampling summaries to assess the supplied solution, not to
claim that clusters are objectively true. Representatives minimise declared
within-cluster distance; they are not automatically typical in a substantive
sense.

## Transition networks

Use first-order networks when nodes and directed edges are the relevant
representation. Declare whether weights are counts, conditional proportions,
or global shares; whether self-transitions are included; and whether grouping
or smoothing is used. Centrality and communities are graph-structural outputs,
not psychological attributes.

## Higher-order transition models

Use higher-order models when recent context is part of the structural question.
Declare the order, smoothing, context separator, and backoff policy. Inspect
which context and order were actually used for every prediction, especially for
unseen contexts.

## Hidden and mixture sequence models

Use the native HMM helpers only for compact, time-homogeneous categorical
workflows. Report initial values, seed, pseudocount, tolerance, convergence
history, likelihood, AIC/BIC, and decoding method. Hidden-state labels and
mixture components are exchangeable statistical constructs. Multiple seeded
fits and specialist software are appropriate when the model is consequential
or more complex.

## Optional adapters

Adapters support TraMineR, arulesSequences, GrpString-style inputs, seqHMM,
igraph, and common gp3tools-style column names without making those packages or
formats mandatory. Use them when a specialist engine adds functionality that
should not be duplicated inside `gp3sequencespypy`.

## Minimum decision checklist

Before analysis, record:

1. the sequence unit and ordering variable;
2. state definitions and any preprocessing policy;
3. whether positions are aligned and comparable;
4. the structural estimand or descriptive question;
5. method parameters, costs, thresholds, seeds, and normalisation;
6. how missing positions, ties, unseen contexts, and optional dependencies are
   handled;
7. sensitivity checks and failure cases;
8. the interpretation boundary separating structure from substantive claims.

## Focused articles

The package website provides dedicated articles for contiguous motifs,
consensus and group comparison, distances and clustering, transition networks,
higher-order models, latent models, and optional adapters. The synthetic case
study demonstrates how these layers can be combined without treating every
method as mandatory.
