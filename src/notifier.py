"""Telegram delivery of unified global market brief."""
from __future__ import annotations

import html

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings
from .logging_setup import get_logger
from .models import GlobalReport

log = get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org"


def _h(text: str) -> str:
    """HTML-escape user content."""
    return html.escape(str(text or ""))


def _format_message(report: GlobalReport, dashboard_url: str) -> str:
    ca = report.cross_analysis
    narr = report.narrative
    risk_emoji = {"Risk-On": "🟢", "Neutral": "🟡", "Risk-Off": "🔴"}.get(
        ca.global_risk_posture, "⚪"
    )

    lines: list[str] = []
    lines.append(f"🌐 <b>글로벌 마켓 브리프</b> ┃ {_h(report.date)}")
    lines.append(f"{risk_emoji} <b>{_h(ca.global_risk_posture)}</b> ┃ {_h(ca.capital_flow_direction)}")
    lines.append("")

    # Cross-market signals (top 3)
    for sig in ca.cross_market_signals[:3]:
        mkts = ", ".join(sig.markets_involved)
        lines.append(f"• {_h(sig.signal)} [{_h(mkts)}]")
    lines.append("")

    # Top mover per market
    for ar in report.agent_reports:
        if ar.top_gainers:
            g = ar.top_gainers[0]
            stale = "⏳" if ar.is_stale else ""
            lines.append(f"{ar.agent_emoji} <b>{_h(g.name)}</b> +{g.change_pct:.1f}%{stale}")
    lines.append("")

    if ca.global_insight:
        lines.append(f"💡 <b>{_h(ca.global_insight)}</b>")
    if narr.positioning_advice:
        lines.append(f"🎯 {_h(narr.positioning_advice)}")
    lines.append("")

    link = dashboard_url.rstrip("/") + f"/report.html?date={report.date}"
    lines.append(f'📊 <a href="{link}">전체 글로벌 보고서</a>')
    return "\n".join(lines)


@retry(stop=stop_after_attempt(4), wait=wait_exponential(min=2, max=16))
def _send(token: str, payload: dict) -> None:
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    with httpx.Client(timeout=20.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()


def send_report(report: GlobalReport) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("telegram credentials missing; skipping notification")
        return

    text = _format_message(report, settings.dashboard_url)
    if len(text) > 4096:
        link_line = text.rsplit("\n", 1)[-1] if "\n" in text else ""
        text = text[: 4096 - len(link_line) - 10] + "\n...\n" + link_line

    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        _send(settings.telegram_bot_token, payload)
    except Exception:
        log.warning("HTML send failed, retrying as plain text")
        payload.pop("parse_mode")
        try:
            _send(settings.telegram_bot_token, payload)
        except Exception as exc:
            log.error("telegram send failed completely: %s", exc)
            return
    log.info("telegram notification sent for %s", report.date)
