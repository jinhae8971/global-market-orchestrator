"""Tests for global report persistence."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src import storage as storage_module
from src.config import Settings
from src.models import (
    AgentReport,
    CrossMarketAnalysis,
    GlobalNarrative,
    GlobalReport,
)


@pytest.fixture(autouse=True)
def tmp_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    s = Settings(anthropic_api_key="x", telegram_bot_token="x", telegram_chat_id="x",
                 repo_root=tmp_path)
    monkeypatch.setattr("src.storage.get_settings", lambda: s)
    (tmp_path / "docs" / "reports").mkdir(parents=True)
    yield s


def _report(date: str) -> GlobalReport:
    return GlobalReport(
        date=date, generated_at=datetime.now(UTC),
        agent_reports=[
            AgentReport(agent_key="crypto", agent_label="Crypto", agent_emoji="🚀",
                        date=date, dashboard_url=""),
        ],
        cross_analysis=CrossMarketAnalysis(
            global_risk_posture="Risk-On",
            capital_flow_direction="rotation into crypto",
        ),
        narrative=GlobalNarrative(
            macro_regime="expansion", flow_summary="risk-on",
            positioning_advice="overweight growth", week_over_week="stable",
        ),
    )


def test_write_and_index(tmp_settings):
    storage_module.write_report(_report("2026-04-14"))
    storage_module.write_report(_report("2026-04-15"))
    index = json.loads((tmp_settings.reports_dir / "index.json").read_text())
    assert index[0]["date"] == "2026-04-15"
    assert index[0]["risk_posture"] == "Risk-On"


def test_index_dedup(tmp_settings):
    storage_module.write_report(_report("2026-04-15"))
    storage_module.write_report(_report("2026-04-15"))
    index = json.loads((tmp_settings.reports_dir / "index.json").read_text())
    assert [e["date"] for e in index].count("2026-04-15") == 1
