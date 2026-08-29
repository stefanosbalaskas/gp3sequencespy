# Time-Varying Condition Comparisons

```python
import pandas as pd
import gp3sequencespy as g
```

## Backend and R-parity target

The Python implementation uses `mssm` for binomial GAMMs. The frozen R 0.3.0 reference uses `mgcv::gam()` with group-specific smooths and an optional participant random-effect smooth. The Python mapping uses a group main effect, one penalized smooth of time per group, and an `mssm` random intercept when requested. Population-level prediction excludes the participant random effect, matching the frozen R prediction contract. The validated default smoothing criterion is `method="REML"`.

## Model target

`fit_time_varying_sequence_model()` estimates the probability of a declared
state or transition over aligned sequence time. It uses group-specific smooths
and can include a participant random-effect smooth. The model concerns a
predeclared structural outcome, not an unobserved psychological state.

## Synthetic repeated sequences

```python
import numpy as np
rng = np.random.default_rng(1)
rows=[]
for i in range(24):
    group = "g1" if i < 12 else "g2"
    for time in range(1, 9):
        lp = -0.5 + 0.25 * time + (0.5 if group == "g2" else 0.0)
        state = "A" if rng.random() < 1 / (1 + np.exp(-lp)) else "B"
        rows.append({"participant_id":f"p{i+1}","sequence_id":f"p{i+1}","sequence_order":time,"state":state,"group":group})
x=pd.DataFrame(rows)
```

## Fit and inspect

```python
model = g.fit_time_varying_sequence_model(
    x, group_col="group", participant_id_col="participant_id",
    target_state="A", k=4, include_random_effect=False
)
g.summarise_time_varying_sequence_model(model)["metadata"]
```

## Predictions

```python
predictions = g.predict_time_varying_sequence_model(model, level=0.95)
predictions.head()
```

```python
transition_model = g.fit_time_varying_sequence_model(
    x, group_col="group", participant_id_col="participant_id",
    outcome="transition", from_state="A", to_state="B", k=4, include_random_effect=False
)
```

## Transition outcomes

Use `outcome = "transition"` together with `from_state` and `to_state` to model
a predeclared transition. The time coordinate refers to the origin position.

## Interpretation

Pointwise intervals describe uncertainty conditional on the fitted model. A
time-varying association is not automatically a causal condition effect. Causal
language requires valid assignment, implementation, estimand definition, and an
analysis aligned with the experimental design.
