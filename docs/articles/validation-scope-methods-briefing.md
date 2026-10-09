# Sequence analysis: validation scope and provenance

The September 2026 deep-search briefings did **not** identify a new scanpath similarity, HMM, semi-Markov or transition estimator whose validation justifies displacing the existing gp3sequencespy scientific surface. Accordingly, no speculative estimator is being introduced in this development tranche.

## Boundaries of existing sequence inference

Sequences belong to **participants**, **trials**, **sessions** and sometimes **datasets**. A transition table derived from adjacent gaze events can share observations, stimuli and study context across train/test folds even when its rows differ.

Before machine-learning evaluation, externally certify:

- temporal-block separation, trial separation, session separation and participant separation as different properties;
- participant and trial identity in the canonical sequence table;
- event-detector and AOI mapping provenance;
- order, duplicated state positions, undefined states and exposure denominators;
- genuine within-person pairing versus unpaired cross-source data.

The [GazeForge validation-scope certificates](https://stefanosbalaskas.github.io/GazeForge/validation-scope-certificates/) can independently audit sample/trial/participant/dataset split identities; its research programme extends session and temporal-block checks. Those validation tools do not automatically certify every sequence model.

## Appropriate reporting

Use `participant-generalization` only when no participant ID appears in both training and test groups. Block-wise disjointness alone does not establish unseen-person inference. Separate transition probabilities from causal claims about attentional mechanisms; analyses of event-derived states should report detector and AOI sensitivity where material.

This page is documentation-only. It does not change the public sequence API, installed version, benchmark status or release readiness.
