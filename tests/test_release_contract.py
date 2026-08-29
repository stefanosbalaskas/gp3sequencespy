from __future__ import annotations

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
    }
    assert required == {name for name in required if (ROOT / name).is_file()}
    assert (ROOT / "docs" / "release-readiness.md").is_file()


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


def test_stable_release_is_explicitly_blocked_on_r_oracle_review():
    checklist = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Required before stable 0.1.0" in checklist
    # The checklist decomposes the oracle gate into executable steps rather than a slogan.
    assert "generate_reference_outputs.R" in checklist
    assert "PARITY_EXCEPTIONS.md" in checklist
    assert "- [x] Review every remaining entry in `PARITY_EXCEPTIONS.md`" in checklist
    assert "- [ ] Create tag `v0.1.0`" in checklist


def test_release_check_workflow_validates_but_does_not_publish():
    workflow = (ROOT / ".github/workflows/release-check.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in workflow
    assert "tags:" in workflow and '"v*"' in workflow
    assert "validate-pyproject" in workflow
    assert "twine check" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert not re.search(r"pypi|publish-package|trusted.publisher", workflow, flags=re.IGNORECASE)
