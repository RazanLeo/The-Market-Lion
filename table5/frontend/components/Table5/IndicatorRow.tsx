// ═══════════════════════════════════════════════════════════════════════════
// 🦁 صف مؤشر واحد — اسم + Tier + 6 خلايا أطر + دائرة قرار + زر toggle عرض
// ═══════════════════════════════════════════════════════════════════════════
'use client';

import { useState } from 'react';
import { IndicatorRow as Row } from '@/lib/api';
import { SignalCell } from './SignalCell';
import { TierBadge } from './TierBadge';
import { Eye, EyeOff } from 'lucide-react';

const TF_ORDER = ['1M', '5M', '15M', '30M', '1H', '4H'];

interface Props {
  row: Row;
}

export function IndicatorRow({ row }: Props) {
  const [showOnChart, setShowOnChart] = useState(false);

  const decisionColor =
    row.direction === 'شراء'
      ? 'text-emerald-400'
      : row.direction === 'بيع'
      ? 'text-rose-400'
      : 'text-neutral-400';

  return (
    <tr className="hover:bg-neutral-900/40 transition-colors border-b border-neutral-900/40">
      <td className="px-3 py-1.5 sticky right-0 bg-[#0A0A0A] z-10">
        <div className="flex items-center gap-2">
          <TierBadge tier={row.tier} />
          <span className="text-xs text-neutral-200 truncate max-w-[260px]">
            #{row.indicator_id} {row.indicator_name}
          </span>
        </div>
      </td>
      {TF_ORDER.map((tf) => (
        <SignalCell
          key={tf}
          signal={row.signals[tf] || 'محايد'}
          rawValue={row.raw_values[tf]}
        />
      ))}
      <td className="px-2 py-1.5 text-center border-r border-neutral-800/50">
        <span className={`font-mono text-xs ${decisionColor}`}>
          {row.weighted_score >= 0 ? '+' : ''}
          {row.weighted_score.toFixed(3)}
        </span>
      </td>
      <td className="px-2 py-1.5 text-center">
        <button
          onClick={() => setShowOnChart((v) => !v)}
          className={`rounded-md p-1.5 transition-colors ${
            showOnChart
              ? 'bg-[#C9A227]/20 text-[#C9A227]'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
          title={showOnChart ? 'إخفاء من الشارت' : 'إظهار على الشارت'}
        >
          {showOnChart ? <Eye size={14} /> : <EyeOff size={14} />}
        </button>
      </td>
    </tr>
  );
}
