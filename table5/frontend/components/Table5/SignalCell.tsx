// ═══════════════════════════════════════════════════════════════════════════
// 🦁 خلية إشارة على إطار زمني واحد
// ═══════════════════════════════════════════════════════════════════════════
'use client';

import { cn } from '@/lib/utils';

interface Props {
  signal: 'شراء' | 'بيع' | 'محايد' | string;
  rawValue?: number | null;
}

export function SignalCell({ signal, rawValue }: Props) {
  const cls =
    signal === 'شراء'
      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
      : signal === 'بيع'
      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
      : 'bg-neutral-700/40 text-neutral-400 border-neutral-700/60';

  return (
    <td className="px-2 py-1.5 text-center border-r border-neutral-800/50">
      <div
        className={cn(
          'rounded-md border px-2 py-1 text-xs font-semibold transition-colors',
          cls,
        )}
        title={rawValue != null ? `قيمة خام: ${rawValue.toFixed(4)}` : undefined}
      >
        {signal}
      </div>
    </td>
  );
}
