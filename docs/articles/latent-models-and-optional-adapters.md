# Latent Sequence Models and Optional Adapters

Hidden states and mixture components are statistical constructs. They should
not be labelled as emotions, cognitive states, diagnoses, intentions, or causal
mechanisms without independent theory, design, and validation.

```python
import pandas as pd
import gp3sequencespy as g
```

## Synthetic categorical sequences

```python
paths = {
    "s1": ["A", "A", "B", "B", "C"],
    "s2": ["A", "B", "B", "C", "C"],
    "s3": ["A", "A", "B", "C", "C"],
    "s4": ["D", "D", "C", "C", "B"],
    "s5": ["D", "C", "C", "B", "B"],
    "s6": ["D", "D", "C", "B", "B"],
}

rows = []
for sequence_id, states in paths.items():
    for sequence_order, state in enumerate(states, start=1):
        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_order": sequence_order,
                "state": state,
            }
        )

sequence_data = pd.DataFrame(rows)
```

## Categorical HMM

```python
model = g.fit_sequence_hmm(
    sequence_data,
    n_states=2,
    max_iter=100,
    seed=11,
)
print(g.summarise_sequence_hmm(model)["fit"])
print(g.decode_sequence_states(model).head())
```

## Mixture HMM

```python
mixture = g.fit_sequence_hmm_mixture(
    sequence_data,
    n_components=2,
    n_states=2,
    max_iter=100,
    seed=11,
)
print(mixture.responsibilities)
```

Fit multiple seeded specifications when the result is consequential. EM can
converge to local optima, and latent-state labels are exchangeable.

## Multichannel and covariate-dependent HMMs

`gp3sequencespy` also provides dedicated multichannel and covariate-dependent
HMM workflows. Use the [multichannel/covariate article](multichannel-and-covariate-hmms.md)
for those APIs and their stronger reporting requirements.

Specialist engines remain appropriate for models beyond the supported package
scope, for alternative estimation strategies, or for extensive diagnostic /
model-selection workflows.

## Optional ecosystem adapters

Adapters provide explicit Python-native handoffs for several R ecosystem
representations and common Gazepoint/gp3tools-style inputs.

```python
grp_input = g.as_grpstring_data(sequence_data)
traminer_like = g.as_traminer_sequences(sequence_data)
seqhmm_like = g.as_seqhmm_sequences(sequence_data)
arules_like = g.as_arules_sequences(sequence_data)

print(grp_input.key)
print(grp_input.strings)
```

These adapters preserve semantic intent but do not pretend to create R S3/S4
objects inside Python. See [Parity & validation](../parity.md) for the explicit
cross-language boundary.
