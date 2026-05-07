// ═══════════════════════════════════════════════════════════════════════════
// 🦁 صفحة الجدول الخامس
// ═══════════════════════════════════════════════════════════════════════════
'use client';

import { useState } from 'react';
import { IndicatorsTable } from '@/components/Table5';

const SYMBOLS = ['XAU/USD', 'XTI/USD', 'EUR/USD', 'BTC/USD'];

export default function Table5Page() {
  const [symbol, setSymbol] = useState('XAU/USD');

  return (
    <main className="min-h-screen bg-[#0A0A0A] text-neutral-100 p-6" dir="rtl">
      {/* اختيار الرمز */}
      <div className="mb-4 flex items-center gap-2">
        <span className="text-sm text-neutral-400">الرمز:</span>
        {SYMBOLS.map((s) => (
          <button
            key={s}
            onClick={() => setSymbol(s)}
            className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
              s === symbol
                ? 'border-[#C9A227] bg-[#C9A227]/10 text-[#C9A227]'
                : 'border-neutral-700 text-neutral-400 hover:border-neutral-500'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <IndicatorsTable symbol={symbol} />
    </main>
  );
}
