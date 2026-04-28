from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from smart_finance_platform.database import SessionLocal, init_db
from smart_finance_platform.seed import create_demo_data
from smart_finance_platform.services.ai import predict_stock_trend
from smart_finance_platform.services.analytics import export_excel_report
from smart_finance_platform.services.blockchain import verify_chain
from smart_finance_platform.services.finance import get_stock_history, stock_valuation
from smart_finance_platform.services.operations import (
    list_investments,
    list_transactions,
    user_dashboard,
)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        user = create_demo_data(db)
        dashboard = user_dashboard(db, user.id)
        transactions = list_transactions(db, user.id)
        investments = list_investments(db, user.id)
        chain = verify_chain(db)
        history = get_stock_history("AAPL")
        valuation = stock_valuation("AAPL", history)
        prediction = predict_stock_trend(history, days=7)
        report_path = export_excel_report(user, transactions, investments)

        print("Smoke check passed")
        print(f"User: {user.email}")
        print(f"Risk score: {dashboard['summary']['risk']['score']}")
        print(f"Blockchain valid: {chain['is_valid']}")
        print(f"AAPL trend: {prediction['direction']} at {valuation['current_price']}")
        print(f"Excel report: {report_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
