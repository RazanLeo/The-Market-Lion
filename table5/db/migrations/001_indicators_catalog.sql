-- ═══════════════════════════════════════════════════════════════════════════
-- 🦁 أسد السوق — Migration 001
-- جدول تعريف الـ 71 مؤشراً (المرجع الثابت)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS indicators_catalog (
    id              SMALLINT      PRIMARY KEY,                    -- 1..71
    name            VARCHAR(100)  NOT NULL UNIQUE,                -- مطابق للـ Excel
    name_ar         VARCHAR(150),                                  -- الاسم العربي (اختياري)
    category        VARCHAR(80)   NOT NULL,                        -- التصنيف بالعربي
    category_en     VARCHAR(50)   NOT NULL,                        -- التصنيف بالإنجليزي
    tier            CHAR(1)       NOT NULL CHECK (tier IN ('S','A','B','C')),
    weight_in_module DECIMAL(10,8) NOT NULL,                      -- وزن من 0.10
    strategy_text   TEXT          NOT NULL,                        -- الاستراتيجية الذهبية
    ta_lib_function VARCHAR(200),                                  -- "ta.RSI(close, 14)"
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,           -- يتحكم بها الأدمن
    sort_order      SMALLINT      NOT NULL,                        -- ترتيب العرض
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_indicators_category ON indicators_catalog(category_en);
CREATE INDEX idx_indicators_tier     ON indicators_catalog(tier);
CREATE INDEX idx_indicators_active   ON indicators_catalog(is_active) WHERE is_active = TRUE;

-- التحقق من الأوزان
COMMENT ON COLUMN indicators_catalog.weight_in_module IS 'وزن المؤشر من 10٪ (0..0.10). مجموع الـ 71 = 0.10 بالضبط';
COMMENT ON COLUMN indicators_catalog.tier IS 'S=4 (مؤسسي جوهري) | A=3 (موثوقية عالية) | B=2 (داعم صلب) | C=1 (تخصصي نادر)';
