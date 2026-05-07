// ═══════════════════════════════════════════════════════════════════════════
// 🦁 جدول المؤشرات الـ 71 × 6 أطر زمنية + قرار نهائي
// ═══════════════════════════════════════════════════════════════════════════
'use client';

import { useMemo, useState } from 'react';
import { useTable5Stream } from '@/lib/useTable5Stream';
import { IndicatorRow } from './IndicatorRow';
import { DecisionRow } from './DecisionRow';

const TF_ORDER = ['1M', '5M', '15M', '30M', '1H', '4H'];
const CATEGORIES_AR = [
  'مؤشرات الاتجاه',
  'مؤشرات الزخم',
  'مؤشرات التذبذب والتقلب',
  'مؤشرات الحجم والتدفق',
  'الدعم والمقاومة وفيبوناتشي',
  'مؤشرات متكاملة',
];

interface Props {
  symbol: string;
}

export function IndicatorsTable({ symbol }: Props) {
  const { decision, error, connected } = useTable5Stream(symbol);
  const [filterCat, setFilterCat] = useState<string | null>(null);
  const [filterTier, setFilterTier] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!decision) return [];
    return decision.indicators.filter((r) => {
      if (filterCat && r.category !== filterCat) return false;
      if (filterTier && r.tier !== filterTier) return false;
      return true;
    });
  }, [decision, filterCat, filterTier]);

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-rose-300">
        خطأ في الاتصال: {error}
      </div>
    );
  }
  if (!decision) {
    return (
      <div className="rounded-xl border border-[#C9A227]/30 bg-[#0A0A0A] p-8 text-center text-neutral-400">
        جاري حساب الإشارات...
      </div>
    );
  }

  return (
    <div className="text-right" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-[#C9A227]">
            🦁 الجدول الخامس — المؤشرات الفنية
          </h2>
          <p className="text-sm text-neutral-400">
            {symbol} · 71 مؤشر × 6 أطر زمنية · الوزن في القرار: 10٪
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`h-2 w-2 rounded-full ${
              connected ? 'bg-emerald-500 animate-pulse' : 'bg-neutral-600'
            }`}
          />
          <span className="text-neutral-400">
            {connected ? 'مباشر' : 'غير متصل'}
          </span>
        </div>
      </div>

      {/* القرار النهائي */}
      <DecisionRow decision={decision} />

      {/* المرشحات */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs text-neutral-400">تصنيف:</span>
        <button
          onClick={() => setFilterCat(null)}
          className={`text-xs rounded-full px-3 py-1 border ${
            filterCat === null
              ? 'border-[#C9A227] text-[#C9A227]'
              : 'border-neutral-700 text-neutral-400 hover:border-neutral-500'
          }`}
        >
          الكل
        </button>
        {CATEGORIES_AR.map((c) => (
          <button
            key={c}
            onClick={() => setFilterCat(c === filterCat ? null : c)}
            className={`text-xs rounded-full px-3 py-1 border ${
              filterCat === c
                ? 'border-[#C9A227] text-[#C9A227]'
                : 'border-neutral-700 text-neutral-400 hover:border-neutral-500'
            }`}
          >
            {c}
          </button>
        ))}
        <span className="text-xs text-neutral-400 mr-3">Tier:</span>
        {(['S', 'A', 'B', 'C'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setFilterTier(t === filterTier ? null : t)}
            className={`text-xs rounded-full px-3 py-1 border ${
              filterTier === t
                ? 'border-[#C9A227] text-[#C9A227]'
                : 'border-neutral-700 text-neutral-400 hover:border-neutral-500'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* الجدول */}
      <div className="overflow-x-auto rounded-xl border border-neutral-800 bg-[#0A0A0A]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 bg-[#0F0F0F]">
              <th className="px-3 py-2 text-right font-semibold text-[#C9A227] sticky right-0 bg-[#0F0F0F] z-10">
                المؤشر
              </th>
              {TF_ORDER.map((tf) => (
                <th
                  key={tf}
                  className="px-2 py-2 text-center font-semibold text-[#C9A227] border-r border-neutral-800/50"
                >
                  {tf}
                </th>
              ))}
              <th className="px-2 py-2 text-center font-semibold text-[#C9A227] border-r border-neutral-800/50">
                موزون
              </th>
              <th className="px-2 py-2 text-center font-semibold text-[#C9A227]">عرض</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <IndicatorRow key={row.indicator_id} row={row} />
            ))}
          </tbody>
        </table>
      </div>

      {/* عداد */}
      <div className="mt-2 text-xs text-neutral-500 text-left">
        عرض {filtered.length} من {decision.indicators.length} مؤشر
      </div>
    </div>
  );
}
