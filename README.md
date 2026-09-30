# MarketPilot

**Research-driven Indian equity trading-idea & trade-monitoring platform.**

MarketPilot researches Indian equities, computes transparent 100-point opportunity
scores, generates research-based trade ideas with entry/stop/targets and risk-reward,
and lets **you** decide which idea to monitor. It then tracks the equity and surfaces
alerts (T1/T2/Stop-loss/Trailing stop/Regime).

> ⚠️ MarketPilot is **NOT** an automated trading bot. It never places buy/sell orders.
> The Kotak Neo integration is **READ-ONLY** — no order execution exists anywhere.
> You always make the final trading decision.

---

## Run MarketPilot Locally

Runs fully locally from GitHub — **no Emergent dependency** for normal operation.

### Requirements
- Python 3.10+ (3.11 recommended)
- Node.js 18+ and Yarn (`npm i -g yarn`) — or npm
- MongoDB running locally (or a MongoDB Atlas URL)

### Steps

```bash
# 1. Clone
git clone <your-marketpilot-repo-url>
cd marketpilot

# 2. Backend env
cp backend/.env.example backend/.env
python -c "import secrets;print(secrets.token_hex(32))"   # paste into JWT_SECRET in backend/.env

# 3. Frontend env
cp frontend/.env.example frontend/.env                    # set REACT_APP_BACKEND_URL=http://localhost:8001

# 4. Start MongoDB (example)
#    macOS/Linux: mongod --dbpath /data/db
#    Windows:     "C:\Program Files\MongoDB\Server\<ver>\bin\mongod.exe" --dbpath C:\data\db
#    or:          docker run -d -p 27017:27017 --name marketpilot-mongo mongo:7

# 5. Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 6. Frontend (new terminal)
cd frontend
yarn install        # or: npm install
yarn start          # or: npm start   -> http://localhost:3000
```

Open **http://localhost:3000**. Seeded demo login: `demo@marketpilot.in` / (the `DEMO_PASSWORD` you set).

### Run tests
```bash
cd backend && pytest            # engine, broker, providers, API (mocked data; no real orders)
cd frontend && yarn build       # production build
```

### Docker (optional)
A `docker-compose.yml` is provided for MongoDB + backend. It is optional — the plain
local path above is the primary supported flow.
```bash
docker compose up --build
```

---

## Configuration

Copy `backend/.env.example` → `backend/.env` and fill values. **Never commit `.env`.**

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `MONGO_URL` | Yes | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | Yes | Database name | `marketpilot` |
| `JWT_SECRET` | Yes | JWT signing secret (64-char hex) | `openssl rand -hex 32` |
| `JWT_ALGORITHM` | No | JWT algorithm | `HS256` |
| `ENVIRONMENT` | No | App environment label | `development` |
| `MARKET_DATA_PROVIDER` | Yes | `mock` (demo) or `kotak` (live read-only) | `mock` |
| `KOTAK_ENVIRONMENT` | If kotak | Kotak env: `prod` or `uat` | `prod` |
| `KOTAK_CONSUMER_KEY` | If kotak | Kotak Neo consumer key | *(from Kotak app)* |
| `KOTAK_MOBILE` | If kotak | Registered mobile (+91…) | `+91XXXXXXXXXX` |
| `KOTAK_UCC` | If kotak | Unique Client Code | `ABCDE` |
| `KOTAK_MPIN` | If kotak | Trading MPIN | *(secret)* |
| `KOTAK_TOTP_SECRET` | If kotak | TOTP secret for 2FA | *(secret)* |
| `TELEGRAM_BOT_TOKEN` | No | **Server-side only** bot token for alerts | *(secret)* |
| `CORS_ORIGINS` | No | Extra allowed origins (comma-sep) | `http://localhost:3000` |

### Important rules
- **Never commit `.env`** and never share credentials. `.gitignore` excludes all `.env*` except `.env.example`.
- **Kotak Neo is READ-ONLY** — there is no order-placement / trade-execution code.
- The **Telegram bot token is server-side only** (`TELEGRAM_BOT_TOKEN`); it is never sent to,
  stored in, or displayed by the frontend, and is never returned by any API.
- **Telegram notification preferences** (on/off per alert type, chat id) are configured in the
  app: **Settings → Notifications** — no env editing needed for preferences.
- **MOCK mode** needs no Kotak credentials (deterministic demo data).
- **KOTAK mode** needs valid Kotak credentials; without them the app stays healthy and safely
  falls back to demo data (the UI clearly shows **Demo** vs **Live**, never mislabeling mock as live).

---

## Architecture

```
frontend/  React + Tailwind + Recharts (SPA), react-router, sonner
backend/   FastAPI
  ├─ engine/       deterministic technical / fundamental / sentiment / sector / risk / scoring / monitoring
  ├─ providers/    MarketData / Fundamental / News / Sentiment interfaces + Mock & Kotak impls + factory
  ├─ brokers/      BrokerAdapter interface + Kotak Neo READ-ONLY adapter + instruments + websocket + registry
  ├─ routes/       equities, monitoring, alerts/journal, system, notifications
  ├─ telegram.py   server-side Telegram sender
  ├─ market_status.py  Asia/Kolkata PRE_MARKET/OPEN/CLOSED
  ├─ services.py   composes providers+engine into equities / ideas / market overview (+ data-quality)
  └─ auth.py       JWT (httpOnly cookies) + bcrypt + brute-force + password reset
MongoDB    users, monitoring_sessions, alerts, journal_entries, user_settings, reset tokens
```

Numeric analysis is deterministic (Pandas/NumPy). LLMs are never used to decide buy/sell.

## Technology Stack
React · Tailwind · Recharts · FastAPI · Pydantic · Pandas · NumPy · MongoDB · JWT (bcrypt).

## Deployment Readiness
Frontend → any static host (Cloudflare Pages) via `yarn build`. Backend → any Python host
(`backend/Dockerfile`). Database → MongoDB Atlas. Emergent hosting is **not** required.

## Future F&O Roadmap
A separate post-V1 module: option chain, PCR, Max Pain, Greeks, strategy builder. V1 exposes
only an "F&O — Coming Soon" placeholder with no functionality behind it.

---
_Ideas are labelled "Research-based opportunity", never "guaranteed". Do your own due diligence._
