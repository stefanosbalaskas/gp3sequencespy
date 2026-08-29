from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import gp3sequencespy as g

ROOT = Path(__file__).parents[1]


def _project() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_release_governance_files_exist():
    required = {
        "LICENSE",
        "CITATION.cff",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "RELEASE_CHECKLIST.md",
        "REPRODUCIBILITY.md",
        "PYPI_PUBLISHING.md",
    }
    assert required == {name for name in required if (ROOT / name).is_file()}
    assert (ROOT / "docs" / "release-readiness.md").is_file()
    assert (ROOT / "reference" / "release_publication_0.1.0.json").is_file()


def test_distribution_metadata_is_publication_ready_for_0_1_0():
    project = _project()
    assert project["version"] == g.__version__ == "0.1.0"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert "Development Status :: 4 - Beta" in project["classifiers"]
    assert "Programming Language :: Python :: 3.14" in project["classifiers"]
    assert set(project["urls"]) >= {"Homepage", "Documentation", "Source", "Issues", "Changelog"}
    assert set(project["optional-dependencies"]) >= {"dev", "docs", "time", "release"}


def test_citation_and_changelog_match_package_version():
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "version: 0.1.0" in citation
    assert "## [0.1.0] - 2026-08-30" in changelog


def test_reproducibility_document_freezes_authoritative_r_reference():
    text = (ROOT / "REPRODUCIBILITY.md").read_text(encoding="utf-8")
    assert "gp3sequences` **0.3.0**" in text
    assert "1d2ca1d72ebd375292fc9bdd0f41848b8224f9e1ae9d34acbd9469f103bf5b8d" in text
    assert "4ebf0bebea2955c5f98f8ddf0fe03e81d0b7ac3a" in text


def test_stable_release_gate_records_completed_r_oracle_review():
    checklist = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Required before stable 0.1.0" in checklist
    # The checklist preserves the executable oracle gates and records completion.
    assert "generate_reference_outputs.R" in checklist
    assert "PARITY_EXCEPTIONS.md" in checklist
    assert "- [x] Review every remaining entry in `PARITY_EXCEPTIONS.md`" in checklist
    assert "- [x] Create tag `v0.1.0`" in checklist
    assert "- [x] Publish the exact frozen `0.1.0` wheel and sdist to production PyPI." in checklist


def test_release_check_workflow_validates_but_does_not_publish():
    workflow = (ROOT / ".github/workflows/release-check.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in workflow
    assert "tags:" in workflow and '"v*"' in workflow
    assert "validate-pyproject" in workflow
    assert "twine check" in workflow
    assert "actions/upload-artifact@v7.0.1" in workflow
    assert not re.search(r"pypi|publish-package|trusted.publisher", workflow, flags=re.IGNORECASE)

    publisher = (ROOT / ".github/workflows/publish-pypi.yml").read_text(encoding="utf-8")
    assert "release:" in publisher and "types: [published]" in publisher
    assert "environment:" in publisher and "name: pypi" in publisher
    assert publisher.count("id-token: write") == 1
    assert "actions/upload-artifact@v7.0.1" in publisher
    assert "actions/download-artifact@v8.0.1" in publisher
    assert "pypa/gh-action-pypi-publish@release/v1" in publisher
    assert "gh release download" in publisher
    assert "twine check --strict" in publisher
    assert "TWINE_PASSWORD" not in publisher
    assert "PYPI_TOKEN" not in publisher
    assert "secrets." not in publisher

    record = json.loads(
        (ROOT / "reference" / "release_publication_0.1.0.json").read_text(encoding="utf-8")
    )
    assert record["git_commit"] == "28f06a571889bf9db760d00c47e1252d3836679a"
    assert record["git_tag"] == "v0.1.0"
    assert record["wheel"]["sha256"] == (
        "97725d0b34872b79c9f9cb4da57f14a788a8920880a0a415c13669d281a39525"
    )
    assert record["sdist"]["sha256"] == (
        "e01ff3ac4ec0cbede48b1019e4bcabddd38b9587df3fe541ce66aff585bf7e19"
    )
