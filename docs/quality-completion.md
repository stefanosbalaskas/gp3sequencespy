# Quality-completion contract

`gp3sequencespy` treats code coverage as evidence about the exercised behavioral contract, not as a cosmetic badge.

The quality-completion tranche adds four permanent layers:

1. **Statement and branch coverage** for `src/gp3sequencespy` with a machine-readable deficit ledger.
2. **Property/invariant tests** for mathematical and structural contracts.
3. **Optional-backend tests**, including explicit absence behavior and PyArrow compatibility.
4. **Mutation smoke tests** for selected high-risk invariants, so execution alone is not accepted as sufficient evidence.

## Coverage policy

The final target is 100% justified statement coverage and 100% justified branch coverage. A line or branch may be excluded only when its exclusion is recorded and justified as structurally unreachable, platform-specific, or an optional-backend guard that is exercised in a dedicated environment. Blanket exclusion patterns are not permitted.

The coverage ledger is generated with:

```bash
uv run pytest -q --cov=gp3sequencespy --cov-branch --cov-report=json:coverage.json
uv run python scripts/generate_coverage_ledger.py coverage.json --require-statements 100 --require-branches 100
```

During the completion branch, the same script may be run without the final thresholds to produce the deficit map used to add tests. The thresholds are frozen at 100 only after the deficit ledger is empty or every remaining exception is explicitly justified.

## Mutation policy

`scripts/run_mutation_smoke.py` applies deterministic source mutations to selected invariants and requires the test suite to kill every mutation. This is deliberately small and auditable; it supplements, rather than replaces, broad test coverage.
