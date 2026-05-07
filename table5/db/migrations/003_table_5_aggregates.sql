-- ═══════════════════════════════════════════════════════════════════════════
-- 🦁 أسد السوق — Migration 003
-- نتائج محرك التصويت المجمعة لكل لقطة زمنية
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS table_5_aggregates (
    timestamp        TIMESTAMPTZ   NOT NULL,
    symbol           VARCHAR(20)   NOT NULL,
    selected_tf      VARCHAR(5)    NOT NULL CHECK (selected_tf IN ('1M','5M','15M','30M','1H','4H')),
    net_score        DECIMAL(10,8) NOT NULL,                       -- -0.10 .. +0.10
    confidence       DECIMAL(8,6)  NOT NULL,                       -- 0..1
    decision         VARCHAR(10)   NOT NULL CHECK (decision IN ('شراء','بيع','محايد')),
    signal_level     VARCHAR(20)   NOT NULL,                       -- 👑/🟢/🟡/⚪
    indicators_data  JSONB         NOT NULL,                       -- snapshot كامل للـ71 مؤشر

    PRIMARY KEY (timestamp, symbol, selected_tf)
);

SELECT create_hypertable('table_5_aggregates', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_aggregates_symbol
    ON table_5_aggregates(symbol, selected_tf, timestamp DESC);

-- احفظ 180 يوم
SELECT add_retention_policy('table_5_aggregates', INTERVAL '180 days', if_not_exists => TRUE);

COMMENT ON TABLE table_5_aggregates IS 'مخرجات محرك التصويت — مساهمة الجدول الخامس في القرار الكلي للبوت';
