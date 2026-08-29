# Latent Sequence Models and Optional Adapters

```python
import pandas as pd
import gp3sequencespypy as g
```

## Interpretation boundary

Hidden states and mixture components are statistical constructs. They must not
be labelled as emotions, cognitive states, diagnoses, intentions, or causal
mechanisms without independent theory, design, and validation.

## Synthetic categorical sequences

```python
paths = {'s1': ['A', 'A', 'B', 'B', 'C'], 's2': ['A', 'B', 'B', 'C', 'C'], 's3': ['A', 'A', 'B', 'C', 'C'], 's4': ['D', 'D', 'C', 'C', 'B'], 's5': ['D', 'C', 'C', 'B', 'B'], 's6': ['D', 'D', 'C', 'B', 'B']}
groups = None
rows = []
for sid, states in paths.items():
    for order, state in enumerate(states, start=1):
        row = {"sequence_id": sid, "sequence_order": order, "state": state}
        rows.append(row)
sequence_data = pd.DataFrame(rows)
```

## Categorical HMM

```python
hmm = g.fit_sequence_hmm(sequence_data, n_states=2, max_iter=100, seed=11)
print(g.summarise_sequence_hmm(hmm)["fit"])
print(g.decode_sequence_states(hmm).head())
```

## Mixture HMM

```python
mixture = g.fit_sequence_hmm_mixture(
    sequence_data, n_components=2, n_states=2, max_iter=100, seed=11
)
print(mixture.responsibilities)
print(g.summarise_sequence_hmm(mixture)["fit"])
```

## Estimation limitations

The native estimators are compact, dependency-light, time-homogeneous
categorical HMM workflows. EM estimation can converge to local optima, latent
state labels are exchangeable, and AIC or BIC differences do not validate a
substantive interpretation. Analysts should inspect convergence histories, fit
multiple seeded specifications when the result matters, and use a specialist
package such as `seqHMM` for multichannel, covariate-dependent, or more complex
models.

## Optional ecosystem adapters

The adapters are dependency-safe semantic handoffs and do not make specialist
packages mandatory dependencies.

```python
grp_input = g.as_grpstring_data(sequence_data)
print(grp_input.key)
print(grp_input.strings)
traminer_like = g.as_traminer_sequences(sequence_data)
seqhmm_like = g.as_seqhmm_sequences(sequence_data)
arules_like = g.as_arules_sequences(sequence_data)
```
