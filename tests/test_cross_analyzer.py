"""Tests for cross-market JSON extraction."""
from __future__ import annotations

import pytest

from src.cross_analyzer import _extract_json


def test_extract_json_clean():
    raw = '{"global_risk_posture": "Risk-On", "capital_flow_direction": "test"}'
    result = _extract_json(raw)
    assert result["global_risk_posture"] == "Risk-On"


def test_extract_json_with_fences():
    raw = '```json\n{"global_risk_posture": "Neutral"}\n```'
    result = _extract_json(raw)
    assert result["global_risk_posture"] == "Neutral"


def test_extract_json_with_braces_in_strings():
    raw = '{"global_risk_posture": "Risk-On", "capital_flow_direction": "rotation {into} crypto"}'
    result = _extract_json(raw)
    assert "into" in result["capital_flow_direction"]


def test_extract_json_no_json_raises():
    with pytest.raises(ValueError):
        _extract_json("just text, no json")
