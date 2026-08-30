# Reporting guide

A sequence-analysis report should make the **data representation**, **method
choices**, **validation**, and **interpretation boundary** inspectable.

## Minimum methods checklist

| Component | Report at minimum |
|---|---|
| Sequence unit | what one sequence represents |
| Ordering | order / time variable and tie handling |
| State definition | state labels, coding rules, unknown-state policy |
| Missingness | missing-state and missing-position handling |
| Repeated states | preserve / collapse policy |
| Duration | whether durations are analysed, weighted, or ignored |
| Motifs | length range, overlap policy, prevalence denominator, filters |
| Distances | distance family, normalisation, insertion/deletion/substitution costs |
| Clustering | method, linkage, `k`, seed, validation and stability checks |
| Networks | weight definition, normalisation, self-transition policy |
| HMMs | state count, components/channels, seed, convergence, likelihood criteria |
| Group inference | design declaration, statistic, assignment mechanism, permutations |
| Time-varying models | target transition, smoothing / basis specification, prediction target |
| Software | `gp3sequencespy` version and optional backends |
| Reproducibility | seed(s), analysis audit, environment / lockfile where relevant |

## Example methods paragraph

> Ordered categorical sequences were analysed with `gp3sequencespy 0.1.1`.
> Sequence order was defined explicitly by the event-order field. Missing states
> and duplicate positions were treated as errors and repeated states were
> preserved. Whole-sequence dissimilarity was quantified using normalized LCS
> distance. A two-cluster average-linkage hierarchical solution was summarised
> descriptively and evaluated with cluster validation and bootstrap stability.
> First-order transition networks used row-normalized outgoing transition
> proportions. All substantive interpretation was restricted to observed
> sequence structure.

Adapt that paragraph to the actual analysis. Do not copy settings that were not
used.

## Reporting motifs

State:

- motif length range;
- whether overlapping occurrences were allowed;
- the sequence-prevalence denominator;
- minimum occurrence / sequence / prevalence filters;
- ranking and top-N rules.

## Reporting distance and clustering

State:

- distance method and normalization;
- any non-default edit / substitution costs;
- clustering algorithm and linkage;
- `k`;
- medoid / representative rule;
- validation criteria;
- bootstrap design, number of repetitions, and seed.

## Reporting transition networks

State:

- whether self-transitions were included;
- whether edges are counts, global shares, or conditional outgoing shares;
- any thresholding / smoothing;
- how centrality and communities were computed.

!!! warning
    Network centrality does not automatically represent attentional priority,
    importance, influence, or preference.

## Reporting HMMs

State:

- number of latent states;
- mixture components or channels where relevant;
- starting / seed strategy;
- pseudocount or smoothing;
- optimization tolerance and iteration cap;
- convergence status;
- likelihood, AIC/BIC where available;
- decoding method;
- sensitivity to alternative seeded fits.

Hidden-state labels are exchangeable statistical labels.

## Reporting randomization inference

State:

- declared design;
- grouping / assignment variable;
- exchangeability or randomization unit;
- statistic;
- permutation count;
- seed;
- effect estimate separately from the randomization p-value.

A p-value does not repair an invalid assignment mechanism.

## Reporting software and provenance

```python
import gp3sequencespy as g

print(g.__version__)
print(g.sequence_capabilities())
```

Also retain the analysis environment or lockfile when the work is intended to
be exactly reproducible.

## Citation

Cite the software version used and archive DOI:

**DOI:** `10.5281/zenodo.22166449`

See the repository `CITATION.cff` for machine-readable citation metadata.

## Interpretation language

Prefer:

- “sequence structure differed between groups”;
- “the observed transition share was higher”;
- “the clustering solution separated these trajectories under the declared
  distance”;
- “the latent model assigned observations to two statistical states”.

Avoid unsupported language such as:

- “participants paid more attention”;
- “the cluster represents a cognitive strategy”;
- “centrality proves importance”;
- “the HMM identified emotional states”;
- “the group difference is causal” without a valid design.
