-- ═══════════════════════════════════════════════════════════════════════════
-- 🦁 أسد السوق — Migration 005
-- إعدادات الإدارة (الأوزان والعتبات قابلة للتعديل من لوحة الأدمن)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS admin_indicator_settings (
    id                  SERIAL       PRIMARY KEY,
    setting_key         VARCHAR(100) NOT NULL UNIQUE,
    setting_value       JSONB        NOT NULL,
    description         TEXT,
    updated_by_admin_id BIGINT,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- البيانات الافتراضية الرسمية للجدول الخامس
INSERT INTO admin_indicator_settings (setting_key, setting_value, description) VALUES
    ('tier_values',
     '{"S": 4, "A": 3, "B": 2, "C": 1}',
     'قيم Tier للمؤشرات: S=مؤسسي جوهري، A=موثوقية عالية، B=داعم صلب، C=تخصصي نادر'),
    ('timeframe_weights',
     '{"1M": 5, "5M": 10, "15M": 20, "30M": 18, "1H": 22, "4H": 25}',
     'أوزان الأطر الزمنية الستة (مجموع 100). 4H الإطار المرجعي الأكبر — لا يُخالَف'),
    ('signal_thresholds',
     '{"crown": 0.80, "strong": 0.60, "weak": 0.30}',
     'عتبات مستويات الإشارة: 👑 Crown ≥80%، 🟢 قوية ≥60%، 🟡 ضعيفة ≥30%'),
    ('decision_threshold',
     '0.005',
     'الحد الأدنى لصافي الدرجة لاتخاذ قرار (0.5%)'),
    ('module_weight',
     '0.10',
     'وزن الجدول الخامس من القرار الكلي للبوت (10٪)'),
    ('total_tier_sum',
     '166',
     '13×S(4) + 11×A(3) + 34×B(2) + 13×C(1) = 166. لا يُعدَّل'),
    ('choppiness_filter_threshold',
     '61.8',
     'إذا Choppiness Index > هذه القيمة → سوق جانبي → قلّل الثقة 50٪'),
    ('htf_veto_ratio',
     '1.5',
     'Tier S على 4H يُلغي القرار إذا تفوّق المعارض بهذه النسبة')
ON CONFLICT (setting_key) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_admin_settings_key ON admin_indicator_settings(setting_key);

COMMENT ON TABLE admin_indicator_settings IS 'إعدادات لوحة إدارة الجدول الخامس - قابلة للتعديل من رزان فقط';
