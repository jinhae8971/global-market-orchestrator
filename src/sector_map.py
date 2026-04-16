"""Sector normalization across 5 markets into a unified taxonomy."""
from __future__ import annotations

# Unified sector taxonomy for cross-market comparison
UNIFIED_SECTORS = [
    "Semiconductors",
    "AI/Software",
    "Financials",
    "Healthcare/Biotech",
    "Consumer",
    "Industrials",
    "Energy",
    "EV/Battery",
    "Defense",
    "Telecom/Media",
    "Materials",
    "Real Estate",
    "Crypto/DeFi",
    "Crypto/AI",
    "Crypto/L1",
    "Crypto/Meme",
]

# Market-specific tag -> unified sector mapping
_MAP: dict[str, str] = {
    # KOSPI
    "반도체": "Semiconductors",
    "2차전지": "EV/Battery",
    "자동차": "Consumer",
    "조선": "Industrials",
    "바이오": "Healthcare/Biotech",
    "AI/SW": "AI/Software",
    "금융": "Financials",
    "건설": "Industrials",
    "유통": "Consumer",
    "엔터": "Telecom/Media",
    "화학": "Materials",
    "철강": "Materials",
    "방산": "Defense",
    "통신": "Telecom/Media",
    "음식료": "Consumer",
    "에너지": "Energy",
    "게임": "AI/Software",
    "제약": "Healthcare/Biotech",
    # US GICS
    "Technology": "AI/Software",
    "Information Technology": "AI/Software",
    "Healthcare": "Healthcare/Biotech",
    "Financials": "Financials",
    "Consumer Discretionary": "Consumer",
    "Consumer Staples": "Consumer",
    "Communication Services": "Telecom/Media",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Energy",
    # Crypto
    "L1": "Crypto/L1",
    "L2": "Crypto/L1",
    "DeFi": "Crypto/DeFi",
    "DEX": "Crypto/DeFi",
    "LST": "Crypto/DeFi",
    "LRT": "Crypto/DeFi",
    "RWA": "Crypto/DeFi",
    "AI": "Crypto/AI",
    "DePIN": "Crypto/AI",
    "Gaming": "Crypto/DeFi",
    "Meme": "Crypto/Meme",
    "Privacy": "Crypto/L1",
    "Oracle": "Crypto/DeFi",
    "ZK": "Crypto/L1",
    "Interop": "Crypto/L1",
    "Exchange": "Crypto/DeFi",
}


def normalize_sector(raw_tag: str) -> str:
    """Map a market-specific sector tag to the unified taxonomy."""
    return _MAP.get(raw_tag, raw_tag)


def normalize_sectors(tags: list[str]) -> list[str]:
    """Map a list of tags, deduplicate, preserve order."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = normalize_sector(tag)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
