"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentEndpoint(BaseSettings):
    """Dashboard base URL for one downstream agent."""

    model_config = SettingsConfigDict(extra="ignore")

    key: str
    label: str
    emoji: str
    dashboard_url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Secrets ---
    anthropic_api_key: str = Field(default="")
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")

    # --- Agent URLs ---
    crypto_dashboard_url: str = Field(default="")
    kospi_dashboard_url: str = Field(default="")
    sp500_dashboard_url: str = Field(default="")
    nasdaq_dashboard_url: str = Field(default="")
    dow30_dashboard_url: str = Field(default="")

    # --- This orchestrator ---
    dashboard_url: str = Field(default="https://example.github.io/global-market-orchestrator/")

    # --- Tuning ---
    claude_model: str = Field(default="claude-sonnet-4-6")
    narrative_lookback_days: int = Field(default=7)

    # --- Paths ---
    repo_root: Path = Field(default=Path(__file__).resolve().parent.parent)

    @property
    def reports_dir(self) -> Path:
        return self.repo_root / "docs" / "reports"

    @property
    def prompts_dir(self) -> Path:
        return self.repo_root / "prompts"

    def agent_endpoints(self) -> list[AgentEndpoint]:
        return [
            AgentEndpoint(key="crypto", label="Crypto", emoji="🚀",
                          dashboard_url=self.crypto_dashboard_url),
            AgentEndpoint(key="kospi", label="KOSPI", emoji="🇰🇷",
                          dashboard_url=self.kospi_dashboard_url),
            AgentEndpoint(key="sp500", label="S&P 500", emoji="🇺🇸",
                          dashboard_url=self.sp500_dashboard_url),
            AgentEndpoint(key="nasdaq", label="NASDAQ-100", emoji="💻",
                          dashboard_url=self.nasdaq_dashboard_url),
            AgentEndpoint(key="dow30", label="Dow 30", emoji="🏛️",
                          dashboard_url=self.dow30_dashboard_url),
        ]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
