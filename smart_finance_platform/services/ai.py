from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from smart_finance_platform.models import Investment, Transaction, User
from smart_finance_platform.services.analytics import savings_rate, spending_by_category
from smart_finance_platform.services.finance import portfolio_summary


def predict_stock_trend(price_history: pd.DataFrame, days: int = 7) -> dict[str, object]:
    if price_history.empty or "close" not in price_history:
        return {
            "direction": "unknown",
            "slope": 0.0,
            "predictions": [],
            "confidence_note": "Not enough price history for a prediction.",
        }

    close = price_history["close"].astype(float).to_numpy()
    x = np.arange(len(close)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(x, close)

    future_x = np.arange(len(close), len(close) + days).reshape(-1, 1)
    forecast = model.predict(future_x)
    slope = float(model.coef_[0])
    direction = "uptrend" if slope > 0.05 else "downtrend" if slope < -0.05 else "sideways"
    start_date = pd.to_datetime(price_history["date"].iloc[-1]).date()

    predictions = [
        {
            "date": (start_date + timedelta(days=index + 1)).isoformat(),
            "predicted_close": round(float(value), 2),
        }
        for index, value in enumerate(forecast)
    ]

    return {
        "direction": direction,
        "slope": round(slope, 4),
        "predictions": predictions,
        "confidence_note": "Linear regression demo model; validate with broader market research before investing.",
    }


def risk_score(user: User, transactions: list[Transaction]) -> dict[str, object]:
    monthly_income = float(user.monthly_income or 0)
    now = datetime.utcnow()
    recent_expenses = [
        float(txn.amount)
        for txn in transactions
        if txn.transaction_kind == "expense" and txn.txn_date >= now - timedelta(days=30)
    ]

    total_recent_spend = sum(recent_expenses)
    spend_ratio = total_recent_spend / monthly_income if monthly_income else 1.0
    volatility = float(np.std(recent_expenses)) if len(recent_expenses) > 1 else 0.0
    volatility_ratio = volatility / monthly_income if monthly_income else 0.0

    score = 780
    score -= max(0.0, spend_ratio - 0.55) * 360
    score -= volatility_ratio * 150
    score += min(60, max(0.0, 0.35 - spend_ratio) * 180)
    score = int(max(300, min(900, round(score))))

    if score >= 760:
        level = "excellent"
    elif score >= 680:
        level = "healthy"
    elif score >= 580:
        level = "watchlist"
    else:
        level = "high_risk"

    return {
        "score": score,
        "level": level,
        "monthly_spend": round(total_recent_spend, 2),
        "spend_to_income_ratio": round(spend_ratio, 2),
        "savings_rate_percent": savings_rate(user, transactions),
    }


def unusual_activity_alerts(transactions: list[Transaction]) -> list[dict[str, object]]:
    expenses = [txn for txn in transactions if txn.transaction_kind == "expense"]
    if not expenses:
        return []

    amounts = np.array([float(txn.amount) for txn in expenses], dtype=float)
    mean = float(amounts.mean())
    std = float(amounts.std())
    threshold = max(mean + 2 * std, mean * 2.5)
    alerts: list[dict[str, object]] = []

    seen_same_day: set[tuple[str, str, float]] = set()
    for txn in expenses:
        fingerprint = (txn.txn_date.date().isoformat(), txn.merchant.lower(), round(txn.amount, 2))
        if float(txn.amount) > threshold and len(expenses) >= 4:
            alerts.append(
                {
                    "transaction_id": txn.id,
                    "severity": "high",
                    "message": f"Unusually high payment at {txn.merchant}: {txn.amount:.2f}",
                }
            )
        if fingerprint in seen_same_day:
            alerts.append(
                {
                    "transaction_id": txn.id,
                    "severity": "medium",
                    "message": f"Duplicate-looking transaction at {txn.merchant} on {txn.txn_date.date()}",
                }
            )
        seen_same_day.add(fingerprint)

    return alerts


def recommendation_engine(
    user: User,
    transactions: list[Transaction],
    investments: list[Investment],
) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    user_risk = risk_score(user, transactions)
    portfolio = portfolio_summary(investments)
    categories = spending_by_category(transactions)
    savings = float(user_risk["savings_rate_percent"])

    if savings < 15:
        recommendations.append(
            {
                "type": "expense_optimization",
                "priority": "high",
                "title": "Raise your monthly savings rate",
                "detail": "Your savings rate is below 15%. Reduce discretionary spends before increasing market exposure.",
            }
        )
    else:
        recommendations.append(
            {
                "type": "investment",
                "priority": "medium",
                "title": "Automate a monthly investment plan",
                "detail": "Your cashflow can support a disciplined SIP or ETF allocation aligned with your risk preference.",
            }
        )

    if categories:
        top = categories[0]
        recommendations.append(
            {
                "type": "budgeting",
                "priority": "medium",
                "title": f"Review {top['category']} spending",
                "detail": f"{top['category'].title()} is your largest expense bucket at {top['amount']:.2f}.",
            }
        )

    if user.risk_preference == "conservative":
        allocation = "favor diversified index funds, liquid funds, and short-duration debt exposure"
    elif user.risk_preference == "aggressive":
        allocation = "consider a higher equity allocation with strict position sizing and emergency reserves"
    else:
        allocation = "balance broad-market equity funds with stable fixed-income instruments"

    recommendations.append(
        {
            "type": "portfolio_strategy",
            "priority": "medium",
            "title": "Risk-aligned allocation",
            "detail": f"For a {user.risk_preference} profile, {allocation}.",
        }
    )

    if portfolio["total_invested"] == 0:
        recommendations.append(
            {
                "type": "investment",
                "priority": "high",
                "title": "Start with diversified exposure",
                "detail": "No holdings are recorded yet. Begin with low-cost diversified funds before concentrated stock bets.",
            }
        )
    elif float(portfolio["roi_percent"]) < -8:
        recommendations.append(
            {
                "type": "risk_management",
                "priority": "high",
                "title": "Review underperforming holdings",
                "detail": "Your tracked portfolio is down more than 8%. Check whether losses are thesis-driven or market-wide.",
            }
        )

    for alert in unusual_activity_alerts(transactions)[:3]:
        recommendations.append(
            {
                "type": "fraud_alert",
                "priority": alert["severity"],
                "title": "Unusual transaction detected",
                "detail": alert["message"],
            }
        )

    return recommendations
