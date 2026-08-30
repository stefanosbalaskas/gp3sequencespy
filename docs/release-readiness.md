# Release status

## gp3sequencespy 0.1.1

Version **0.1.1** is the current stable PyPI release and a
metadata / release-infrastructure maintenance release over the frozen 0.1.0
scientific implementation.

<div class="gp3-release-panel">
<span class="gp3-status gp3-status--good">PyPI published</span>
<span class="gp3-status gp3-status--good">GitHub Release published</span>
<span class="gp3-status gp3-status--good">Trusted Publishing verified</span>
<span class="gp3-status gp3-status--good">Docs live</span>
</div>

## Scientific contract

No scientific algorithm, public scientific API, plotting semantics, or frozen R
0.3.0 parity contract changed between 0.1.0 and 0.1.1.

- frozen API: **81 / 81**
- frozen signatures: **81 / 81**
- translated R test blocks: **130 / 130**
- unexplained signature drift: **0**
- Python tests: **182**
- deterministic R-oracle tranches: **PASS**
- strict MkDocs build: **PASS**
- fresh production PyPI install: **PASS**

## Distribution identity

Version 0.1.1 was built from release commit:

`b19cfb6931ce7785f32d2f3eacf2b880f050400d`

and published through GitHub Actions Trusted Publishing / OIDC.

## Documentation

The site is built with MkDocs Material and deployed from the generated
`gh-pages` branch. GitHub Pages serves that branch from its root.

## Archive

Zenodo DOI: [10.5281/zenodo.22166449](https://doi.org/10.5281/zenodo.22166449)

## What to cite

Use the exact software version in methods / reproducibility statements and use
the repository `CITATION.cff` or Zenodo archive metadata for formal citation.

## Historical release

The original **0.1.0** scientific release remains immutable. Version 0.1.1 was
created specifically to correct public metadata, record the DOI, and exercise
the token-free PyPI publishing path.
