# AI-Powered Smart Investment & Payment Analytics Platform

This project is a working financial analytics platform that combines payments, investments, AI insights, SQL storage, Excel reporting, and blockchain-style transaction verification in one Python application.

It is designed as a practical prototype for a smarter personal finance system: users can simulate UPI or wallet payments, track investments, analyze spending behavior, predict stock trends, receive personalized recommendations, detect unusual activity, and verify that transaction records have not been tampered with.

## Greater Purpose

Most people manage money through many disconnected apps: one for UPI payments, one for wallet transactions, one for stocks, one for reports, and another for budgeting. Because the data is fragmented, users often do not understand where their money goes, whether their spending is healthy, or how their investment behavior matches their income and risk profile.

The greater purpose of this platform is to bring financial awareness, intelligent decision support, and trust into one system. Instead of only recording transactions, the platform explains them, scores risk, suggests improvements, and protects transaction integrity through a blockchain-style hash chain.

In a real-world version, this idea could help users:

- Understand spending patterns before they become financial problems
- Improve savings and investment discipline
- Detect unusual or suspicious financial activity
- Compare income, expenses, risk, and portfolio performance in one place
- Build trust in transaction history through tamper detection

## What Makes It Different

Traditional finance tracker:

- Stores expenses and shows basic charts
- Requires users to manually interpret their own behavior
- Usually separates payments, investments, and reports
- Does not verify whether historical transaction records changed

This platform:

- Combines payment simulation, investment tracking, AI, analytics, and reports
- Uses Linear Regression to predict simple stock trends
- Calculates a risk score based on spending vs income
- Generates personalized investment and expense optimization recommendations
- Detects unusual transactions and duplicate-looking activity
- Stores transaction hashes in a blockchain-style chain for integrity verification
- Exports user financial summaries to Excel
- Supports SQLite by default and MySQL for a production-style setup

The key difference is that this is not only a tracker. It is an intelligent financial decision-support system.

## What It Creates

When you run the project, it creates:

- A local SQL database: `smart_finance.db`
- Database tables:
  - `users`
  - `transactions`
  - `investments`
- Demo user data when the seed function is used
- Simulated UPI, wallet, card, and bank-transfer transactions
- Blockchain hashes for every stored transaction
- Dashboard charts for spending, cashflow, budget usage, and portfolio returns
- AI-generated risk scores and recommendations
- Stock trend forecasts using Linear Regression
- Fraud or unusual-activity alerts
- Excel reports inside the `reports/` folder

Generated files are ignored by Git where appropriate, including the SQLite database, virtual environment, temp files, and Excel reports.

## How To Use It

You can use the project in three ways:

1. Streamlit dashboard for interactive usage
2. FastAPI backend for API testing and integration
3. Smoke-check script for quick verification

### 1. Use The Streamlit Dashboard

Start the dashboard:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

In the dashboard you can:

- Select or create a user profile
- Add UPI, wallet, card, or bank-transfer transactions
- Categorize expenses automatically or manually
- Add stock, ETF, mutual fund, bond, or crypto holdings
- View spending breakdown charts
- View monthly income, expenses, and savings
- Check AI-generated risk score
- View smart recommendations
- Run stock trend predictions
- Check fraud and unusual-activity alerts
- Verify blockchain transaction integrity
- Download an Excel financial report

### 2. Use The FastAPI Backend

Start the API server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn smart_finance_platform.main:app --reload --host 127.0.0.1 --port 8000
```

Open the interactive API docs:

```text
http://127.0.0.1:8000/docs
```

Useful endpoints:

- `GET /health`
- `POST /seed/demo`
- `GET /users`
- `POST /users`
- `POST /transactions`
- `GET /users/{user_id}/transactions`
- `POST /investments`
- `GET /users/{user_id}/investments`
- `GET /users/{user_id}/dashboard`
- `GET /users/{user_id}/recommendations`
- `GET /users/{user_id}/risk`
- `GET /blockchain/verify`
- `GET /stocks/AAPL/analysis`
- `GET /users/{user_id}/report/excel`

### 3. Run A Smoke Check

Run:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_check.py
```

This checks the full workflow:

- Initializes the database
- Creates demo data
- Builds the dashboard summary
- Verifies the blockchain chain
- Runs stock valuation and prediction
- Exports an Excel report

Expected output includes:

```text
Smoke check passed
Blockchain valid: True
Excel report: reports\user_1_financial_report.xlsx
```

## Complete Workflow

The platform follows this flow:

1. User creates or selects a profile.
2. User adds payment transactions such as UPI, wallet, card, or bank transfer.
3. Each transaction is stored in SQL.
4. Each transaction receives a blockchain-style hash.
5. Analytics services process spending, income, budget usage, and savings.
6. AI services calculate risk, detect unusual activity, and generate recommendations.
7. Investment services calculate ROI, moving averages, and trend direction.
8. Dashboard and API display insights, predictions, charts, and reports.
9. Excel export creates a shareable financial summary.

## Main Features

- Personalized financial dashboard
- UPI and wallet transaction simulation
- Expense categorization
- Budget tracking
- Savings rate calculation
- Investment portfolio tracking
- ROI and moving average analysis
- Linear Regression stock prediction
- Risk scoring similar to a financial health score
- Recommendation engine for saving, investing, and spending control
- Fraud and unusual transaction alerts
- Blockchain-style transaction verification
- Excel report generation
- SQLite and MySQL support

## Project Structure

```text
smart_finance_platform/
  api/routes.py              FastAPI route definitions
  main.py                    FastAPI app entrypoint
  models.py                  SQLAlchemy database tables
  schemas.py                 Pydantic request/response schemas
  seed.py                    Demo data generator
  services/
    ai.py                    Prediction, risk scoring, recommendations, fraud alerts
    analytics.py             Pandas summaries and Excel reports
    blockchain.py            Transaction hash-chain verification
    finance.py               Categorization, ROI, stock analysis
    operations.py            CRUD and dashboard orchestration
dashboard/streamlit_app.py   Streamlit interface
scripts/smoke_check.py       End-to-end local verification
```

## Technology Stack

- Backend: FastAPI
- Frontend: Streamlit
- Database: SQLite by default, MySQL supported
- ORM: SQLAlchemy
- AI and ML: Scikit-learn Linear Regression
- Analytics: Pandas and NumPy
- Reports: OpenPyXL and Pandas Excel export
- Market Data: Synthetic data by default, optional Yahoo Finance
- Blockchain: Custom Python hash-chain simulation

## Setup

The dependencies have been installed into `.venv` in this workspace. To recreate the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PowerShell script activation may be disabled on this machine, so the commands above call the venv Python directly.

## MySQL Configuration

SQLite is used by default:

```text
DATABASE_URL=sqlite:///./smart_finance.db
```

For MySQL, create a database:

```sql
CREATE DATABASE smart_finance;
```

Then set this in `.env`:

```text
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/smart_finance
```

You can copy `.env.example` to `.env` and update the values.

## Live Market Data

By default, stock history uses deterministic synthetic demo data. This keeps the project usable offline and stable for presentations.

To enable Yahoo Finance data:

```text
ENABLE_LIVE_MARKET_DATA=true
```

The code automatically falls back to synthetic prices if live data is unavailable.

## Educational Notes

This is a prototype and educational project. The investment recommendations are demo logic, not financial advice. The blockchain module is a simulated hash chain for integrity verification, not a distributed blockchain network.

## Future Enhancements

- Real authentication and user sessions
- Bank or UPI API integration
- More advanced stock forecasting models
- Portfolio optimization
- Credit-style scoring history
- Real fraud detection model trained on transaction patterns
- Notifications for budget limits and suspicious payments
- Deployment with Docker and cloud database support
