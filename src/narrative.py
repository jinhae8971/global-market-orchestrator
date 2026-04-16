"""Global narrative synthesis over recent daily orchestrator reports."""
from __future__ import annotations

import json

from .config import get_settings
from .cross_analyzer import _call_claude, _extract_json
from .logging_setup import get_logger
from .models import CrossMarketAnalysis, GlobalNarrative, GlobalReport

log = get_logger(__name__)


def _summarize_past(report: GlobalReport) -> dict:
    return {
        "date": report.date,
        "risk_posture": report.cross_analysis.global_risk_posture,
        "capital_flow": report.cross_analysis.capital_flow_direction,
        "signals": [s.signal for s in report.cross_analysis.cross_market_signals],
        "divergences": report.cross_analysis.divergences,
        "insight": report.cross_analysis.global_insight,
    }


def synthesize_global_narrative(
    today_analysis: CrossMarketAnalysis,
    prior_reports: list[GlobalReport],
) -> GlobalNarrative:
    settings = get_settings()
    system = (settings.prompts_dir / "global_narrative_system.md").read_text(encoding="utf-8")

    today_ctx = {
        "date": "today",
        "risk_posture": today_analysis.global_risk_posture,
        "capital_flow": today_analysis.capital_flow_direction,
        "signals": [s.signal for s in today_analysis.cross_market_signals],
        "divergences": today_analysis.divergences,
        "insight": today_analysis.global_insight,
    }
    history = [_summarize_past(r) for r in prior_reports]

    user_text = (
        "Here is the recent history of global cross-market reports (most recent "
        "first) followed by today's analysis. Produce the global narrative JSON.\n\n"
        + json.dumps({"today": today_ctx, "history": history}, ensure_ascii=False, indent=2)
    )

    try:
        raw = _call_claude(system, user_text)
        data = _extract_json(raw)
        return GlobalNarrative(
            macro_regime=data.get("macro_regime", ""),
            flow_summary=data.get("flow_summary", ""),
            theme_convergence=list(data.get("theme_convergence") or []),
            theme_divergence=list(data.get("theme_divergence") or []),
            positioning_advice=data.get("positioning_advice", ""),
            week_over_week=data.get("week_over_week", ""),
        )
    except Exception as exc:  # noqa: BLE001
        log.error("global narrative synthesis failed: %s", exc)
        return GlobalNarrative(
            macro_regime="unavailable",
            flow_summary=f"Synthesis error: {exc}",
            positioning_advice="",
            week_over_week="",
        )
