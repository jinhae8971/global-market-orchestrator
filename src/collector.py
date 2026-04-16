"""Collect latest reports from each downstream agent's GitHub Pages."""
from __future__ import annotations

from datetime import UTC, datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import AgentEndpoint, get_settings
from .logging_setup import get_logger
from .models import AgentGainer, AgentNarrative, AgentReport

log = get_logger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _fetch_json(url: str) -> dict | list:
    with httpx.Client(timeout=20.0) as client:
        r = client.get(url, follow_redirects=True)
        r.raise_for_status()
        return r.json()


def _normalise_gainer(raw: dict, agent_key: str) -> AgentGainer:
    """Extract a minimal gainer from different agent report schemas."""
    # Crypto uses 'symbol' / 'change_48h_pct'; stocks use 'ticker' / 'change_pct_nd'
    identifier = raw.get("ticker") or raw.get("symbol") or raw.get("id") or "?"
    name = raw.get("name", identifier)
    change = (
        raw.get("change_pct_nd")
        or raw.get("change_48h_pct")
        or raw.get("change_pct")
        or 0.0
    )
    # sector / tag
    sector = raw.get("sector") or raw.get("market") or ""
    return AgentGainer(
        identifier=str(identifier),
        name=str(name),
        change_pct=float(change),
        sector_or_tag=str(sector),
    )


def _normalise_narrative(raw: dict | None) -> AgentNarrative:
    if not raw:
        return AgentNarrative()
    return AgentNarrative(
        current_narrative=raw.get("current_narrative", ""),
        hot_sectors=list(raw.get("hot_sectors") or []),
        cooling_sectors=list(raw.get("cooling_sectors") or []),
        investment_insight=raw.get("investment_insight", ""),
    )


def collect_agent_report(endpoint: AgentEndpoint, today: str) -> AgentReport:
    """Fetch and normalise the latest report from one agent."""
    base = endpoint.dashboard_url.rstrip("/")
    index_url = f"{base}/reports/index.json"

    try:
        index = _fetch_json(index_url)
        if not isinstance(index, list) or not index:
            raise ValueError("empty index")
    except Exception as exc:
        log.warning("[%s] failed to fetch index: %s", endpoint.key, exc)
        return _empty_report(endpoint, today)

    latest_date = index[0].get("date", "")
    report_url = f"{base}/reports/{latest_date}.json"

    try:
        raw = _fetch_json(report_url)
        if not isinstance(raw, dict):
            raise ValueError("non-dict report")
    except Exception as exc:
        log.warning("[%s] failed to fetch report %s: %s", endpoint.key, latest_date, exc)
        return _empty_report(endpoint, today)

    # Normalise gainers
    gainers_raw = raw.get("gainers") or []
    gainers = [_normalise_gainer(g, endpoint.key) for g in gainers_raw[:5]]

    # Normalise analyses for sector tags
    analyses_raw = raw.get("analyses") or []
    tag_map: dict[str, list[str]] = {}
    for a in analyses_raw:
        ident = a.get("ticker") or a.get("coin_id") or a.get("symbol") or ""
        tags = a.get("sector_tags") or a.get("category_tags") or []
        tag_map[str(ident)] = list(tags)
    for g in gainers:
        if not g.sector_or_tag and g.identifier in tag_map and tag_map[g.identifier]:
            g.sector_or_tag = tag_map[g.identifier][0]

    narrative = _normalise_narrative(raw.get("narrative"))
    is_stale = latest_date != today

    log.info(
        "[%s] collected report date=%s (stale=%s, gainers=%d)",
        endpoint.key, latest_date, is_stale, len(gainers),
    )
    return AgentReport(
        agent_key=endpoint.key,
        agent_label=endpoint.label,
        agent_emoji=endpoint.emoji,
        date=latest_date,
        dashboard_url=f"{base}/report.html?date={latest_date}",
        is_stale=is_stale,
        top_gainers=gainers,
        narrative=narrative,
    )


def collect_all(today: str | None = None) -> list[AgentReport]:
    """Collect reports from all configured agent endpoints."""
    if today is None:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
    settings = get_settings()
    reports: list[AgentReport] = []
    for ep in settings.agent_endpoints():
        if not ep.dashboard_url:
            log.warning("[%s] no dashboard_url configured, skipping", ep.key)
            reports.append(_empty_report(ep, today))
            continue
        reports.append(collect_agent_report(ep, today))
    return reports


def _empty_report(endpoint: AgentEndpoint, today: str) -> AgentReport:
    return AgentReport(
        agent_key=endpoint.key,
        agent_label=endpoint.label,
        agent_emoji=endpoint.emoji,
        date=today,
        dashboard_url="",
        is_stale=True,
    )
