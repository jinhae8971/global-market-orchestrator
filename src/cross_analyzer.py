"""Claude-powered cross-market analysis with prompt caching."""
from __future__ import annotations

import json
import re

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings
from .logging_setup import get_logger
from .models import (
    AgentReport,
    CrossMarketAnalysis,
    CrossMarketSignal,
    SectorHeatEntry,
)

log = get_logger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call_claude(system: str, user_text: str) -> str:
    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_text}],
    )
    parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    log.info(
        "claude usage: input=%s cache_read=%s cache_write=%s output=%s",
        response.usage.input_tokens,
        getattr(response.usage, "cache_read_input_tokens", 0),
        getattr(response.usage, "cache_creation_input_tokens", 0),
        response.usage.output_tokens,
    )
    return "".join(parts)


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL)
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in model response")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON in model response")


def _agent_to_context(ar: AgentReport) -> dict:
    """Serialise one agent report into a compact context dict for Claude."""
    return {
        "market": ar.agent_label,
        "key": ar.agent_key,
        "date": ar.date,
        "is_stale": ar.is_stale,
        "top_gainers": [
            {
                "id": g.identifier,
                "name": g.name,
                "change_pct": round(g.change_pct, 2),
                "sector": g.sector_or_tag,
            }
            for g in ar.top_gainers
        ],
        "narrative": ar.narrative.current_narrative,
        "hot_sectors": ar.narrative.hot_sectors,
        "cooling_sectors": ar.narrative.cooling_sectors,
        "insight": ar.narrative.investment_insight,
    }


def analyze_cross_market(agent_reports: list[AgentReport]) -> CrossMarketAnalysis:
    """Run Claude cross-market analysis on today's collected agent reports."""
    settings = get_settings()
    system = (settings.prompts_dir / "cross_analyzer_system.md").read_text(encoding="utf-8")

    contexts = [_agent_to_context(ar) for ar in agent_reports]
    user_text = (
        "Here are today's reports from all five market agents. "
        "Produce the cross-market analysis JSON per the system prompt.\n\n"
        + json.dumps({"agent_reports": contexts}, ensure_ascii=False, indent=2)
    )

    raw = _call_claude(system, user_text)
    try:
        data = _extract_json(raw)
    except Exception as exc:
        log.error("failed to parse cross-analyzer JSON: %s", exc)
        raise

    signals = [
        CrossMarketSignal(
            signal=s.get("signal", ""),
            markets_involved=list(s.get("markets_involved") or []),
        )
        for s in (data.get("cross_market_signals") or [])
    ]
    heatmap = [
        SectorHeatEntry(**h) for h in (data.get("sector_heatmap") or [])
    ]

    return CrossMarketAnalysis(
        global_risk_posture=data.get("global_risk_posture", "Neutral"),
        capital_flow_direction=data.get("capital_flow_direction", ""),
        cross_market_signals=signals,
        sector_heatmap=heatmap,
        divergences=list(data.get("divergences") or []),
        global_insight=data.get("global_insight", ""),
    )
