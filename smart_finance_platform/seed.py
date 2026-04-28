from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from smart_finance_platform.models import User
from smart_finance_platform.schemas import InvestmentCreate, TransactionCreate, UserCreate
from smart_finance_platform.services.operations import (
    create_investment,
    create_transaction,
    create_user,
)


def create_demo_data(db: Session) -> User:
    existing = db.execute(select(User).where(User.email == "demo@smartfinance.local")).scalar_one_or_none()
    if existing:
        return existing

    user = create_user(
        db,
        UserCreate(
            name="Demo Investor",
            email="demo@smartfinance.local",
            monthly_income=120000,
            risk_preference="moderate",
        ),
    )

    now = datetime.utcnow()
    transactions = [
        ("UPI", "Monthly Salary", "income", "income", 120000, 27),
        ("UPI", "Apartment Rent", "rent", "expense", 36000, 25),
        ("Wallet", "Zomato Dinner", "food", "expense", 1350, 23),
        ("UPI", "Metro Card Recharge", "transport", "expense", 2200, 22),
        ("Card", "Amazon Electronics", "shopping", "expense", 12999, 20),
        ("UPI", "Electricity Board", "utilities", "expense", 3100, 18),
        ("Wallet", "Netflix Subscription", "entertainment", "expense", 649, 15),
        ("UPI", "Apollo Pharmacy", "health", "expense", 1850, 14),
        ("UPI", "Zerodha SIP", "investment", "investment", 18000, 12),
        ("UPI", "Cafe Coffee", "food", "expense", 430, 8),
        ("Card", "Online Course", "education", "expense", 4500, 6),
        ("Wallet", "Movie Tickets", "entertainment", "expense", 1100, 4),
        ("UPI", "Swiggy Weekend", "food", "expense", 980, 2),
    ]

    for payment_method, merchant, category, kind, amount, days_ago in transactions:
        create_transaction(
            db,
            TransactionCreate(
                user_id=user.id,
                payment_method=payment_method,
                merchant=merchant,
                category=category,
                amount=amount,
                transaction_kind=kind,
                txn_date=now - timedelta(days=days_ago),
            ),
        )

    investments = [
        ("AAPL", "stock", 4, 178.0, 191.5, "Technology"),
        ("MSFT", "stock", 3, 405.0, 430.0, "Technology"),
        ("NIFTYBEES", "etf", 80, 238.0, 251.0, "Index ETF"),
        ("BTC", "crypto", 0.05, 62000.0, 66500.0, "Crypto"),
    ]
    for symbol, asset_type, quantity, buy_price, current_price, sector in investments:
        create_investment(
            db,
            InvestmentCreate(
                user_id=user.id,
                symbol=symbol,
                asset_type=asset_type,
                quantity=quantity,
                buy_price=buy_price,
                current_price=current_price,
                sector=sector,
                purchase_date=now - timedelta(days=45),
            ),
        )

    return user
