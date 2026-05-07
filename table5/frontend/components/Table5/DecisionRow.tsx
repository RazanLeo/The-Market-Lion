// ═══════════════════════════════════════════════════════════════════════════
// 🦁 صف القرار النهائي — ملخص + مؤشر confidence + شارة المستوى
// ═══════════════════════════════════════════════════════════════════════════
'use client';

import { Decision } from '@/lib/api';

interface Props {
  decision: Decision;
}

export function DecisionRow({ decision }: Props) {
  const pct = Math.round(decision.confidence * 100);
  const dirColor =
    decision.decision === 'شراء'
      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/40'
      : decision.decision === 'بيع'
      ? 'text-rose-400 bg-rose-500/10 border-rose-500/40'
      : 'text-neutral-400 bg-neutral-700/30 border-neutral-700/40';

  const barColor =
    decision.decision === 'شراء'
      ? 'bg-emerald-500'
      : decision.decision === 'بيع'
      ? 'bg-rose-500'
      : 'bg-neutral-500';

  return (
    <div className="rounded-xl border border-[#C9A227]/30 bg-gradient-to-l from-[#0A0A0A] to-[#0F0F0F] p-4 mb-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-sm text-neutral-400">القرار النهائي</span>
          <span
            className={`rounded-lg border px-3 py-1 text-base font-bold ${dirColor}`}
          >
            {decision.decision}
          </span>
          <span className="text-sm text-neutral-300">{decision.signal_level}</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {decision.filters.choppiness_applied && (
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-amber-300">
              فلتر تذبذب
            </span>
          )}
          {decision.filters.htf_veto_applied && (
            <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-violet-300">
              HTF Veto
            </span>
          )}
          {decision.filters.convergence_boost && (
            <span className="rounded-full bg-[#C9A227]/20 px-2 py-0.5 text-[#C9A227]">
              S Convergence (+10٪)
            </span>
          )}
          <span className="text-neutral-500">
            S consensus: {decision.filters.tier_s_consensus}
          </span>
        </div>
      </div>

      {/* شريط الثقة */}
      <div className="mt-3">
        <div className="flex justify-between text-xs text-neutral-400 mb-1">
          <span>قوة القرار</span>
          <span className="font-mono">
            score: {decision.net_score >= 0 ? '+' : ''}
            {decision.net_score.toFixed(4)} | confidence: {pct}%
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden">
          <div
            className={`h-full ${barColor} transition-all duration-500`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
