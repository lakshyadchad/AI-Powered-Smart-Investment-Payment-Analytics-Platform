from __future__ import annotations

from pathlib import Path

import pandas as pd

from smart_finance_platform.config import settings
from smart_finance_platform.models import Investment, Transaction, User
from smart_finance_platform.services.finance import portfolio_summary


def transactions_to_frame(transactions: list[Transaction]) -> pd.DataFrame:
    rows = [
        {
            "id": txn.id,
            "date": txn.txn_date,
            "merchant": txn.merchant,
            "category": txn.category,
            "payment_method": txn.payment_method,
            "kind": txn.transaction_kind,
            "amount": float(txn.amount),
            "status": txn.status,
            "blockchain_hash": txn.blockchain_hash,
        }
        for txn in transactions
    ]
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["date"] = pd.to_datetime(frame["date"])
    return frame


def investments_to_frame(investments: list[Investment]) -> pd.DataFrame:
    rows = portfolio_summary(investments)["holdings"]
    return pd.DataFrame(rows)


def spending_by_category(transactions: list[Transaction]) -> list[dict[str, object]]:
    frame = transactions_to_frame(transactions)
    if frame.empty:
        return []
    expenses = frame[frame["kind"] == "expense"]
    if expenses.empty:
        return []
    grouped = (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    return grouped.round(2).to_dict(orient="records")


def monthly_cashflow(transactions: list[Transaction]) -> list[dict[str, object]]:
    frame = transactions_to_frame(transactions)
    if frame.empty:
        return []

    frame["month"] = frame["date"].dt.to_period("M").astype(str)
    expenses = (
        frame[frame["kind"] == "expense"].groupby("month")["amount"].sum().rename("expenses")
    )
    income = (
        frame[frame["kind"] == "income"].groupby("month")["amount"].sum().rename("income")
    )
    summary = pd.concat([income, expenses], axis=1).fillna(0).reset_index()
    summary["net_savings"] = summary["income"] - summary["expenses"]
    return summary.round(2).to_dict(orient="records")


def savings_rate(user: User, transactions: list[Transaction]) -> float:
    monthly_income = float(user.monthly_income or 0)
    if monthly_income <= 0:
        return 0.0
    expense_total = sum(
        float(txn.amount)
        for txn in transactions
        if txn.transaction_kind == "expense"
    )
    months = max(1, len({txn.txn_date.strftime("%Y-%m") for txn in transactions}))
    average_monthly_expense = expense_total / months
    return round(((monthly_income - average_monthly_expense) / monthly_income) * 100, 2)


def budget_snapshot(user: User, transactions: list[Transaction]) -> list[dict[str, object]]:
    from smart_finance_platform.services.finance import DEFAULT_BUDGET_SPLIT

    spend = {row["category"]: row["amount"] for row in spending_by_category(transactions)}
    snapshot = []
    for category, split in DEFAULT_BUDGET_SPLIT.items():
        budget = float(user.monthly_income or 0) * split

        used = spend.get(category, 0.0)
        snapshot.append(
            {
                "category": category,
                "budget": round(budget, 2),
                "spent": round(used, 2),
                "remaining": round(budget - used, 2),
                "utilization_percent": round((used / budget) * 100, 2) if budget else 0.0,
            }
        )

    for category, used in sorted(spend.items()):
        if category in DEFAULT_BUDGET_SPLIT:
            continue
        snapshot.append(
            {
                "category": category,
                "budget": 0.0,
                "spent": round(used, 2),
                "remaining": round(-used, 2),
                "utilization_percent": 0.0,
            }
        )
    return snapshot


def export_excel_report(
    user: User,
    transactions: list[Transaction],
    investments: list[Investment],
    output_dir: str | Path | None = None,
) -> Path:
    directory = Path(output_dir or settings.report_dir)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"user_{user.id}_financial_report.xlsx"
    path = directory / filename

    transaction_frame = transactions_to_frame(transactions)
    investment_frame = investments_to_frame(investments)
    category_frame = pd.DataFrame(spending_by_category(transactions))
    cashflow_frame = pd.DataFrame(monthly_cashflow(transactions))
    budget_frame = pd.DataFrame(budget_snapshot(user, transactions))

    summary_frame = pd.DataFrame(
        [
            {"metric": "Monthly income", "value": user.monthly_income},
            {"metric": "Savings rate (%)", "value": savings_rate(user, transactions)},
            {
                "metric": "Portfolio current value",
                "value": portfolio_summary(investments)["current_value"],
            },
            {
                "metric": "Portfolio ROI (%)",
                "value": portfolio_summary(investments)["roi_percent"],
            },
        ]
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_frame.to_excel(writer, sheet_name="Summary", index=False)
        transaction_frame.to_excel(writer, sheet_name="Transactions", index=False)
        investment_frame.to_excel(writer, sheet_name="Investments", index=False)
        category_frame.to_excel(writer, sheet_name="Spending", index=False)
        cashflow_frame.to_excel(writer, sheet_name="Cashflow", index=False)
        budget_frame.to_excel(writer, sheet_name="Budget", index=False)

    return path
