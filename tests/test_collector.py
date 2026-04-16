"""Tests for the downstream agent report collector."""
from __future__ import annotations

from src.collector import _normalise_gainer, _normalise_narrative


def test_normalise_gainer_stock_format():
    raw = {"ticker": "NVDA", "name": "NVIDIA", "change_pct_nd": 8.5, "sector": "Technology"}
    g = _normalise_gainer(raw, "sp500")
    assert g.identifier == "NVDA"
    assert g.change_pct == 8.5
    assert g.sector_or_tag == "Technology"


def test_normalise_gainer_crypto_format():
    raw = {"symbol": "tao", "name": "Bittensor", "change_48h_pct": 42.3, "id": "bittensor"}
    g = _normalise_gainer(raw, "crypto")
    assert g.identifier == "tao"
    assert g.change_pct == 42.3


def test_normalise_gainer_missing_fields():
    g = _normalise_gainer({}, "dow30")
    assert g.identifier == "?"
    assert g.change_pct == 0.0


def test_normalise_narrative_full():
    raw = {"current_narrative": "AI boom", "hot_sectors": ["Tech"],
           "cooling_sectors": ["Energy"], "investment_insight": "overweight AI"}
    n = _normalise_narrative(raw)
    assert n.current_narrative == "AI boom"
    assert n.hot_sectors == ["Tech"]


def test_normalise_narrative_none():
    n = _normalise_narrative(None)
    assert n.current_narrative == ""
    assert n.hot_sectors == []
