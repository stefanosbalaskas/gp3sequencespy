# Multichannel and Covariate-Dependent HMMs

```python
import pandas as pd
import gp3sequencespy as g
```

## Scope and guardrails

Multichannel HMMs model several categorical observation channels through a
shared finite-state process. Covariate-dependent HMMs allow initial and
transition probabilities to vary with declared numeric covariates. Latent states
are statistical model states; labels should not be treated as emotion,
cognition, diagnosis, or causal mechanisms.

## Synthetic data

```python
paths = {'s1': ['A', 'A', 'B', 'B', 'C'], 's2': ['A', 'B', 'B', 'C', 'C'], 's3': ['A', 'A', 'B', 'C', 'C'], 's4': ['D', 'D', 'C', 'C', 'B'], 's5': ['D', 'C', 'C', 'B', 'B'], 's6': ['D', 'D', 'C', 'B', 'B']}
rows=[]
for i,(sid,states) in enumerate(paths.items()):
    for order,state in enumerate(states,1):
        rows.append({"sequence_id":sid,"sequence_order":order,"state":state,"channel_context":"x" if order<4 else "y","condition_numeric":float(i%2)})
data=pd.DataFrame(rows)
```

## Multichannel model

```python
multi = g.fit_multichannel_sequence_hmm(
    data, n_states=2, channel_cols=["state", "channel_context"], max_iter=50, seed=11
)
print(g.summarise_multichannel_sequence_hmm(multi)["fit"])
print(g.decode_multichannel_sequence_states(multi).head())
```

```python
ax = g.plot_multichannel_sequence_hmm(multi, channel="state")
```

## Covariate-dependent model

```python
covariate = g.fit_covariate_sequence_hmm(
    data, n_states=2, initial_covariate_cols=["condition_numeric"],
    transition_covariate_cols=["condition_numeric"], max_iter=30, inner_maxit=50, seed=12
)
print(g.summarise_covariate_sequence_hmm(covariate)["fit"])
print(g.predict_covariate_transition_probabilities(
    covariate, pd.DataFrame({"condition_numeric": [0.0, 1.0]})
).head())
```

## Reporting

Report channel coding, state count, starting seed, convergence status,
log-likelihood history, AIC/BIC as descriptive criteria, covariate scaling,
and any sensitivity analyses. Multiple starts and simulation recovery should be
used before substantive interpretation.
