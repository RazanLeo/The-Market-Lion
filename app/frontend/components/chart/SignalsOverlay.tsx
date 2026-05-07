'use client';
/**
 * Signals overlay panel — renders Buy Lion / Sell Lion / Buy Cub / Sell Cub / ARC / BUMP / DUMP
 * tags above the chart container (since TradingView free embed doesn't allow custom drawings).
 */
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

type Sig = { ts: string; kind: string; decision: string; score: number };

export function SignalsOverlay({ symbol, tf = '15M' }: { symbol: string; tf?: string }) {
  const [items, setItems] = useState<Sig[]>([]);
  useEffect(() => {
    let alive = true;
    async function pull() {
      try {
        const r = await api.get(`/signals/recent?symbol=${symbol}&tf=${tf}&limit=20`);
        if (alive) setItems(r.data?.items ?? []);
      } catch {}
    }
    pull();
    const i = setInterval(pull, 8000);
    return () => { alive = false; clearInterval(i); };
  }, [symbol, tf]);

  return (
    <div className="mt-2 flex gap-2 overflow-x-auto py-1 scrollbar-thin">
      {items.length === 0 ? <span className="text-xs text-muted">Awaiting signals…</span> :
        items.map((s, i) => (
          <span key={i} className={`shrink-0 rounded-md px-2 py-1 text-[10px] font-semibold ${
            s.kind === 'Buy Lion' ? 'bg-bull text-white shadow-glow' :
            s.kind === 'Sell Lion' ? 'bg-bear text-white shadow-glow' :
            s.kind === 'Buy Cub' ? 'cell-buy' :
            s.kind === 'Sell Cub' ? 'cell-sell' : 'cell-neutral'
          }`}>
            {s.kind} · {s.score.toFixed(0)}% · {s.ts.slice(11, 16)}
          </span>
        ))
      }
    </div>
  );
}
