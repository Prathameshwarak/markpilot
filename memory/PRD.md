# MarketPilot — Product Requirements & Progress

## Original Problem Statement
Build **MarketPilot**, a brand-new research-driven Indian equity **Trade-Idea + Trade-Monitoring MVP**
(NOT an automated trading bot — the system must never place orders; the user makes the final decision).
F&O is explicitly out of scope for V1 and shown only as "Coming Soon". Scope intentionally small
(~80 credits). Milestone 1 = foundation: project structure, frontend shell, backend shell, DB models,
auth foundation, broker + data-provider abstractions, dashboard UI with (mock) data, Equity/F&O
navigation, health/system-status endpoints, initial tests, README.

## Architecture
- **Frontend:** React + Tailwind + Recharts (SPA), react-router, sonner. Dark "Swiss financial terminal" theme.
- **Backend:** FastAPI + Pydantic; deterministic engine in Pandas/NumPy.
  - `engine/` technical, fundamental, sentiment, sector, risk, scoring, monitoring (all pure & unit-tested)
  - `providers/` MarketData / Fundamental / News / Sentiment interfaces + mock implementations
  - `brokers/` BrokerAdapter interface + Kotak Neo **read-only** adapter (NO place_order)
  - `routes/` equities, monitoring, alerts/journal, system
  - `services.py` composes providers+engine into cached EQUITIES and IDEAS (idea id = `idea-<SYMBOL>`)
  - `auth.py` JWT (httpOnly cookies + bearer fallback), bcrypt, brute-force, password reset
- **DB:** MongoDB — users, monitoring_sessions, alerts, journal_entries, user_settings, reset tokens.
- LLMs never decide buy/sell; all numeric analysis is deterministic.

## User Personas
- **Swing/positional retail trader** researching Indian large-caps who wants transparent, explainable
  ideas and a disciplined manual monitoring + journaling workflow (no auto-execution).

## Core Requirements (static)
- Transparent 100-pt Opportunity Score: Technical 35 / Fundamental 25 / Sentiment 15 / Sector 10 / R:R 15.
- Deterministic indicators: RSI14, EMA20/50, ATR14, volume ratio, momentum, support/resistance.
- ATR-based entry/stop/targets (T1=1R, T2=2R), configurable rules.
- Monitoring state machine: MONITORING/T1_HIT/T2_HIT/STOP_LOSS_HIT/INVALIDATED/CLOSED + ATR trailing.
- Never places orders. Kotak Neo adapter read-only; Telegram config-ready only.

## Implemented (2026-06-30, Milestone 1)
- ✅ Project scaffolding, .env/.env.example, .gitignore, Dockerfile, docker-compose.yml, README.
- ✅ JWT auth (register/login/logout/me/refresh/forgot/reset) + bcrypt + brute-force + admin/demo seeding.
- ✅ DB models & collections; PyObjectId/BaseDocument base.
- ✅ Deterministic engine + transparent scoring + monitoring state machine.
- ✅ Provider abstractions + deterministic mock providers; 12-symbol liquid large-cap universe.
- ✅ BrokerAdapter interface + Kotak Neo read-only stub (order execution disabled).
- ✅ API: market/overview, equities(+detail+research), trade-ideas(+monitor), monitoring(+refresh/close),
     alerts, journal, settings, system/status, health.
- ✅ Frontend: Login/Register/Forgot/Reset, Dashboard, Equity scanner, Equity detail, Trade Ideas,
     My Monitoring, Trade Journal, Market Overview, Settings, F&O Coming Soon.
- ✅ Tests: 40 backend unit tests (engine + API) + 15 e2e tests — all passing. Testing agent: no bugs.

## Implemented (2026-09-30, Milestone 2 — Live data provider + real Kotak Neo adapter)
- ✅ Real READ-ONLY Kotak Neo adapter using current SDK (`neo_api_client` / kotakneoapi v3):
     authenticate (consumer_key → totp_login → totp_validate, TOTP via pyotp, 15s hard timeout),
     health_check, get_quote, get_historical_data, get_instrument, subscribe/unsubscribe. NO
     place_order/modify_order/cancel_order exist or are called. Never logs/returns credentials.
- ✅ MarketDataProvider architecture: MockMarketDataProvider + KotakMarketDataProvider behind a
     factory selected by MARKET_DATA_PROVIDER (mock default; kotak only when fully configured,
     else transparent DEMO fallback — never presents fallback as LIVE).
- ✅ Instrument mapping layer (brokers/instruments.py): internal symbol → exchange/trading_symbol/
     broker_instrument_token, keeping broker specifics out of the engine.
- ✅ Lightweight in-process TTL cache (cache.py) for quotes/historical/instruments.
- ✅ Market-status service (Asia/Kolkata): PRE_MARKET/OPEN/CLOSED, holiday-extensible.
- ✅ Expanded /api/system/status (database, market_data MOCK/KOTAK/ERROR, kotak status, scheduler,
     application, last_market_data_timestamp) + /api/broker/kotak/status + POST /api/broker/kotak/test-connection.
- ✅ Data-quality tagging (DEMO/LIVE/PARTIAL, is_live, data_timestamp, technical_status INSUFFICIENT_DATA).
- ✅ WebSocket infra scaffold (brokers/websocket.py) + MockWebSocketProvider for tests (no alerts yet).
- ✅ Frontend: Settings Kotak connection panel (status/last-connection/last-error/last-data + Test Connection),
     Dashboard & Equity LIVE/DEMO data badges.
- ✅ Config: MARKET_DATA_PROVIDER + documented required KOTAK_* vars in .env.example (placeholders only).
- ✅ Tests: 78 in-process pytest + 8 M2 public + 15 M1 e2e — all passing. Testing agent: no regressions,
     no secret leakage, order placement impossible. NOTE: live Kotak path is implemented against the
     current API but NOT tested end-to-end (no real credentials available); it correctly reports
     NOT_CONFIGURED and the app serves demo data.

## Kotak Neo — required env (current API auth flow)
KOTAK_CONSUMER_KEY, KOTAK_MOBILE, KOTAK_UCC, KOTAK_MPIN, KOTAK_TOTP_SECRET (+ optional KOTAK_ENVIRONMENT).
API_KEY/API_SECRET/CONSUMER_SECRET are NOT required by the current flow.

## Backlog (prioritised)
- **P0 (next milestone):** Replace mock MarketDataProvider with real data (yfinance/NSE) behind existing interface; real fundamentals; scheduled monitoring re-evaluation (cron) instead of manual refresh.
- **P1:** Live Telegram alert delivery; FinBERT SentimentProvider swap; expand equity universe; equity-detail radar chart; watchlist filter.
- **P2:** Kotak Neo live read-only quotes/historical; market-regime-change alerts automation; journal equity curve chart; CSV export.
- **F&O module (post-V1, separate):** option chain, PCR, Max Pain, Greeks, strategy builder.

## Next Tasks (Milestone 3)
1. Provide real Kotak creds in a secure env + set MARKET_DATA_PROVIDER=kotak; verify live auth,
   quotes and historical end-to-end (currently untested without credentials).
2. Resolve real Kotak instrument tokens via scrip_master/search_scrip instead of static seeds.
3. Real fundamentals + news providers behind existing interfaces.
4. Platform cron to re-evaluate monitoring sessions and emit alerts (monitoring engine milestone).
3. Live Telegram sending using stored chat id + bot token.
