# FAQ and troubleshooting

## What data shape does gp3sequencespy expect?

The standard representation is long format: one row per observed categorical
state, an explicit sequence identifier, an explicit ordering variable, and a
state column. Optional duration and sequence-level metadata columns can be
carried alongside the sequence.

Start with `audit_sequence_data()` before relying on any downstream method.

## Can I pass Gazepoint data directly?

The package is vendor-neutral at the sequence-analysis layer. Use
`prepare_gp3tools_sequences()` when you have a compatible gp3tools-style
sequence table, or map your own columns into the standard sequence contract.
Raw gaze samples normally require event/AOI construction before they become
categorical sequences.

## Should repeated consecutive states be collapsed?

Only if that is part of the analysis specification. `prepare_sequence_data()`
can preserve or collapse repeated runs explicitly. Collapsing changes the
sequence representation and therefore can change motif, transition, distance,
and model results.

## Motif or subsequence?

A **motif** is contiguous. A **subsequence** preserves order while allowing
bounded gaps. Choose the representation that matches the research question and
report the length/gap/span constraints.

## Which distance should I use?

There is no universally best distance. Levenshtein, LCS, optimal matching, and
transition-profile distances encode different notions of similarity. Use the
[method map](method-map.md) and report the exact choice, normalization, and
costs.

## How many clusters should I use?

`k` is an analytical choice, not a fact discovered automatically by a single
index. Compare defensible specifications, inspect validation summaries, use
bootstrap stability where appropriate, and avoid turning clusters into latent
psychological types without external evidence.

## Are HMM states psychological or cognitive states?

No. They are latent statistical states. Substantive labels require independent
theory, measurement, design, and validation. Check convergence and alternative
starts before interpreting the model at all.

## Why are some R outputs represented differently in Python?

Python cannot provide literal R S3/S4 object identity. Adapters return native
Python structures while preserving the documented semantic handoff. Plotting
uses Matplotlib, randomization uses NumPy RNG streams, and the time-varying
backend uses the validated `mssm` translation. See [R → Python](r-to-python.md)
and [Parity & validation](parity.md).

## Can I make causal claims from a group comparison?

Not from descriptive group summaries. The design-aware inference API requires
an explicit design declaration. Even with randomization-based inference, causal
language depends on valid assignment, implementation, attrition handling, and a
well-defined estimand.

## Why does a plot look different from the R package?

The scientific plotting contract is semantic, not pixel identity. Python uses
Matplotlib and supports a keyword-only `ax=` extension for composition. Axis
content, plotted quantities, and documented defaults are the parity target.

## How do I make an analysis reproducible?

Pin the package version, preserve the raw ordered data, save validation and
preparation decisions, record seeds and method parameters, keep the environment
or lockfile, and retain package-native audit objects. See the
[reproducibility guide](reproducibility.md).

## What should I cite?

Record the exact package version and use the machine-readable `CITATION.cff` or
Zenodo archive metadata. Current archive DOI:
`10.5281/zenodo.22166449`.

## Where do I report bugs or request features?

Use the repository issue tracker and include the smallest reproducible example,
package/Python versions, and the relevant validation/audit output where
possible.
