from __future__ import annotations

from datetime import datetime
from typing import Iterable

import numpy as np
import pandas as pd

from smart_finance_platform.config import settings
from smart_finance_platform.models import Investment

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "food": ("restaurant", "cafe", "swiggy", "zomato", "grocery", "food", "coffee"),
    "rent": ("rent", "landlord", "lease", "apartment"),
    "utilities": ("electricity", "water", "gas", "wifi", "internet", "broadband"),
    "transport": ("uber", "ola", "metro", "fuel", "petrol", "diesel", "bus", "taxi"),
    "shopping": ("amazon", "flipkart", "mall", "clothes", "electronics"),
    "health": ("pharmacy", "hospital", "doctor", "clinic", "medicine"),
    "entertainment": ("netflix", "prime", "spotify", "movie", "cinema", "gaming"),
    "education": ("course", "college", "school", "book", "tuition"),
    "investment": ("stock", "mutual fund", "sip", "broker", "zerodha", "groww"),
    "income": ("salary", "bonus", "interest", "dividend", "refund"),
}

DEFAULT_BUDGET_SPLIT = {
    "rent": 0.30,
    "food": 0.12,
    "utilities": 0.08,
    "transport": 0.08,
    "shopping": 0.10,
    "health": 0.06,
    "entertainment": 0.05,
    "education": 0.06,
    "investment": 0.15,
}


def available_categories() -> list[str]:
    return sorted([*CATEGORY_KEYWORDS.keys(), "other"])


def categorize_expense(merchant: str, notes: str | None = None) -> str:
    text = f"{merchant} {notes or ''}".strip().lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "other"


def calculate_roi(buy_price: float, current_price: float) -> float:
    if buy_price <= 0:
        return 0.0
    return ((current_price - buy_price) / buy_price) * 100


def moving_average(values: Iterable[float], window: int = 7) -> list[float]:
    series = pd.Series(list(values), dtype="float")
    if series.empty:
        return []
    return series.rolling(window=min(window, len(series)), min_periods=1).mean().round(2).tolist()


def portfolio_summary(investments: list[Investment]) -> dict[str, object]:
    rows = []
    total_invested = 0.0
    current_value = 0.0

    for item in investments:
        invested = item.quantity * item.buy_price
        value = item.quantity * item.current_price
        total_invested += invested
        current_value += value
        rows.append(
            {
                "symbol": item.symbol.upper(),
                "asset_type": item.asset_type,
                "quantity": item.quantity,
                "buy_price": round(item.buy_price, 2),
                "current_price": round(item.current_price, 2),
                "invested": round(invested, 2),
                "current_value": round(value, 2),
                "roi_percent": round(calculate_roi(item.buy_price, item.current_price), 2),
                "sector": item.sector or "Unclassified",
            }
        )

    portfolio_roi = (
        ((current_value - total_invested) / total_invested) * 100
        if total_invested
        else 0.0
    )
    return {
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "gain_loss": round(current_value - total_invested, 2),
        "roi_percent": round(portfolio_roi, 2),
        "holdings": rows,
    }


def synthetic_price_history(symbol: str, periods: int = 90) -> pd.DataFrame:
    seed = sum(ord(char) for char in symbol.upper())
    rng = np.random.default_rng(seed)
    base = 80 + (seed % 170)
    drift = ((seed % 13) - 5) / 35
    seasonal = np.sin(np.linspace(0, 5 * np.pi, periods)) * (2 + seed % 6)
    noise = rng.normal(0, 1.8, periods)
    prices = np.maximum(5, base + np.cumsum(drift + noise) + seasonal)
    dates = pd.date_range(end=datetime.utcnow().date(), periods=periods, freq="D")
    return pd.DataFrame({"date": dates, "close": prices.round(2)})


def get_stock_history(symbol: str, periods: int = 90) -> pd.DataFrame:
    if settings.enable_live_market_data:
        try:
            import yfinance as yf

            raw = yf.download(
                symbol.upper(),
                period=f"{max(periods, 30)}d",
                progress=False,
                auto_adjust=True,
            )
            if not raw.empty and "Close" in raw:
                frame = raw.reset_index()[["Date", "Close"]]
                frame.columns = ["date", "close"]
                return frame.tail(periods).reset_index(drop=True)
        except Exception:
            pass
    return synthetic_price_history(symbol, periods=periods)


def stock_valuation(symbol: str, prices: pd.DataFrame) -> dict[str, object]:
    close = prices["close"].astype(float)
    current = float(close.iloc[-1]) if not close.empty else 0.0
    ma_7 = moving_average(close, window=7)[-1] if len(close) else 0.0
    ma_30 = moving_average(close, window=30)[-1] if len(close) else 0.0
    trend = "uptrend" if ma_7 > ma_30 else "downtrend" if ma_7 < ma_30 else "sideways"

    pseudo_eps = max(1.0, (sum(ord(char) for char in symbol.upper()) % 18) + 3)
    pe_ratio = current / pseudo_eps if pseudo_eps else 0.0

    return {
        "symbol": symbol.upper(),
        "current_price": round(current, 2),
        "moving_average_7": round(ma_7, 2),
        "moving_average_30": round(ma_30, 2),
        "trend": trend,
        "estimated_pe_ratio": round(pe_ratio, 2),
        "data_source": "Yahoo Finance" if settings.enable_live_market_data else "Synthetic demo data",
    }
