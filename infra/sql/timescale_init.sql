-- Market Lion — TimescaleDB OHLCV Schema

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ──────────────────────────────────────────────
-- OHLCV Candles (hypertable)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ohlcv (
    time        TIMESTAMPTZ NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    timeframe   VARCHAR(5)  NOT NULL,
    open        DOUBLE PRECISION,
    high        DOUBLE PRECISION,
    low         DOUBLE PRECISION,
    close       DOUBLE PRECISION,
    volume      DOUBLE PRECISION,
    source      VARCHAR(20) DEFAULT 'yahoo'
);

SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

CREATE UNIQUE INDEX idx_ohlcv_unique ON ohlcv(time, symbol, timeframe);
CREATE INDEX idx_ohlcv_symbol_tf ON ohlcv(symbol, timeframe, time DESC);

-- Retention policy: keep raw candles 2 years
SELECT add_retention_policy('ohlcv', INTERVAL '2 years', if_not_exists => TRUE);

-- Continuous aggregate: 1-minute candles from tick data
CREATE TABLE IF NOT EXISTS tick_data (
    time        TIMESTAMPTZ NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    bid         DOUBLE PRECISION,
    ask         DOUBLE PRECISION,
    last        DOUBLE PRECISION,
    volume      DOUBLE PRECISION
);

SELECT create_hypertable('tick_data', 'time', if_not_exists => TRUE);
SELECT add_retention_policy('tick_data', INTERVAL '7 days', if_not_exists => TRUE);

-- ──────────────────────────────────────────────
-- Technical Snapshots (for backtesting replay)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS technical_snapshots (
    time            TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(20) NOT NULL,
    timeframe       VARCHAR(5)  NOT NULL,
    school_results  JSONB,
    confluence_score DOUBLE PRECISION,
    signal_side     VARCHAR(5),
    vote_result     JSONB
);

SELECT create_hypertable('technical_snapshots', 'time', if_not_exists => TRUE);

-- ──────────────────────────────────────────────
-- Portfolio Equity Curve
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS equity_curve (
    time        TIMESTAMPTZ NOT NULL,
    user_id     UUID NOT NULL,
    equity      DOUBLE PRECISION,
    balance     DOUBLE PRECISION,
    drawdown    DOUBLE PRECISION,
    open_trades SMALLINT DEFAULT 0
);

SELECT create_hypertable('equity_curve', 'time', if_not_exists => TRUE);
CREATE INDEX idx_equity_user ON equity_curve(user_id, time DESC);
