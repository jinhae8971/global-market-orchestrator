"""Telegram delivery of unified global market brief."""
from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings
from .logging_setup import get_logger
from .models import GlobalReport

log = get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org"
MD_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!\\"

def _esc(text: str) -> str:
    return "".join("\\" + c if c in MD_ESCAPE_CHARS else c for c in text or "")


def _format_message(report: GlobalReport, dashboard_url: str) -> str:
    ca = report.cross_analysis
    narr = report.narrative
    risk_emoji = {"Risk-On": "🟢", "Neutral": "🟡", "Risk-Off": "🔴"}.get(
        ca.global_risk_posture, "⚪"
    )
    lines: list[str] = []
    lines.append(f"🌐 *글로벌 마켓 브리프* ┃ {_esc(report.date)}")
    lines.append(f"{risk_emoji} *{_esc(ca.global_risk_posture)}* ┃ {_esc(ca.capital_flow_direction)}")
    lines.append("")

    # Cross-market signals (top 3, compressed)
    for sig in ca.cross_market_signals[:3]:
        mkts = ", ".join(sig.markets_involved)
        lines.append(f"• {_esc(sig.signal)} \\[{_esc(mkts)}\\]")
    lines.append("")

    # Top mover per market — single line each
    for ar in report.agent_reports:
        if ar.top_gainers:
            g = ar.top_gainers[0]
            stale = "⏳" if ar.is_stale else ""
            lines.append(
                f"{ar.agent_emoji} *{_esc(g.name)}* {_esc(f'+{g.change_pct:.1f}%')}{_esc(stale)}"
            )
    lines.append("")

    if ca.global_insight:
        lines.append(f"💡 *{_esc(ca.global_insight)}*")
    if narr.positioning_advice:
        lines.append(f"🎯 {_esc(narr.positioning_advice)}")
    lines.append("")

    link = dashboard_url.rstrip("/") + f"/report.html?date={report.date}"
    lines.append(f"[📊 전체 글로벌 보고서]({_esc(link)})")
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
    MAX_TG_LEN = 4096
    if len(text) > MAX_TG_LEN:
        # Truncate but keep the dashboard link at the end
        link_line = text.rsplit("\n", 1)[-1] if "\n" in text else ""
        text = text[: MAX_TG_LEN - len(link_line) - 20] + "\n\\.\\.\\.\n" + link_line
    _send(settings.telegram_bot_token, {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    })
    log.info("telegram notification sent for %s", report.date)
