# Technical Specification for Trading Bot

## General

- Language: **Python**
- Framework: **Backtrader** ([repository](https://github.com/mementum/backtrader))
- Architecture: **Docker + FastAPI + SPA Web Interface**
- Configuration: ``** file**
- Modes of operation:
  - **View-only** (without keys) — signals + backtest.
  - **Trading** (with keys) — order execution based on signals.

## Web Interface

At least 2 tabs:

### 1. Dashboard

- Add / remove trading pairs.
- Display signals for each pair (live/last N events).
- If keys are provided — enable trading.
- Checkbox: **“Confirm order execution”**
  - If disabled — orders are executed automatically.
  - If enabled — a modal window with confirmation (details: pair, volume, order type, SL/TP) is shown.
  - Unconfirmed signals are stored in the *pending confirmation* list.

### 2. Backtest

- Select pair, strategy, timeframes, data range (1–30 days).
- Start backtest → results stored locally. 
- Table of previous results (strategy, timeframe, parameters).
- Button **“Detailed statistics”** next to each test opens a modal window; metrics (win-rate, entries/exits, TP/SL, number of trades) are displayed only after clicking. Nearby buttons **“Delete result”** or **“Delete all”** are available.

## API (FastAPI)

- `/pairs` — CRUD operations with pairs.
- `/signals` — list / stream of signals.
- `/backtests` — create/list/get/delete (one or all).
- `/orders` — create order (only in Trading mode).
- `/settings` — read/update settings (including order confirmation).
- `/status/health` — health check.
- `/notifications/test` — test message in Telegram (if configured).

## Services and Components

- **Data layer**:

  - REST (history), WebSocket (live) → Binance Futures USDT-M adapter.
  - Exchange validations: pricePrecision, quantityPrecision, minNotional, tickSize/stepSize.
  - WS recovery: auto-reconnect, resync via REST snapshot, deduplication of events.
  - Rate-limit & retries: request queue, backoff, idempotency.
  - Feed for Backtrader.

- **Storage**:

  - **SQLite (configs/settings only)** — single file `/data/app.db`; `PRAGMA journal_mode=WAL`, indexes for fast reads.
  - **Test/historical data and results** — stored locally in volume: Parquet or CSV/JSON with folder hierarchy:
    - `/data/candles/{exchange}/{symbol}/{tf}.parquet`
    - `/data/backtests/{date}/{pair}_{strategy}_{tf}.json`
    - `/data/reports/{id}/...`
  - **Backtest artifacts** — in `/data/artifacts/` (charts, reports).

- **Strategies**:

  - Plugin system.
  - At least one base strategy (e.g., SMC).
  - Versioning of strategies and parameters.
  - Input/output contract for signals: side, entry, SL, TP, confidence.
  - Unit tests for strategies on synthetic data.

- **Orders**:

  - Market / limit.
  - Stop-market / stop-limit, trailing-stop.
  - Pending confirmation with TTL (auto-cancel if not confirmed).
  - Position size calculated by % risk and SL; leverage control.
  - Idempotent requests.

- **Security**:

  - Keys stored in `.env`.
  - No logging of sensitive data.

- **Monitoring**:

  - Logs and health-checks.
  - Structured logs (JSON) with correlation IDs of tasks/signals.
  - Debug mode (toggle in `.env`).

## Non-functional requirements

- **Performance**: signal latency ≤1s from WS event.
- **Backtests**:
  - Accuracy (UTC, no look-ahead bias).
  - Include commissions, slippage, funding (futures) in PnL.
  - Margin rules and leverage (initial/maintenance margin).
  - Determinism: random\_seed, UTC, no look-ahead.
  - Candle data integrity check (no gaps/duplicates).
- **Tests**: coverage ≥70%.
- **Style**: PEP8.
- **CI/CD**:
  - Linting, tests, Docker image build, example `docker-compose.yml`.
  - Volume mounts for `/data`, example startup.

## Risk management

- Loss limits.
- Max number of open positions.
- Mandatory minimum RR ≥ 3 in backtests and signals.
- Global/per-class RR ≥ 3 enforcement (live and backtest).

## Additional (optional)

- Paper trading mode.
- Audit log of actions and decisions.
- Export results (CSV/JSON).
- Dark theme, localization EN/UK.
- Notifications (Telegram): alerts about new signals or backtest completions.
  - `.env` example:
    ```env
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=...
    TELEGRAM_ENABLED=true
    EXCHANGE=binance_futures
    WS_URL=wss://...
    REST_URL=https://...
    DB_PATH=/data/app.db
    DATA_DIR=/data
    ```

