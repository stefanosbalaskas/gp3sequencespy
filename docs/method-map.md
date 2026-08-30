# Method map

Choose a sequence method from the **structural question** you are asking, not
from the visual result you hope to obtain.

## Decision table

| Research question | Primary function(s) | Main object / output | Key decision to report |
|---|---|---|---|
| Are the input sequences valid and explicitly ordered? | `audit_sequence_data()`, `validate_sequence_data()` | issue / validation tables | ordering, missing-state, duplicate-position policy |
| Which states dominate overall or by position? | `summarise_sequence_states()` | state shares / counts | weighting, duration use, grouping |
| Which direct transitions dominate? | `summarise_sequence_transitions()` | transition table | self-transitions, denominator |
| Which exact adjacent patterns recur? | `extract_sequence_ngrams()` | motif occurrences | motif length, overlap rule |
| Which non-adjacent ordered patterns recur? | `extract_sequence_subsequences()` | subsequences | span / gap constraints |
| What is a representative aligned path? | `create_consensus_sequence()` | consensus sequence | alignment, tie policy, missing positions |
| How different are complete sequences? | `compute_sequence_distance()` | pairwise distance matrix | distance family, normalisation, costs |
| Do sequences form useful descriptive clusters? | `cluster_sequences()`, `validate_sequence_clusters()` | assignments / validation | `k`, linkage/method, distance choice |
| Are clusters stable under resampling? | `bootstrap_sequence_clusters()` | stability results | bootstrap design, seed, repetitions |
| Which trajectories represent a cluster? | `extract_representative_sequences()` | medoids / representatives | representation criterion |
| What does transition structure look like as a graph? | `create_transition_network()` | weighted directed network | weight normalisation, self-loops |
| Do recent states improve next-state prediction? | `fit_higher_order_transition_model()` | higher-order transition model | order, smoothing, backoff |
| Is a compact latent-state model useful? | `fit_sequence_hmm()` | categorical HMM | number of states, seed, convergence |
| Are there multiple latent sequence components? | `fit_sequence_hmm_mixture()` | mixture model | components, states, seeded fits |
| Do multiple channels need joint latent modelling? | `fit_multichannel_sequence_hmm()` | multichannel HMM | channel representation, state count |
| Do covariates predict transition probabilities? | `fit_covariate_sequence_hmm()` | covariate HMM | covariates, reference levels |
| Is a declared group difference compatible with random assignment? | `declare_sequence_comparison_design()`, `test_sequence_group_difference()` | randomization inference | assignment mechanism, statistic |
| How does structure change across panels / waves? | `prepare_sequence_panel()`, `compare_sequence_panel_changes()` | panel summaries | panel identity, wave ordering |
| How do transition probabilities evolve over time? | `fit_time_varying_sequence_model()` | time-varying model | smoothness, prediction target |

## Workflow families

<div class="gp3-method-grid">

<div class="gp3-method-card">
<span class="gp3-method-kicker">Data</span>
<h3>Validation & preparation</h3>
<p>Begin here whenever sequence order, repeated states, durations, or metadata may be ambiguous.</p>
<a href="../articles/sequence-data-validation-and-preparation/">Read workflow →</a>
</div>

<div class="gp3-method-card">
<span class="gp3-method-kicker">Patterns</span>
<h3>Motifs & subsequences</h3>
<p>Use exact contiguous motifs for adjacent patterns and bounded subsequences for ordered non-adjacent structure.</p>
<a href="../articles/contiguous-motif-workflow/">Read motif workflow →</a>
</div>

<div class="gp3-method-card">
<span class="gp3-method-kicker">Geometry</span>
<h3>Distance & clustering</h3>
<p>Use whole-sequence dissimilarity when order and path shape matter beyond marginal state frequencies.</p>
<a href="../articles/distances-clustering-and-stability/">Read clustering workflow →</a>
</div>

<div class="gp3-method-card">
<span class="gp3-method-kicker">Graphs</span>
<h3>Transition networks</h3>
<p>Use directed networks when states are nodes and observed first-order movement is the core object.</p>
<a href="../articles/transition-networks-and-higher-order-models/">Read network workflow →</a>
</div>

<div class="gp3-method-card">
<span class="gp3-method-kicker">Latent</span>
<h3>HMM families</h3>
<p>Use latent models only when the statistical abstraction is justified and convergence / label exchangeability are reported.</p>
<a href="../articles/latent-models-and-optional-adapters/">Read HMM workflow →</a>
</div>

<div class="gp3-method-card">
<span class="gp3-method-kicker">Design</span>
<h3>Group inference</h3>
<p>Use declared comparison designs and randomization logic when moving beyond descriptive group differences.</p>
<a href="../articles/sequence-inference-and-randomization/">Read inference workflow →</a>
</div>

</div>

## Questions to answer before analysis

1. **What is the sequence unit?** Participant, trial, session, scanpath, episode,
   or another unit?
2. **What does order mean?** Event order, time bins, aligned positions, or panel
   wave?
3. **Are positions comparable across sequences?** If not, aligned consensus and
   position-wise summaries may be misleading.
4. **Is duration meaningful?** Decide whether counts, event durations, or both
   enter the estimand.
5. **What structural feature is primary?** States, motifs, complete path
   geometry, transitions, latent states, or time-varying probabilities?
6. **What is inferential versus descriptive?** A group contrast does not become
   causal merely because it is statistically tested.
7. **Which tuning choices matter?** Distance costs, `k`, motif thresholds, model
   state count, smoothing, seeds, and bootstrap repetitions should be declared.
8. **What would falsify the interpretation?** Plan sensitivity checks before
   inspecting the most attractive plot.

!!! warning "Do not reverse-engineer a method from a visually appealing result"
    Clusters, networks, HMM states, and motifs are representations of the
    declared sequence structure. They are not self-validating substantive
    categories.

## Suggested analysis path

```text
raw events
   │
   ├── audit / validate
   ▼
prepared ordered sequences
   │
   ├── descriptive summaries ──► states / transitions / paths
   ├── pattern mining ─────────► motifs / subsequences
   ├── whole-sequence geometry ► distance / clustering / stability
   ├── graph structure ────────► transition networks / higher-order models
   ├── latent structure ───────► HMM / mixture / multichannel / covariate HMM
   └── design-aware inference ─► declared comparison / randomization test
```

Next: [copy complete examples](examples.md) or browse the
[full methodology articles](articles/index.md).
