# Similar gaze tokens can hide different transition systems

![Rendered synthetic plot](../assets/october-2026-plot.svg)

**Methods briefing research implementation, 21 October 2026.**

![Original illustration of shared state vocabulary with distinct transitions](../assets/october-2026-sequence-transfer.svg)

The experimental `sequence_transfer_audit()` works on ordered categorical sequences. It compares token-frequency Jensen–Shannon divergence against transition-frequency Jensen–Shannon divergence, then evaluates a source-trained additive-smoothed first-order transition model on held-out target participants. Reports include separately trained sources, a dataset-equal probability mixture, a naive sample-frequency pooled comparator, and target-domain conditional transition entropy.

### Reproducible worked example

~~~python
import pandas as pd
from research.october_2026.sequence_transfer import sequence_transfer_audit

records = []
for domain, token_path in [("reading", ["A", "B", "A"]),
                           ("search", ["A", "A", "B"])]:
    for p in range(4):
        for step, state in enumerate(token_path):
            records.append([domain, f"{domain}-{p}", "trial", step, state])

data = pd.DataFrame(records, columns=[
    "dataset_id", "participant_id", "sequence_id", "step", "state"])
audit = sequence_transfer_audit(data)
print(audit["domain_comparisons"])
print(audit["heldout_prediction"])
~~~

The same vocabulary can have different conditional transitions. Naively pooled source models can obscure this difference; a future extension should compare source-equal weighting, dataset-size weighting, and target-specific models across real domains.

### Plot of the two divergence measures

~~~python
import matplotlib.pyplot as plt
row = audit["domain_comparisons"].iloc[0]
fig, ax = plt.subplots(figsize=(5, 3))
ax.bar(["Token JS", "Transition JS"],
       [row.token_js_bits, row.transition_js_bits])
ax.set_ylabel("Jensen–Shannon divergence (bits)")
ax.set_title("Synthetic domain comparison")
fig.tight_layout()
~~~

**Limitations:** A source/target split by dataset label does not by itself verify human identity independence across corpora. Sequence splitting can overstate participant generalization. The held-out target comparator in this research diagnostic is deliberately participant-disjoint, but this is not yet a validated external scanpath benchmark. Additional controls for device, task and sequence length are needed.
