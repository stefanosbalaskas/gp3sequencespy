# gp3sequencespy quality-completion tranche

Baseline measured on Python 3.13 with all optional extras installed:

- statements: 4,565
- statement coverage: 88.018%
- branches: 1,704
- branch coverage: 71.185%
- missing statements: 547
- missing branches: 491
- combined coverage.py score: 83.442%

The baseline also exposed a PyArrow compatibility defect in repeated-state collapsing. The quality-completion patch changes the grouping computation to a NumPy-backed boolean cumulative sum and adds an explicit `string[pyarrow]` regression test.

This tranche intentionally does not weaken parity gates, remove tests, alter the frozen 81-function public API, or mutate the published `v0.1.1` tag/PyPI artifacts.
