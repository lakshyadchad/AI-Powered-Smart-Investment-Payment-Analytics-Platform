from __future__ import annotations

import sys
from datetime import datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from smart_finance_platform.config import settings
from smart_finance_platform.database import SessionLocal, init_db
from smart_finance_platform.schemas import InvestmentCreate, TransactionCreate, UserCreate
from smart_finance_platform.seed import create_demo_data
from smart_finance_platform.services.ai import predict_stock_trend
from smart_finance_platform.services.analytics import (
    export_excel_report,
    investments_to_frame,
    transactions_to_frame,
)
from smart_finance_platform.services.blockchain import verify_chain
from smart_finance_platform.services.finance import (
    available_categories,
    get_stock_history,
    stock_valuation,
)
from smart_finance_platform.services.operations import (
    create_investment,
    create_transaction,
    create_user,
    list_investments,
    list_transactions,
    list_users,
    user_dashboard,
)

st.set_page_config(page_title="Smart Finance Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def cached_stock_analysis(symbol: str, forecast_days: int) -> dict[str, object]:
    history = get_stock_history(symbol)
    return {
        "history": history,
        "valuation": stock_valuation(symbol, history),
        "prediction": predict_stock_trend(history, days=forecast_days),
    }


def as_datetime(date_value) -> datetime:
    return datetime.combine(date_value, time(hour=9))


init_db()
db = SessionLocal()

try:
    users = list_users(db)
    if not users:
        create_demo_data(db)
        users = list_users(db)

    st.title("AI-Powered Smart Investment & Payment Analytics Platform")

    with st.sidebar:
        st.subheader("Profile")
        user_labels = {f"{user.name} ({user.email})": user for user in users}
        selected_label = st.selectbox("Active user", list(user_labels.keys()))
        selected_user = user_labels[selected_label]

        with st.expander("Create user"):
            with st.form("create-user-form", clear_on_submit=True):
                name = st.text_input("Name")
                email = st.text_input("Email")
                monthly_income = st.number_input("Monthly income", min_value=0.0, value=80000.0, step=5000.0)
                risk_preference = st.selectbox(
                    "Risk preference",
                    ["conservative", "moderate", "aggressive"],
                    index=1,
                )
                if st.form_submit_button("Create"):
                    normalized_email = email.strip().lower()
                    existing_emails = {user.email.lower() for user in users}

                    if not name.strip() or not normalized_email:
                        st.error("Enter both name and email.")
                    elif normalized_email in existing_emails:
                        st.error("A user with this email already exists. Select that profile from the dropdown.")
                    else:
                        try:
                            create_user(
                                db,
                                UserCreate(
                                    name=name.strip(),
                                    email=normalized_email,
                                    monthly_income=monthly_income,
                                    risk_preference=risk_preference,
                                ),
                            )
                        except ValidationError as exc:
                            st.error(exc.errors()[0]["msg"])
                        except IntegrityError:
                            db.rollback()
                            st.error("A user with this email already exists. Select that profile from the dropdown.")
                        else:
                            st.success("User created.")
                            st.rerun()

        if st.button("Load demo data"):
            create_demo_data(db)
            st.rerun()

    dashboard = user_dashboard(db, selected_user.id)
    transactions = list_transactions(db, selected_user.id)
    investments = list_investments(db, selected_user.id)

    if dashboard is None:
        st.error("Selected user was not found.")
        st.stop()

    summary = dashboard["summary"]
    risk = summary["risk"]
    portfolio = dashboard["portfolio"]
    blockchain = summary["blockchain"]

    metric_cols = st.columns(5)
    metric_cols[0].metric("Monthly Income", f"{settings.default_currency} {selected_user.monthly_income:,.0f}")
    metric_cols[1].metric("Savings Rate", f"{summary['savings_rate_percent']:.1f}%")
    metric_cols[2].metric("Risk Score", f"{risk['score']} / 900", risk["level"].replace("_", " ").title())
    metric_cols[3].metric("Portfolio ROI", f"{portfolio['roi_percent']:.1f}%")
    metric_cols[4].metric("Blockchain", "Verified" if blockchain["is_valid"] else "Issue Found", f"{blockchain['block_count']} blocks")

    overview_tab, transactions_tab, investments_tab, ai_tab, blockchain_tab, reports_tab = st.tabs(
        ["Overview", "Transactions", "Investments", "AI Insights", "Blockchain", "Reports"]
    )

    with overview_tab:
        left, right = st.columns([1.1, 0.9])
        with left:
            st.subheader("Spending Breakdown")
            category_frame = pd.DataFrame(dashboard["spending_by_category"])
            if category_frame.empty:
                st.info("No expense transactions yet.")
            else:
                st.bar_chart(category_frame.set_index("category")["amount"])

            st.subheader("Monthly Cashflow")
            cashflow_frame = pd.DataFrame(dashboard["monthly_cashflow"])
            if cashflow_frame.empty:
                st.info("No cashflow data yet.")
            else:
                st.line_chart(cashflow_frame.set_index("month")[["income", "expenses", "net_savings"]])

        with right:
            st.subheader("Smart Recommendations")
            for item in dashboard["recommendations"]:
                st.write(f"**{item['title']}**")
                st.caption(f"{item['priority'].title()} priority · {item['type'].replace('_', ' ').title()}")
                st.write(item["detail"])

            st.subheader("Budget Snapshot")
            budget_frame = pd.DataFrame(dashboard["budget"])
            if not budget_frame.empty:
                st.dataframe(
                    budget_frame,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "utilization_percent": st.column_config.ProgressColumn(
                            "Utilization",
                            min_value=0,
                            max_value=150,
                            format="%.0f%%",
                        )
                    },
                )

    with transactions_tab:
        st.subheader("Add Payment Transaction")
        with st.form("transaction-form", clear_on_submit=True):
            cols = st.columns(4)
            merchant = cols[0].text_input("Merchant", placeholder="Swiggy, Amazon, Rent")
            amount = cols[1].number_input("Amount", min_value=1.0, value=1000.0, step=100.0)
            payment_method = cols[2].selectbox("Payment method", ["UPI", "Wallet", "Card", "Bank Transfer"])
            transaction_kind = cols[3].selectbox("Kind", ["expense", "income", "investment"])

            category_choice = st.selectbox("Category", ["auto", *available_categories()])
            txn_date = st.date_input("Transaction date")
            notes = st.text_input("Notes")

            if st.form_submit_button("Add transaction"):
                merchant_name = merchant.strip()
                transaction_notes = notes.strip() or None

                if len(merchant_name) < 2:
                    st.error("Enter a merchant name with at least 2 characters.")
                else:
                    try:
                        create_transaction(
                            db,
                            TransactionCreate(
                                user_id=selected_user.id,
                                payment_method=payment_method,
                                merchant=merchant_name,
                                category=None if category_choice == "auto" else category_choice,
                                amount=amount,
                                transaction_kind=transaction_kind,
                                txn_date=as_datetime(txn_date),
                                notes=transaction_notes,
                            ),
                        )
                    except ValidationError as exc:
                        st.error(exc.errors()[0]["msg"])
                    else:
                        st.success("Transaction added.")
                        st.rerun()

        st.subheader("Transaction Ledger")
        transaction_frame = transactions_to_frame(transactions)
        if transaction_frame.empty:
            st.info("No transactions yet.")
        else:
            display_frame = transaction_frame.copy()
            display_frame["blockchain_hash"] = display_frame["blockchain_hash"].fillna("").str.slice(0, 14)
            st.dataframe(display_frame, hide_index=True, use_container_width=True)

    with investments_tab:
        st.subheader("Add Investment Holding")
        with st.form("investment-form", clear_on_submit=True):
            cols = st.columns(5)
            symbol = cols[0].text_input("Symbol", placeholder="AAPL")
            asset_type = cols[1].selectbox("Asset", ["stock", "mutual_fund", "crypto", "bond", "etf"])
            quantity = cols[2].number_input("Quantity", min_value=0.01, value=1.0, step=1.0)
            buy_price = cols[3].number_input("Buy price", min_value=0.01, value=100.0, step=10.0)
            current_price = cols[4].number_input("Current price", min_value=0.01, value=110.0, step=10.0)
            sector = st.text_input("Sector", placeholder="Technology, Banking, Index ETF")
            purchase_date = st.date_input("Purchase date")
            if st.form_submit_button("Add holding"):
                symbol_value = symbol.strip().upper()
                sector_value = sector.strip() or None

                if not symbol_value:
                    st.error("Enter an investment symbol.")
                else:
                    try:
                        create_investment(
                            db,
                            InvestmentCreate(
                                user_id=selected_user.id,
                                symbol=symbol_value,
                                asset_type=asset_type,
                                quantity=quantity,
                                buy_price=buy_price,
                                current_price=current_price,
                                sector=sector_value,
                                purchase_date=as_datetime(purchase_date),
                            ),
                        )
                    except ValidationError as exc:
                        st.error(exc.errors()[0]["msg"])
                    else:
                        st.success("Investment holding added.")
                        st.rerun()

        cols = st.columns(3)
        cols[0].metric("Invested", f"{settings.default_currency} {portfolio['total_invested']:,.0f}")
        cols[1].metric("Current Value", f"{settings.default_currency} {portfolio['current_value']:,.0f}")
        cols[2].metric("Gain / Loss", f"{settings.default_currency} {portfolio['gain_loss']:,.0f}")

        investment_frame = investments_to_frame(investments)
        if investment_frame.empty:
            st.info("No investments yet.")
        else:
            st.dataframe(investment_frame, hide_index=True, use_container_width=True)

    with ai_tab:
        st.subheader("Stock Trend Prediction")
        cols = st.columns([0.6, 0.4])
        symbol = cols[0].text_input("Market symbol", value="AAPL").upper()
        forecast_days = cols[1].slider("Forecast days", min_value=1, max_value=30, value=7)
        analysis = cached_stock_analysis(symbol, forecast_days)

        valuation = analysis["valuation"]
        prediction = analysis["prediction"]
        cols = st.columns(4)
        cols[0].metric("Current Price", f"{valuation['current_price']:.2f}")
        cols[1].metric("7-Day MA", f"{valuation['moving_average_7']:.2f}")
        cols[2].metric("30-Day MA", f"{valuation['moving_average_30']:.2f}")
        cols[3].metric("Trend", prediction["direction"].title())

        history_frame = analysis["history"].copy()
        history_frame["date"] = pd.to_datetime(history_frame["date"])
        history_chart = (
            history_frame[["date", "close"]]
            .rename(columns={"close": "Historical Close"})
            .set_index("date")
        )

        prediction_frame = pd.DataFrame(prediction["predictions"])
        if prediction_frame.empty:
            st.line_chart(history_chart)
            st.info("No forecast values available.")
        else:
            prediction_frame["date"] = pd.to_datetime(prediction_frame["date"])
            prediction_chart = (
                prediction_frame[["date", "predicted_close"]]
                .rename(columns={"predicted_close": "Predicted Close"})
                .set_index("date")
            )
            st.line_chart(pd.concat([history_chart, prediction_chart], axis=1))
            st.caption(f"Showing {len(prediction_frame)} forecast day(s).")
            st.dataframe(prediction_frame, hide_index=True, use_container_width=True)
        st.caption(prediction["confidence_note"])

        st.subheader("Fraud and Risk Alerts")
        alerts = dashboard["fraud_alerts"]
        if not alerts:
            st.success("No unusual activity detected.")
        else:
            for alert in alerts:
                st.warning(alert["message"])

    with blockchain_tab:
        st.subheader("Tamper-Proof Transaction Chain")
        chain_status = verify_chain(db)
        st.metric("Chain Status", "Valid" if chain_status["is_valid"] else "Invalid")
        st.json(chain_status)

        hash_frame = transactions_to_frame(transactions)
        if not hash_frame.empty:
            hash_frame = hash_frame[["id", "date", "merchant", "amount", "blockchain_hash"]]
            st.dataframe(hash_frame, hide_index=True, use_container_width=True)

    with reports_tab:
        st.subheader("Excel Financial Report")
        report_path = export_excel_report(selected_user, transactions, investments)
        with open(report_path, "rb") as report_file:
            st.download_button(
                "Download Excel report",
                data=report_file,
                file_name=report_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

finally:
    db.close()
