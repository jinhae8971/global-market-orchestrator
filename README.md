# Global Market Orchestrator

The **6th and final piece** of the multi-market research system. This orchestrator **does not collect raw data** — it consumes the daily reports from five independent research agents and produces a unified **cross-market intelligence brief**.

```
Crypto + KOSPI + S&P 500 + NASDAQ-100 + Dow 30
                    │
            ┌───────▼────────┐
            │  Orchestrator  │
            └───────┬────────┘
                    │
    Cross-Market Analysis + Global Narrative
    Unified Dashboard + Telegram Brief
```

## What it does (daily at 23:30 UTC)

1. **Collects** the latest report JSON from each agent's GitHub Pages endpoint
2. **Normalises** different schemas (crypto vs stock) into a common format
3. Runs **Claude cross-market analysis** — risk posture, capital flows, sector heatmap, divergences
4. Synthesizes a **7-day global narrative** — macro regime, theme convergence/divergence, positioning
5. Writes a unified report to `docs/reports/` and deploys a **GitHub Pages dashboard**
6. Sends one **Telegram message** covering all five markets

## Key features

| Feature | Detail |
|---|---|
| **Risk posture** | Risk-On / Neutral / Risk-Off based on what's rallying across markets |
| **Cross-market signals** | Links between markets (NVDA +8% in NASDAQ + TAO +42% in Crypto → AI global) |
| **Sector heatmap** | Grid: sector vs market, rated hot/warm/neutral/cool |
| **Divergences** | Where one market tells a different story (Korea biotech up, US healthcare flat) |
| **Stale handling** | Weekend runs: Crypto is fresh, stocks are marked ⏳ stale but still used |
| **Unified dashboard** | All 5 markets on one page with deep-links to individual agent dashboards |

## Architecture

The orchestrator is **completely decoupled** from the agents:
- Agents run at **22:00 UTC**, commit reports, deploy Pages
- Orchestrator runs at **23:30 UTC** (90 min later), fetches Pages, produces its own report
- If an agent is down, the orchestrator gracefully marks it as unavailable

## Setup

### 1. Prerequisites

All 5 agent repos must be deployed with GitHub Pages active:
- `crypto-research-agent`
- `kospi-research-agent`
- `sp500-research-agent`
- `nasdaq-research-agent`
- `dow30-research-agent`

### 2. Create repo + migrate

```bash
cd global-market-orchestrator
git init -b main
git add .
git commit -m "Initial import: global market orchestrator"
git remote add origin https://github.com/<user>/global-market-orchestrator.git
git push -u origin main
```

### 3. Enable GitHub Pages

Settings → Pages → Source: **GitHub Actions**

### 4. Secrets & Variables

| Scope | Name | Value |
|---|---|---|
| Secret | `ANTHROPIC_API_KEY` | `sk-ant-…` |
| Secret | `TELEGRAM_BOT_TOKEN` | bot token |
| Secret | `TELEGRAM_CHAT_ID` | chat id |
| Variable | `CRYPTO_DASHBOARD_URL` | `https://<user>.github.io/crypto-research-agent` |
| Variable | `KOSPI_DASHBOARD_URL` | `https://<user>.github.io/kospi-research-agent` |
| Variable | `SP500_DASHBOARD_URL` | `https://<user>.github.io/sp500-research-agent` |
| Variable | `NASDAQ_DASHBOARD_URL` | `https://<user>.github.io/nasdaq-research-agent` |
| Variable | `DOW30_DASHBOARD_URL` | `https://<user>.github.io/dow30-research-agent` |
| Variable | `DASHBOARD_URL` | `https://<user>.github.io/global-market-orchestrator/` |

### 5. First run

Actions → **Daily Global Orchestrator** → **Run workflow**

## Running locally

```bash
pip install -e ".[dev]"
cp .env.example .env   # fill all URLs + secrets

python -m src.main --dry-run        # collect only, no Claude/telegram
python -m src.main --skip-telegram   # full run, no telegram
python -m src.main                   # full run

python -m pytest
python -m ruff check src tests
```

## Timing

```
22:00 UTC  5 agents run in parallel (each independent)
23:30 UTC  Orchestrator collects → analyzes → publishes
           Cron: 30 23 * * * (every day, including weekends)
```

On weekends, stock agents have no new data. The orchestrator marks them `is_stale: true` and produces a Crypto-focused brief with stale stock context.

## Cost

| Component | Cost/day |
|---|---|
| 5 agents combined | ~$0.15–0.40 |
| Orchestrator (2 Claude calls) | ~$0.05–0.10 |
| **Total system** | **~$0.20–0.50/day ≈ $6–15/month** |

## Tuning

| Variable | Default | Description |
|---|---|---|
| `NARRATIVE_LOOKBACK_DAYS` | `7` | Days of history for narrative |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Model for analysis |
