# Technical Specification for Trading Bot

## General

- Language: **Python**
- Framework: **Backtrader** ([repository](https://github.com/mementum/backtrader))
- Architecture: **Docker + FastAPI + SPA Web Interface**
- Configuration: **Environment variables** file
- Modes of operation:
  - **Simulation Mode** (default) — paper trading with real-time data
  - **Live Trading Mode** (with approval) — real order execution on Binance Futures

## Web Interface

At least 2 tabs:

### 1. Dashboard

- Add / remove trading pairs.
- Display signals for each pair (live/last N events).
- If keys are provided — enable trading.
- Checkbox: **"Confirm order execution"**
  - If disabled — orders are executed automatically.
  - If enabled — a modal window with confirmation (details: pair, volume, order type, SL/TP) is shown.
  - Unconfirmed signals are stored in the *pending confirmation* list.
- **Simulation Controls**: Start/stop simulation, reset portfolio, view performance

### 2. Backtest

- Select pair, strategy, timeframes, data range (1–30 days).
- Start backtest → results stored locally. 
- Table of previous results (strategy, timeframe, parameters).
- Button **"Detailed statistics"** next to each test opens a modal window; metrics (win-rate, entries/exits, TP/SL, number of trades) are displayed only after clicking. Nearby buttons **"Delete result"** or **"Delete all"** are available.

### 3. Simulation (New)

- **Portfolio Overview**: Current value, P&L, open positions
- **Performance Metrics**: Sharpe ratio, drawdown, win rate
- **Trade History**: Complete list of executed trades
- **Position Management**: View and manage open positions
- **Settings**: Simulation parameters and risk management

## API (FastAPI)

- `/pairs` — CRUD operations with pairs.
- `/signals` — list / stream of signals.
- `/backtests` — create/list/get/delete (one or all).
- `/orders` — create order (only in Trading mode).
- `/settings` — read/update settings (including order confirmation).
- `/status/health` — health check.
- `/notifications/test` — test message in Telegram (if configured).
- `/simulation/status` — simulation engine status.
- `/simulation/portfolio` — current portfolio information.
- `/simulation/positions` — open positions.
- `/simulation/trades` — trade history.
- `/simulation/performance` — performance metrics.
- `/simulation/reset` — reset simulation.
- `/simulation/start` — start simulation engine.
- `/simulation/stop` — stop simulation engine.

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
  - **Simulation data** — separate tables with `_sim` suffix for complete isolation.

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

- **Simulation Engine**:

  - Complete paper trading environment.
  - Real-time price updates from WebSocket feeds.
  - Portfolio management with P&L tracking.
  - Order processing with slippage and commission simulation.
  - Performance metrics and portfolio snapshots.
  - Complete data isolation from live trading.

- **Security**:

  - Keys stored in `.env`.
  - No logging of sensitive data.
  - Explicit approval required for live trading.
  - Simulation mode by default.

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
  - Determinism: random_seed, UTC, no look-ahead.
  - Candle data integrity check (no gaps/duplicates).
- **Simulation**:
  - Real-time performance with ≤5s tick intervals.
  - Memory usage <500MB for typical portfolios.
  - Database operations <100ms response time.
  - Complete isolation from live trading data.
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
- Simulation mode protection (no real money at risk).

## Additional (optional)

- Paper trading mode (implemented as simulation engine).
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
    TRADING_MODE=simulation
    TRADING_APPROVED=false
    SIMULATION_INITIAL_CAPITAL=10000.0
    SIMULATION_COMMISSION=0.001
    SIMULATION_SLIPPAGE=0.0001
    ```

## Implementation Steps

### STEP 1: Data Layer ✅
Implement package `src/data`:
- binance_client.py (REST + WS client for Binance USDT-M Futures).
- stream.py (WS manager with auto-reconnect, deduplication, resync via REST snapshot).
- feed.py (custom Backtrader data feed subclass pulling from WS/Parquet).
- validators.py (exchange rules: tickSize, stepSize, precision, minNotional).
- rate_limit.py (queue with retries/backoff/idempotency).
All timestamps in UTC. No look-ahead bias.

### STEP 2: API (FastAPI) ✅
Implement package `src/api`:
- main.py with FastAPI app + routers.
- Routers: pairs, signals, backtests, orders, settings, status, notifications, simulation.
- schemas.py with Pydantic models.
- Enforce TRADING_ENABLED flag (view-only mode if no keys).
- SSE/WS stream for /signals.
- Structured logs with correlation_id middleware.

### STEP 3: Backtests ✅
Implement package `src/backtests`:
- runner.py using Backtrader.Cerebro (attach strategy, feed, run).
- storage.py (save results under /data/backtests/, /data/artifacts/).
- metrics.py (win-rate, trades, TP/SL, commissions, slippage, funding).
- integrity.py (check candles: no gaps/dupes).
- CLI entrypoint.
Deterministic: random_seed, UTC.

### STEP 4: Strategies ✅
Implement package `src/strategies`:
- base.py (abstract Backtrader.Strategy with generate_signals contract).
- registry.py (auto-discovery of *.py strategies, versioning).
- smc_signal.py (simplified, optimized Smart Money Concepts strategy).
Signals: side, entry, SL, TP, confidence.
Include synthetic data tests.

### STEP 5: Orders ✅
Implement package `src/orders`:
- sizing.py (risk% based position sizing, leverage-aware).
- types.py (market, limit, stop-market, stop-limit, trailing-stop).
- queue.py (idempotent submissions, dedupe).
- pending.py (confirmation store with TTL).

### STEP 6: Storage ✅
Implement package `src/storage`:
- db.py (SQLite app.db, WAL mode, indexes).
- configs.py (settings CRUD).
- files.py (helpers for candle/backtest/report paths).
- simulation.py (simulation-specific database schema).

### STEP 7: Simulation Engine ✅
Implement package `src/simulation`:
- engine.py (main simulation engine with portfolio management).
- portfolio.py (position tracking and P&L calculation).
- config.py (simulation configuration and mode management).
- Integration with orders package via adapters.

### STEP 8: Monitoring & CI ✅
Add:
- Logging config (JSON structured).
- /status/health endpoint.
- Dockerfile (multi-stage slim).
- docker-compose.yml with /data volume.
- GitHub Actions CI: lint (ruff), mypy, pytest, build image.
- .env.example file with TELEGRAM_*, EXCHANGE, etc.

### STEP 9: Web UI (SPA) ✅
Scaffold minimal SPA (React/Vite or Svelte):
- Dashboard: pairs CRUD, live signals, trading toggle, confirm-order checkbox, pending list.
- Backtest tab: form (pair/strategy/TF/range), table of runs, detailed modal, delete.
- Simulation tab: portfolio overview, performance metrics, trade history, position management.
- Dark theme, EN/UK i18n placeholders.
Strict API calls to FastAPI backend, no extra endpoints.

### STEP 10: Integration & Testing ✅
Complete integration testing:
- End-to-end simulation workflows.
- API endpoint validation.
- Performance testing.
- Security testing.
- Documentation updates.

