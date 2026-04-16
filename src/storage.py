"""Report persistence for global orchestrator."""
from __future__ import annotations

import json
from pathlib import Path

from .config import get_settings
from .logging_setup import get_logger
from .models import GlobalReport

log = get_logger(__name__)


def write_report(report: GlobalReport) -> Path:
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.reports_dir / f"{report.date}.json"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    log.info("wrote global report %s", report_path.name)
    _update_index(report)
    return report_path


def _update_index(report: GlobalReport) -> None:
    settings = get_settings()
    index_path = settings.reports_dir / "index.json"
    index: list[dict] = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(index, list):
                log.warning("index.json is not a list, rebuilding")
                index = []
        except json.JSONDecodeError:
            log.warning("index.json corrupted, rebuilding")

    index = [e for e in index if e.get("date") != report.date]
    entry = {
        "date": report.date,
        "risk_posture": report.cross_analysis.global_risk_posture,
        "narrative_tagline": report.narrative_tagline,
        "agents": [
            {
                "key": ar.agent_key,
                "label": ar.agent_label,
                "emoji": ar.agent_emoji,
                "date": ar.date,
                "is_stale": ar.is_stale,
                "top_gainer": (
                    {"name": ar.top_gainers[0].name,
                     "change_pct": round(ar.top_gainers[0].change_pct, 1)}
                    if ar.top_gainers else None
                ),
            }
            for ar in report.agent_reports
        ],
    }
    index.insert(0, entry)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("updated index.json (%d entries)", len(index))


def load_recent_reports(days: int) -> list[GlobalReport]:
    settings = get_settings()
    if not settings.reports_dir.exists():
        return []
    files = sorted(settings.reports_dir.glob("20*.json"), reverse=True)
    out: list[GlobalReport] = []
    for f in files[:days]:
        try:
            out.append(GlobalReport.model_validate_json(f.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            log.warning("skipping %s: %s", f.name, exc)
    return out
