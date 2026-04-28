from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from smart_finance_platform.database import get_db
from smart_finance_platform.models import Investment, Transaction
from smart_finance_platform.schemas import (
    InvestmentCreate,
    InvestmentRead,
    StockPredictionRequest,
    TransactionCreate,
    TransactionRead,
    UserCreate,
    UserRead,
)
from smart_finance_platform.seed import create_demo_data
from smart_finance_platform.services.ai import predict_stock_trend, recommendation_engine, risk_score
from smart_finance_platform.services.analytics import export_excel_report
from smart_finance_platform.services.blockchain import verify_chain
from smart_finance_platform.services.finance import get_stock_history, stock_valuation
from smart_finance_platform.services.operations import (
    create_investment,
    create_transaction,
    create_user,
    get_user,
    list_investments,
    list_transactions,
    list_users,
    user_dashboard,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/seed/demo", response_model=UserRead)
def seed_demo(db: Session = Depends(get_db)):
    return create_demo_data(db)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from exc


@router.get("/users", response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    return list_users(db)


@router.get("/users/{user_id}/dashboard")
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    dashboard = user_dashboard(db, user_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dashboard


@router.get("/users/{user_id}/recommendations")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    transactions = list_transactions(db, user_id)
    investments = list_investments(db, user_id)
    return recommendation_engine(user, transactions, investments)


@router.get("/users/{user_id}/risk")
def get_risk_score(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return risk_score(user, list_transactions(db, user_id))


@router.get("/users/{user_id}/report/excel")
def get_excel_report(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    path = export_excel_report(
        user,
        list_transactions(db, user_id),
        list_investments(db, user_id),
    )
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=path.name,
    )


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def add_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    if get_user(db, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return create_transaction(db, payload)


@router.get("/users/{user_id}/transactions", response_model=list[TransactionRead])
def get_transactions(user_id: int, db: Session = Depends(get_db)):
    if get_user(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return list_transactions(db, user_id)


@router.get("/transactions", response_model=list[TransactionRead])
def get_all_transactions(db: Session = Depends(get_db)):
    return list_transactions(db)


@router.post("/investments", response_model=InvestmentRead, status_code=status.HTTP_201_CREATED)
def add_investment(payload: InvestmentCreate, db: Session = Depends(get_db)):
    if get_user(db, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return create_investment(db, payload)


@router.get("/users/{user_id}/investments", response_model=list[InvestmentRead])
def get_investments(user_id: int, db: Session = Depends(get_db)):
    if get_user(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return list_investments(db, user_id)


@router.get("/investments", response_model=list[InvestmentRead])
def get_all_investments(db: Session = Depends(get_db)):
    return list_investments(db)


@router.get("/blockchain/verify")
def verify_blockchain(db: Session = Depends(get_db)):
    return verify_chain(db)


@router.get("/stocks/{symbol}/analysis")
def analyze_stock(symbol: str, days: int = 7):
    history = get_stock_history(symbol)
    return {
        "valuation": stock_valuation(symbol, history),
        "prediction": predict_stock_trend(history, days=days),
        "history": history.tail(30).to_dict(orient="records"),
    }


@router.post("/stocks/predict")
def predict_stock(payload: StockPredictionRequest):
    history = get_stock_history(payload.symbol)
    return {
        "valuation": stock_valuation(payload.symbol, history),
        "prediction": predict_stock_trend(history, days=payload.days),
    }


@router.get("/admin/raw/transactions", response_model=list[TransactionRead], include_in_schema=False)
def raw_transactions(db: Session = Depends(get_db)) -> list[Transaction]:
    return list_transactions(db)


@router.get("/admin/raw/investments", response_model=list[InvestmentRead], include_in_schema=False)
def raw_investments(db: Session = Depends(get_db)) -> list[Investment]:
    return list_investments(db)
