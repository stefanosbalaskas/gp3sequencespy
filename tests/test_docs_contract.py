from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import gp3sequencespy as g

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"


def test_frozen_article_port_is_complete():
    manifest = json.loads((ROOT / "reference" / "article_manifest.json").read_text())
    frozen = {Path(item["filename"]).stem for item in manifest}
    actual = {path.stem for path in (DOCS / "articles").glob("*.md")} - {"index"}
    assert len(frozen) == 15
    assert frozen == actual


def test_api_reference_covers_all_81_frozen_functions():
    manifest = json.loads((ROOT / "reference" / "api_manifest.json").read_text())
    names = [item["name"] for item in manifest]
    text = (DOCS / "reference" / "api.md").read_text()
    documented = re.findall(r"::: gp3sequencespy\.([A-Za-z_][A-Za-z0-9_]*)", text)
    assert len(names) == 81
    assert documented == names
    assert all(hasattr(g, name) for name in names)


def test_all_python_doc_fences_parse():
    blocks = []
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for match in re.finditer(r"```python\n(.*?)```", text, flags=re.S):
            blocks.append((page, match.group(1)))
    assert len(blocks) >= 60
    for page, code in blocks:
        ast.parse(code, filename=str(page))


def test_mkdocs_nav_lists_all_articles():
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for article in (DOCS / "articles").glob("*.md"):
        if article.name == "index.md":
            continue
        assert f"articles/{article.name}" in config


def test_homepage_outer_wrapper_stays_raw_html():
    """Prevent md_in_html from escaping indented homepage layout fragments."""
    text = (DOCS / "index.md").read_text(encoding="utf-8")
    assert '<div class="gp3-home">' in text
    assert '<div class="gp3-home" markdown=' not in text
    assert 'markdown="1"' not in text
    assert '<div class="gp3-trust-row"' in text
