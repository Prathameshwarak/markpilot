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

## Backlog (prioritised)
- **P0 (next milestone):** Replace mock MarketDataProvider with real data (yfinance/NSE) behind existing interface; real fundamentals; scheduled monitoring re-evaluation (cron) instead of manual refresh.
- **P1:** Live Telegram alert delivery; FinBERT SentimentProvider swap; expand equity universe; equity-detail radar chart; watchlist filter.
- **P2:** Kotak Neo live read-only quotes/historical; market-regime-change alerts automation; journal equity curve chart; CSV export.
- **F&O module (post-V1, separate):** option chain, PCR, Max Pain, Greeks, strategy builder.

## Next Tasks
1. Wire a real MarketDataProvider (yfinance) + fundamentals; keep engine untouched.
2. Add platform cron to re-evaluate active monitoring sessions and emit alerts automatically.
3. Live Telegram sending using stored chat id + bot token.
