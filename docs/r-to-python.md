# R → Python translation guide

`gp3sequencespy` ports the frozen public contract of **gp3sequences 0.3.0** while
using native Python scientific objects and tooling.

## What is frozen

- 81 / 81 public R-function counterparts;
- 81 / 81 audited public signatures;
- 130 / 130 translated frozen R test blocks;
- 15 / 15 methodology/vignette topics;
- deterministic oracle tranches for the core, hierarchical/PAM, and
  time-varying-model contracts.

## What is intentionally Python-native

| R-side concept | Python-side representation | Contract |
|---|---|---|
| data frames / tibbles | pandas DataFrames | semantic data contract |
| distance objects | package-native distance result | matrix + labels + settings |
| igraph handoff | NetworkX graph | graph semantics, not R object identity |
| TraMineR / seqHMM style objects | structured adapters | semantic handoff |
| base-R graphics | Matplotlib | plotted quantity/default semantics |
| R random streams | NumPy RNG | seeded/statistical reproducibility |
| `mgcv` time model | `mssm` GAMM | validated model/prediction translation |

## Naming and calling style

The public function names intentionally stay close to the R package so a
methods section can be translated without inventing a second conceptual API.
Python objects, keyword arguments, exceptions, and return structures follow
Python conventions where necessary.

```python
import gp3sequencespy as g

validation = g.validate_sequence_data(
    data,
    "sequence_id",
    "sequence_order",
    "state",
)
```

## Plot composition

Frozen plot helpers preserve their documented method/default contract and add a
Python-only keyword-only `ax=` extension where applicable:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
g.plot_sequence_index(data, ax=ax)
```

This supports publication figure composition without claiming pixel-level
identity with base R.

## Randomized methods

Seeds are reproducible within the Python implementation, but R and NumPy do not
share bit-identical random-number streams. Cross-language validation therefore
checks deterministic/statistical contracts rather than matching every draw.

## Time-varying models

The default verified translation uses `mssm 1.2.5` and REML. Population-level
predictions exclude the participant random intercept to match the frozen R
prediction target. Non-default smoothing criteria outside the verified contract
should be treated as a documented boundary rather than assumed parity.

## Ecosystem adapters

Use adapters when an external engine or data representation is the better tool.
The package deliberately avoids pretending that Python-native objects are
literal R objects.

## How to report a translated analysis

State:

1. the R reference version (`gp3sequences 0.3.0`) when parity matters;
2. the Python package version;
3. any adapter/backend used;
4. random seeds and algorithm settings;
5. the documented cross-language boundary relevant to the method.

For the full audit record, see [Parity & validation](parity.md) and
[Reproducibility](reproducibility.md).
