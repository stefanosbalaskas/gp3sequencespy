# Frozen R oracle outputs

The authoritative behavioral reference is the user-supplied `gp3sequences_0.3.0.tar.gz` artifact with SHA-256:

`1d2ca1d72ebd375292fc9bdd0f41848b8224f9e1ae9d34acbd9469f103bf5b8d`

Reference outputs are intentionally **not fabricated or committed from Python**. Generate them with an R installation by setting `GP3SEQUENCES_R_TARBALL` to that exact artifact and running:

```sh
Rscript parity/r_scripts/generate_reference_outputs.R . parity/actual/r
python -m parity.generate_python_outputs
python parity/compare_oracle.py
```

The current execution environment used to develop this tranche has no R executable, so the R side of the oracle has not yet been executed. Until it is, numerical parity claims remain bounded by `PARITY_EXCEPTIONS.md` and `PARITY_TEST_MATRIX.md`.
