from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from smart_finance_platform.models import Transaction

GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class Block:
    index: int
    timestamp: str
    transaction_data: dict[str, object]
    previous_hash: str
    nonce: int = 0
    hash: str = field(default="")

    def compute_hash(self) -> str:
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transaction_data": self.transaction_data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def transaction_payload(transaction: Transaction) -> dict[str, object]:
    return {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "payment_method": transaction.payment_method,
        "merchant": transaction.merchant,
        "category": transaction.category,
        "amount": round(float(transaction.amount), 2),
        "transaction_kind": transaction.transaction_kind,
        "status": transaction.status,
        "txn_date": transaction.txn_date.isoformat(),
    }


def create_block(transaction: Transaction, previous_hash: str) -> Block:
    timestamp = transaction.created_at.isoformat() if transaction.created_at else datetime.utcnow().isoformat()
    block = Block(
        index=transaction.id,
        timestamp=timestamp,
        transaction_data=transaction_payload(transaction),
        previous_hash=previous_hash,
    )
    return Block(
        index=block.index,
        timestamp=block.timestamp,
        transaction_data=block.transaction_data,
        previous_hash=block.previous_hash,
        nonce=block.nonce,
        hash=block.compute_hash(),
    )


def previous_transaction_hash(db: Session, current_transaction_id: int | None = None) -> str:
    statement = select(Transaction).order_by(Transaction.id.desc())
    if current_transaction_id is not None:
        statement = (
            select(Transaction)
            .where(Transaction.id < current_transaction_id)
            .order_by(Transaction.id.desc())
        )
    transaction = db.execute(statement.limit(1)).scalar_one_or_none()
    return transaction.blockchain_hash if transaction and transaction.blockchain_hash else GENESIS_HASH


def attach_transaction_hash(db: Session, transaction: Transaction) -> Transaction:
    previous_hash = previous_transaction_hash(db, transaction.id)
    block = create_block(transaction, previous_hash)
    transaction.blockchain_hash = block.hash
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def verify_chain(db: Session) -> dict[str, object]:
    transactions = db.execute(select(Transaction).order_by(Transaction.id.asc())).scalars().all()
    previous_hash = GENESIS_HASH
    invalid_blocks: list[dict[str, object]] = []

    for transaction in transactions:
        expected_hash = create_block(transaction, previous_hash).hash
        if transaction.blockchain_hash != expected_hash:
            invalid_blocks.append(
                {
                    "transaction_id": transaction.id,
                    "expected_hash": expected_hash,
                    "stored_hash": transaction.blockchain_hash,
                }
            )
        previous_hash = transaction.blockchain_hash or expected_hash

    return {
        "is_valid": not invalid_blocks,
        "block_count": len(transactions),
        "invalid_blocks": invalid_blocks,
    }
