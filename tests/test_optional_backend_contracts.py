from __future__ import annotations

import builtins

import pytest

from gp3sequencespy import capabilities, time_models
from gp3sequencespy._exceptions import ModelFitError


def test_time_backend_absence_has_actionable_error(monkeypatch):
    original = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "mssm" or name.startswith("mssm."):
            raise ImportError("blocked for contract test")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ModelFitError, match="gp3sequencespy\\[time\\]"):
        time_models._require_time_backend()


def test_capability_table_reports_absent_optional_backends(monkeypatch):
    monkeypatch.setattr(
        capabilities, "_available", lambda package: package in {"networkx", "matplotlib", "scipy"}
    )
    table = capabilities.sequence_capabilities(include_optional=True, check_versions=False)
    assert table.loc[table.backend.eq("hmmlearn|pomegranate"), "available"].eq(False).all()
    assert table.loc[table.backend.eq("networkx"), "available"].eq(True).all()
