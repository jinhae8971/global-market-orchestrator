"""Daily pipeline entry point.

Flow:
  1. Collect latest reports from all 5 agent dashboards
  2. Run cross-market analysis with Claude
  3. Load prior global reports → synthesize weekly narrative
  4. Write global report + update dashboard index
  5. Send unified Telegram notification
"""
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from .collector import collect_all
from .config import get_settings
from .cross_analyzer import analyze_cross_market
from .logging_setup import get_logger
from .models import (
    CrossMarketAnalysis,
    GlobalNarrative,
    GlobalReport,
)
from .narrative import synthesize_global_narrative
from .notifier import send_report
from .storage import load_recent_reports, write_report

log = get_logger(__name__)


def run(dry_run: bool = False, skip_telegram: bool = False) -> GlobalReport:
    settings = get_settings()
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log.info("=== global-market-orchestrator run (dry_run=%s) ===", dry_run)

    if not dry_run and not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for full runs (use --dry-run to skip)")

    # 1. Collect
    agent_reports = collect_all(today)
    active = [ar for ar in agent_reports if ar.top_gainers]
    log.info("collected %d agent reports (%d with data)", len(agent_reports), len(active))

    if dry_run:
        for ar in agent_reports:
            status = "stale" if ar.is_stale else "fresh"
            top = ar.top_gainers[0].name if ar.top_gainers else "n/a"
            log.info("DRY [%s] %s top=%s (%s)", ar.agent_key, ar.date, top, status)
        return GlobalReport(
            date=today,
            generated_at=datetime.now(UTC),
            agent_reports=agent_reports,
            cross_analysis=CrossMarketAnalysis(
                global_risk_posture="(dry-run)",
                capital_flow_direction="(dry-run)",
            ),
            narrative=GlobalNarrative(
                macro_regime="(dry-run)",
                flow_summary="(dry-run)",
                positioning_advice="",
                week_over_week="",
            ),
        )

    # 2. Cross-market analysis
    cross = analyze_cross_market(agent_reports)

    # 3. Global narrative
    prior_reports = load_recent_reports(days=settings.narrative_lookback_days)
    narrative = synthesize_global_narrative(cross, prior_reports)

    # 4. Write
    report = GlobalReport(
        date=today,
        generated_at=datetime.now(UTC),
        agent_reports=agent_reports,
        cross_analysis=cross,
        narrative=narrative,
    )
    write_report(report)

    # 5. Notify
    if not skip_telegram:
        try:
            send_report(report)
        except Exception as exc:  # noqa: BLE001
            log.error("telegram send failed: %s", exc)

    log.info("=== run complete: %s ===", report.date)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Global Market Orchestrator daily run")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-telegram", action="store_true")
    args = parser.parse_args()
    try:
        run(dry_run=args.dry_run, skip_telegram=args.skip_telegram)
    except Exception as exc:  # noqa: BLE001
        log.exception("pipeline failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
