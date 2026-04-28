from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    monthly_income: float = Field(..., ge=0)
    risk_preference: str = Field("moderate", pattern="^(conservative|moderate|aggressive)$")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    monthly_income: float
    risk_preference: str
    created_at: datetime


class TransactionCreate(BaseModel):
    user_id: int
    payment_method: str = Field("UPI", pattern="^(UPI|Wallet|Card|Bank Transfer)$")
    merchant: str = Field(..., min_length=2, max_length=140)
    category: str | None = None
    amount: float = Field(..., gt=0)
    transaction_kind: str = Field("expense", pattern="^(expense|income|investment)$")
    txn_date: datetime | None = None
    notes: str | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    payment_method: str
    merchant: str
    category: str
    amount: float
    transaction_kind: str
    status: str
    txn_date: datetime
    blockchain_hash: str | None
    notes: str | None


class InvestmentCreate(BaseModel):
    user_id: int
    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: str = Field("stock", pattern="^(stock|mutual_fund|crypto|bond|etf)$")
    quantity: float = Field(..., gt=0)
    buy_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    sector: str | None = None
    purchase_date: datetime | None = None


class InvestmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    symbol: str
    asset_type: str
    quantity: float
    buy_price: float
    current_price: float
    sector: str | None
    purchase_date: datetime

class StockPredictionRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    days: int = Field(7, ge=1, le=60)
