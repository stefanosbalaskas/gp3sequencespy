"""Research-only cross-domain categorical sequence-transfer diagnostics."""
from __future__ import annotations

from collections import Counter
from math import log

import numpy as np
import pandas as pd


def _transitions(sequences):
    counts = Counter()
    bigrams = Counter()
    for seq in sequences:
        counts.update(seq)
        bigrams.update(zip(seq[:-1], seq[1:], strict=True))
    return counts, bigrams


def _js(p, q):
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    p = p / p.sum()
    q = q / q.sum()
    middle = (p + q) / 2
    return float((np.sum(np.where(p > 0, p * np.log2(np.maximum(p, 1e-300) / middle), 0))
                  + np.sum(np.where(q > 0, q * np.log2(np.maximum(q, 1e-300) / middle), 0))) / 2)


def _predictive_nll(train, test, vocabulary, alpha=1.0):
    n_states = len(vocabulary)
    _, bigrams = _transitions(train)
    outgoing = Counter()
    for (a, _), count in bigrams.items():
        outgoing[a] += count
    losses = []
    for sequence in test:
        for a, b in zip(sequence[:-1], sequence[1:], strict=True):
            prob = (bigrams[(a, b)] + alpha) / (outgoing[a] + alpha * n_states)
            losses.append(-log(prob))
    return float(np.mean(losses)) if losses else np.nan



def _balanced_source_nll(sources, test, vocabulary, alpha=1.0):
    """Log loss of an equal-source-weight mixture of transition probabilities."""
    v = len(vocabulary)
    source_models = []
    for sequences in sources:
        _, bigrams = _transitions(sequences)
        outgoing = Counter()
        for (a, _), n in bigrams.items():
            outgoing[a] += n
        source_models.append((bigrams, outgoing))
    losses = []
    for sequence in test:
        for a, b in zip(sequence[:-1], sequence[1:], strict=True):
            prob = np.mean([
                (pairs[(a, b)] + alpha) / (outgoing[a] + alpha * v)
                for pairs, outgoing in source_models
            ])
            losses.append(-log(float(prob)))
    return float(np.mean(losses)) if losses else np.nan


def _transition_conditional_entropy(sequences):
    _, bigrams = _transitions(sequences)
    n = sum(bigrams.values())
    if n == 0:
        return np.nan
    outgoing = Counter()
    for (a, _), count in bigrams.items():
        outgoing[a] += count
    return float(-sum(
        (count / n) * np.log2(count / outgoing[a])
        for (a, _), count in bigrams.items()
    ))


def sequence_transfer_audit(
    data: pd.DataFrame,
    *,
    dataset_col: str = "dataset_id",
    participant_col: str = "participant_id",
    sequence_col: str = "sequence_id",
    order_col: str = "step",
    state_col: str = "state",
) -> dict:
    """Compare domain token/transition JS and participant-held-out log loss.

    A target domain is split into deterministic whole-participant development
    and evaluation partitions. Source domain models never use target samples.
    The pooled baseline weights source *sequences* by frequency and can be
    dominated by larger corpora. No causal or universal gaze-language claim.
    """
    required = [dataset_col, participant_col, sequence_col, order_col, state_col]
    if not set(required).issubset(data.columns):
        raise ValueError("required sequence/domain identifiers missing")
    if data[required].isna().any().any():
        raise ValueError("identifiers and states must be complete")
    if data.duplicated([dataset_col, participant_col, sequence_col, order_col]).any():
        raise ValueError("duplicate within-sequence order")
    if (data[state_col].astype(str).str.len() == 0).any():
        raise ValueError("empty state")
    datasets = sorted(data[dataset_col].unique(), key=str)
    if len(datasets) < 2:
        raise ValueError("at least two datasets required")
    prepared = {}
    for dataset in datasets:
        frame = data[data[dataset_col] == dataset].copy()
        sequences = []
        mapping = {}
        for (participant, seq_id), group in frame.groupby(
                [participant_col, sequence_col], sort=False):
            group = group.sort_values(order_col, kind="stable")
            if len(group) < 2:
                raise ValueError("sequences require at least two states")
            values = group[state_col].astype(str).tolist()
            sequences.append(values)
            mapping.setdefault(str(participant), []).append(values)
        if len(mapping) < 2:
            raise ValueError("each domain requires at least two participants")
        prepared[dataset] = (sequences, mapping)
    participant_id_sets = [set(mapping) for _, mapping in prepared.values()]
    for i in range(len(participant_id_sets)):
        for j in range(i + 1, len(participant_id_sets)):
            if participant_id_sets[i] & participant_id_sets[j]:
                raise ValueError(
                    "participant identity overlap across datasets; "
                    "external transfer claim is ineligible"
                )
    vocabulary = sorted({state for sequences, _ in prepared.values()
                         for seq in sequences for state in seq})
    tokens = {name: _transitions(prepared[name][0])[0] for name in datasets}
    transitions = {name: _transitions(prepared[name][0])[1] for name in datasets}
    all_pairs = sorted(set().union(*(set(t) for t in transitions.values())))
    comparisons = []
    for i, source in enumerate(datasets):
        for target in datasets[i + 1:]:
            p = [tokens[source][v] for v in vocabulary]
            q = [tokens[target][v] for v in vocabulary]
            trans_p = [transitions[source][v] for v in all_pairs]
            trans_q = [transitions[target][v] for v in all_pairs]
            comparisons.append({
                "source": source, "target": target,
                "token_js_bits": _js(p, q),
                "transition_js_bits": _js(trans_p, trans_q),
            })
    prediction = []
    per_source_prediction = []
    for target in datasets:
        target_map = prepared[target][1]
        participants = sorted(target_map)
        train_names = participants[::2]
        test_names = participants[1::2]
        if not test_names:
            raise ValueError("target evaluation requires held-out participants")
        target_train = [seq for p in train_names for seq in target_map[p]]
        target_test = [seq for p in test_names for seq in target_map[p]]
        external = [seq for name in datasets if name != target
                    for seq in prepared[name][0]]
        source_datasets = [name for name in datasets if name != target]
        for name in source_datasets:
            per_source_prediction.append({
                "source": name, "target": target,
                "target_holdout_nll": _predictive_nll(prepared[name][0], target_test, vocabulary),
            })
        prediction.append({
            "target": target,
            "target_trained_holdout_nll": _predictive_nll(target_train, target_test, vocabulary),
            "out_of_domain_nll": _predictive_nll(external, target_test, vocabulary),
            "equal_source_mixture_nll": _balanced_source_nll(
                [prepared[name][0] for name in source_datasets], target_test, vocabulary),
            "target_transition_entropy_bits": _transition_conditional_entropy(prepared[target][0]),
            "target_train_participants": len(train_names),
            "target_holdout_participants": len(test_names),
            "target_holdout_sequences": len(target_test),
        })
    return {
        "domain_comparisons": pd.DataFrame(comparisons),
        "heldout_prediction": pd.DataFrame(prediction),
        "source_specific_prediction": pd.DataFrame(per_source_prediction),
        "claim_boundary": ("Descriptive tokens and matched-target evaluation; "
                           "no cross-domain universal representation."),
    }
