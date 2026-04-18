"""Global narrative synthesis over recent daily orchestrator reports."""
from __future__ import annotations

import json
from collections import Counter

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


def _data_driven_fallback(
    today_analysis: CrossMarketAnalysis,
    has_history: bool,
    exc: Exception,
) -> GlobalNarrative:
    """Generate a minimal data-driven narrative when Claude synthesis fails.

    Pulls from today's cross-market analysis signals and sector heatmap to
    produce a best-effort narrative rather than returning empty strings.
    """
    # Convergence: sector tags appearing 'hot' across multiple markets
    hot_sectors: Counter = Counter()
    cool_sectors: Counter = Counter()
    for entry in today_analysis.sector_heatmap:
        sector = entry.sector if hasattr(entry, "sector") else getattr(entry, "theme", "")
        ratings = entry.ratings if hasattr(entry, "ratings") else {}
        if not sector or not isinstance(ratings, dict):
            continue
        for _, rating in ratings.items():
            if rating == "hot":
                hot_sectors[sector] += 1
            elif rating == "cool":
                cool_sectors[sector] += 1

    convergence = [s for s, count in hot_sectors.most_common(3) if count >= 2]
    divergence = today_analysis.divergences[:3] if today_analysis.divergences else []

    regime = today_analysis.global_risk_posture or "Unknown"
    flow = today_analysis.capital_flow_direction or "자본 흐름 방향 분석 불가"

    return GlobalNarrative(
        macro_regime=f"{regime} (Claude 합성 실패 시 fallback — cross-analysis 직접 사용)",
        flow_summary=(
            f"{flow} | Claude 내러티브 오류: {type(exc).__name__}: {str(exc)[:100]}"
        ),
        theme_convergence=convergence,
        theme_divergence=[str(d) for d in divergence],
        positioning_advice=(
            today_analysis.global_insight
            or "Cross-analysis에서 도출한 포지셔닝 시그널 없음. 다음 실행 시 자동 복구 예상."
        ),
        week_over_week=(
            "이전 히스토리 비교 불가 (첫 실행 또는 히스토리 로딩 실패)"
            if not has_history else ""
        ),
    )


def synthesize_global_narrative(
    today_analysis: CrossMarketAnalysis,
    prior_reports: list[GlobalReport],
) -> GlobalNarrative:
    settings = get_settings()
    prompt_path = settings.prompts_dir / "global_narrative_system.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file missing: {prompt_path}")
    system = prompt_path.read_text(encoding="utf-8")

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
        "IMPORTANT: Your response MUST start with `{` and contain ONLY a valid "
        "JSON object. No preamble, no markdown fences, no explanation. "
        "If history is empty (first run), STILL generate a narrative from today's "
        "cross-analysis alone — do NOT refuse.\n\n"
        + json.dumps({"today": today_ctx, "history": history}, ensure_ascii=False, indent=2)
    )

    raw = ""
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
        if raw:
            log.error(
                "global narrative synthesis failed: %s | raw response (first 500 chars): %r",
                exc, raw[:500],
            )
        else:
            log.error("global narrative synthesis failed before response: %s", exc)
        return _data_driven_fallback(today_analysis, bool(prior_reports), exc)
