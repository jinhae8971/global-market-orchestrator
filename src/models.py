"""Pydantic models for global orchestrator."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ── Downstream agent report (minimal subset we consume) ──


class AgentGainer(BaseModel):
    """Minimal gainer info from a downstream agent's report."""

    identifier: str  # ticker or coin id
    name: str
    change_pct: float
    sector_or_tag: str = ""


class AgentNarrative(BaseModel):
    current_narrative: str = ""
    hot_sectors: list[str] = Field(default_factory=list)
    cooling_sectors: list[str] = Field(default_factory=list)
    investment_insight: str = ""


class AgentReport(BaseModel):
    """Normalised snapshot of one downstream agent's daily report."""

    agent_key: str       # crypto | kospi | sp500 | nasdaq | dow30
    agent_label: str
    agent_emoji: str
    date: str
    dashboard_url: str
    is_stale: bool = False  # True if report date differs from today
    top_gainers: list[AgentGainer] = Field(default_factory=list)
    narrative: AgentNarrative = Field(default_factory=AgentNarrative)


# ── Orchestrator's own analysis ──


class CrossMarketSignal(BaseModel):
    signal: str
    markets_involved: list[str]


class SectorHeatEntry(BaseModel):
    sector: str
    crypto: str = "n/a"   # hot | warm | neutral | cool | n/a
    kospi: str = "n/a"
    sp500: str = "n/a"
    nasdaq: str = "n/a"
    dow30: str = "n/a"


class CrossMarketAnalysis(BaseModel):
    global_risk_posture: str  # Risk-On | Neutral | Risk-Off
    capital_flow_direction: str
    cross_market_signals: list[CrossMarketSignal] = Field(default_factory=list)
    sector_heatmap: list[SectorHeatEntry] = Field(default_factory=list)
    divergences: list[str] = Field(default_factory=list)
    global_insight: str = ""


class GlobalNarrative(BaseModel):
    macro_regime: str
    flow_summary: str
    theme_convergence: list[str] = Field(default_factory=list)
    theme_divergence: list[str] = Field(default_factory=list)
    positioning_advice: str
    week_over_week: str = ""


class GlobalReport(BaseModel):
    date: str
    generated_at: datetime
    agent_reports: list[AgentReport]
    cross_analysis: CrossMarketAnalysis
    narrative: GlobalNarrative

    @property
    def narrative_tagline(self) -> str:
        return self.cross_analysis.capital_flow_direction[:140]
