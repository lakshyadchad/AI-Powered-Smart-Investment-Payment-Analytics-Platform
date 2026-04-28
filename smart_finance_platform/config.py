from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv(
        "APP_NAME", "AI-Powered Smart Investment & Payment Analytics Platform"
    )
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smart_finance.db")
    default_currency: str = os.getenv("DEFAULT_CURRENCY", "INR")
    enable_live_market_data: bool = (
        os.getenv("ENABLE_LIVE_MARKET_DATA", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    report_dir: str = os.getenv("REPORT_DIR", "reports")


settings = Settings()
