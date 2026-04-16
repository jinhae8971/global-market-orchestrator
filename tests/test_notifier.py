"""Tests for Telegram message formatting."""
from __future__ import annotations

from datetime import UTC, datetime

from src.models import (
    AgentGainer,
    AgentReport,
    CrossMarketAnalysis,
    CrossMarketSignal,
    GlobalNarrative,
    GlobalReport,
)
from src.notifier import _esc, _format_message


def test_escape_md():
    assert _esc("Hello (world)!") == "Hello \\(world\\)\\!"
    assert _esc("S&P 500") == "S&P 500"


def test_format_message():
    report = GlobalReport(
        date="2026-04-16", generated_at=datetime.now(UTC),
        agent_reports=[
            AgentReport(
                agent_key="crypto", agent_label="Crypto", agent_emoji="🚀",
                date="2026-04-16", dashboard_url="https://example.io/crypto/",
                top_gainers=[AgentGainer(identifier="TAO", name="Bittensor",
                                         change_pct=42.3, sector_or_tag="AI")],
            ),
            AgentReport(
                agent_key="sp500", agent_label="S&P 500", agent_emoji="🇺🇸",
                date="2026-04-16", dashboard_url="https://example.io/sp500/",
                top_gainers=[AgentGainer(identifier="NVDA", name="NVIDIA",
                                         change_pct=8.1, sector_or_tag="Technology")],
            ),
        ],
        cross_analysis=CrossMarketAnalysis(
            global_risk_posture="Risk-On",
            capital_flow_direction="broad risk-on rotation",
            cross_market_signals=[
                CrossMarketSignal(signal="AI theme global", markets_involved=["nasdaq", "crypto"]),
            ],
            global_insight="overweight AI infrastructure across markets",
        ),
        narrative=GlobalNarrative(
            macro_regime="expansion", flow_summary="risk-on",
            positioning_advice="lean into growth", week_over_week="stable",
        ),
    )
    msg = _format_message(report, "https://example.io/global/")
    assert "Global Market Brief" in msg
    assert "Risk\\-On" in msg
    assert "Bittensor" in msg
    assert "NVIDIA" in msg
    assert "report.html?date=2026-04-16" in msg.replace("\\", "")
