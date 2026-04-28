from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from smart_finance_platform.models import Investment, Transaction, User
from smart_finance_platform.schemas import InvestmentCreate, TransactionCreate, UserCreate
from smart_finance_platform.services.ai import recommendation_engine, risk_score, unusual_activity_alerts
from smart_finance_platform.services.analytics import (
    budget_snapshot,
    monthly_cashflow,
    savings_rate,
    spending_by_category,
)
from smart_finance_platform.services.blockchain import attach_transaction_hash, verify_chain
from smart_finance_platform.services.finance import categorize_expense, portfolio_summary


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        name=payload.name,
        email=str(payload.email).lower(),
        monthly_income=payload.monthly_income,
        risk_preference=payload.risk_preference,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return db.execute(select(User).order_by(User.id.asc())).scalars().all()


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    category = payload.category or categorize_expense(payload.merchant, payload.notes)
    transaction = Transaction(
        user_id=payload.user_id,
        payment_method=payload.payment_method,
        merchant=payload.merchant,
        category=category,
        amount=payload.amount,
        transaction_kind=payload.transaction_kind,
        txn_date=payload.txn_date or datetime.utcnow(),
        notes=payload.notes,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return attach_transaction_hash(db, transaction)


def list_transactions(db: Session, user_id: int | None = None) -> list[Transaction]:
    statement = select(Transaction).order_by(Transaction.txn_date.desc(), Transaction.id.desc())
    if user_id is not None:
        statement = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
        )
    return db.execute(statement).scalars().all()


def create_investment(db: Session, payload: InvestmentCreate) -> Investment:
    investment = Investment(
        user_id=payload.user_id,
        symbol=payload.symbol.upper(),
        asset_type=payload.asset_type,
        quantity=payload.quantity,
        buy_price=payload.buy_price,
        current_price=payload.current_price,
        sector=payload.sector,
        purchase_date=payload.purchase_date or datetime.utcnow(),
    )
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return investment


def list_investments(db: Session, user_id: int | None = None) -> list[Investment]:
    statement = select(Investment).order_by(Investment.purchase_date.desc(), Investment.id.desc())
    if user_id is not None:
        statement = (
            select(Investment)
            .where(Investment.user_id == user_id)
            .order_by(Investment.purchase_date.desc(), Investment.id.desc())
        )
    return db.execute(statement).scalars().all()


def user_dashboard(db: Session, user_id: int) -> dict[str, object] | None:
    user = get_user(db, user_id)
    if user is None:
        return None

    transactions = list_transactions(db, user_id)
    investments = list_investments(db, user_id)
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "monthly_income": user.monthly_income,
            "risk_preference": user.risk_preference,
        },
        "summary": {
            "transaction_count": len(transactions),
            "investment_count": len(investments),
            "savings_rate_percent": savings_rate(user, transactions),
            "risk": risk_score(user, transactions),
            "blockchain": verify_chain(db),
        },
        "spending_by_category": spending_by_category(transactions),
        "monthly_cashflow": monthly_cashflow(transactions),
        "budget": budget_snapshot(user, transactions),
        "portfolio": portfolio_summary(investments),
        "recommendations": recommendation_engine(user, transactions, investments),
        "fraud_alerts": unusual_activity_alerts(transactions),
    }
