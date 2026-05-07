-- ═══════════════════════════════════════════════════════════════════════════
-- 🦁 أسد السوق — Migration 004
-- تفضيلات المستخدم للعرض البصري للمؤشرات على الشارت
-- (الافتراضي: كل المؤشرات OFF، التصويت يستمر دائماً في الخلفية)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS user_chart_preferences (
    user_id        BIGINT       NOT NULL,                          -- FK to users.id
    indicator_id   SMALLINT     NOT NULL REFERENCES indicators_catalog(id) ON DELETE CASCADE,
    show_on_chart  BOOLEAN      NOT NULL DEFAULT FALSE,            -- الافتراضي OFF
    custom_color   VARCHAR(7),                                     -- #RRGGBB (اختياري)
    custom_opacity DECIMAL(3,2) DEFAULT 1.0 CHECK (custom_opacity BETWEEN 0 AND 1),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, indicator_id)
);

CREATE INDEX IF NOT EXISTS idx_chart_prefs_user
    ON user_chart_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_chart_prefs_active
    ON user_chart_preferences(user_id, indicator_id) WHERE show_on_chart = TRUE;

COMMENT ON TABLE user_chart_preferences IS 'تفضيلات عرض المؤشرات على شارت TradingView لكل مستخدم. التصويت لا يتأثر بهذه التفضيلات.';
