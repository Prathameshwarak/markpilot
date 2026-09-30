# MarketPilot

**Research-driven Indian equity trading-idea & trade-monitoring platform.**

MarketPilot researches Indian equities, computes transparent 100-point opportunity
scores, generates research-based trade ideas with entry/stop/targets and risk-reward,
and lets **you** decide which idea to monitor. It then tracks the equity and raises
alerts (T1/T2/Stop-loss/Trailing stop/Regime changes).

> ⚠️ MarketPilot is **NOT** an automated trading bot. It never places buy/sell orders.
> The user always makes the final trading decision.

---

## Project Overview

- Equity research + technical / fundamental / sentiment / sector analysis
- Transparent scoring: **Technical 35 · Fundamental 25 · Sentiment 15 · Sector 10 · Risk/Reward 15 = 100**
- Trade ideas with entry, stop-loss, two targets, R:R and full reasoning
- Manual "Monitor This Idea" → deterministic monitoring state machine + ATR trailing stop
- Internal alerts + trade journal
- F&O is intentionally **Coming Soon** (no functionality behind it in V1)

## Architecture

```
frontend/  React + Tailwind + Recharts (SPA)
backend/   FastAPI
  ├─ engine/       deterministic technical / fundamental / sentiment / sector / risk / scoring / monitoring
  ├─ providers/    MarketData / Fundamental / News / Sentiment interfaces (+ mock impls)
  ├─ brokers/      BrokerAdapter interface + Kotak Neo read-only adapter (no order execution)
  ├─ routes/       equities, monitoring, alerts/journal, system
  ├─ data/         initial liquid large-cap universe
  ├─ auth.py       JWT auth (register/login/refresh/reset) + brute-force protection
  └─ services.py   composes providers + engine into equities / ideas / market overview
MongoDB    users, monitoring_sessions, alerts, journal_entries, reset tokens…
```

All numeric analysis is **deterministic** (Pandas/NumPy). LLMs are only ever used for
summarization/classification/explanation — never to decide buy/sell.

## Technology Stack

- **Frontend:** React, Tailwind CSS, Recharts, react-router, sonner
- **Backend:** Python, FastAPI, Pydantic, Pandas, NumPy
- **Database:** MongoDB
- **Auth:** JWT (httpOnly cookies) + bcrypt password hashing
- **Notifications:** Telegram (config-ready in V1)
- **Broker:** Kotak Neo adapter (read-only; order execution not implemented)

## Local Setup

### Prerequisites
- Python 3.11+, Node 18+ with Yarn, MongoDB running locally (or Atlas)

### Environment
Copy the example and fill values:
```bash
cp backend/.env.example backend/.env
python -c "import secrets;print(secrets.token_hex(32))"   # → JWT_SECRET
```
Frontend uses `REACT_APP_BACKEND_URL` (see `frontend/.env`).

### Run backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Run frontend
```bash
cd frontend
yarn install
yarn start        # http://localhost:3000
```

### Database
MongoDB via `MONGO_URL` + `DB_NAME`. Indexes and admin/demo users are seeded on startup.

### Run tests
```bash
cd backend
pytest            # engine + API tests (mocked market data, no real orders)
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `MONGO_URL`, `DB_NAME` | MongoDB connection |
| `FRONTEND_URL` | CORS origin + password-reset link |
| `JWT_SECRET` | JWT signing secret |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Seeded owner account |
| `DEMO_EMAIL`, `DEMO_PASSWORD` | Seeded demo account |
| `EMERGENT_EMAIL_KEY`, `EMAIL_FROM_NAME` | Password-reset email |
| `KOTAK_*` | Kotak Neo broker adapter (read-only) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Telegram notifications (config-ready) |

**Never commit** `.env`, API secrets, Kotak credentials, Telegram tokens, JWT secrets or
database credentials. `.gitignore` already excludes them.

## Deployment Readiness

- **Frontend:** Cloudflare Pages (or any static host) — build with `yarn build`
- **Backend:** Render or any Python host — `backend/Dockerfile` provided
- **Database:** MongoDB Atlas free/hobby tier
- **Notifications:** Telegram
- **Broker:** Kotak Neo

Emergent hosting is **not** a mandatory dependency.

## Future F&O Roadmap

A separate F&O module (post-V1): option chain, PCR, Max Pain, Greeks, volatility surface,
and options strategy builder. V1 exposes only an "F&O — Coming Soon" placeholder with no
functionality behind it. Extension points already exist via the provider/broker interfaces.

---

_Ideas are labelled "Research-based opportunity", never "guaranteed". Do your own due diligence._
