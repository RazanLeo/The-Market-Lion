-- ═══════════════════════════════════════════════════════════════════════════
-- 🦁 أسد السوق — Migration 002
-- جدول إشارات المؤشرات (TimescaleDB hypertable)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS indicator_signals (
    timestamp     TIMESTAMPTZ   NOT NULL,
    symbol        VARCHAR(20)   NOT NULL,                          -- "XAU/USD", "XTI/USD"
    indicator_id  SMALLINT      NOT NULL REFERENCES indicators_catalog(id) ON DELETE CASCADE,
    timeframe     VARCHAR(5)    NOT NULL CHECK (timeframe IN ('1M','5M','15M','30M','1H','4H')),
    signal        VARCHAR(10)   NOT NULL CHECK (signal IN ('شراء','بيع','محايد')),
    raw_value     DECIMAL(20,8),                                   -- القيمة الخام للمؤشر (للعرض)
    metadata      JSONB,                                           -- معلومات إضافية للـ debugging

    PRIMARY KEY (timestamp, symbol, indicator_id, timeframe)
);

-- تحويل لـ hypertable للأداء العالي مع time-series
SELECT create_hypertable('indicator_signals', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- فهارس للاستعلامات الشائعة
CREATE INDEX IF NOT EXISTS idx_signals_symbol_tf
    ON indicator_signals(symbol, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_indicator
    ON indicator_signals(indicator_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_latest
    ON indicator_signals(symbol, timeframe, indicator_id, timestamp DESC);

-- Retention: احفظ 90 يوم فقط (يمكن للأدمن تعديلها)
SELECT add_retention_policy('indicator_signals', INTERVAL '90 days', if_not_exists => TRUE);

-- Continuous aggregate: آخر إشارة لكل دقيقة
CREATE MATERIALIZED VIEW IF NOT EXISTS indicator_signals_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', timestamp) AS bucket,
    symbol, indicator_id, timeframe,
    last(signal, timestamp) AS latest_signal,
    last(raw_value, timestamp) AS latest_value,
    last(metadata, timestamp) AS latest_metadata
FROM indicator_signals
GROUP BY bucket, symbol, indicator_id, timeframe;

SELECT add_continuous_aggregate_policy('indicator_signals_1min',
    start_offset => INTERVAL '5 minutes',
    end_offset   => INTERVAL '30 seconds',
    schedule_interval => INTERVAL '30 seconds',
    if_not_exists => TRUE
);

COMMENT ON TABLE indicator_signals IS 'time-series إشارات المؤشرات الـ71 على 6 أطر زمنية';
