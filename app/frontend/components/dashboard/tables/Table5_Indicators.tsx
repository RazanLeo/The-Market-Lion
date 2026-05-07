'use client';
import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

export function Table5_Indicators({ symbol, tf }: { symbol: string; tf: string }) {
  const t = useTranslations('dashboard');
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    let alive = true;
    const f = async () => { try { const r = await api.get(`/analysis/indicators?symbol=${symbol}&tf=${tf}`); if (alive) setRows(r.data?.indicators ?? []); } catch {} };
    f(); const i = setInterval(f, 15000);
    return () => { alive = false; clearInterval(i); };
  }, [symbol, tf]);
  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
      <h3 className="mb-3 text-sm font-semibold text-gold">5. {t('indicators')} (10%) — {rows.length} active</h3>
      <div className="max-h-96 overflow-auto scrollbar-thin">
        <table className="min-w-full text-xs">
          <thead className="sticky top-0 bg-bg-secondary"><tr>{['Indicator','Result','Confidence','Weight'].map(h=><th key={h} className="px-2 py-1 text-start text-muted font-normal">{h}</th>)}</tr></thead>
          <tbody>{rows.length===0?<tr><td className="px-2 py-3 text-muted" colSpan={4}>—</td></tr>:rows.map((r,i)=>(<tr key={i} className="border-t border-[rgba(201,162,39,0.05)]"><td className="px-2 py-1">{r.code}</td><td className="px-2 py-1">{badge(r.result)}</td><td className="px-2 py-1 tabular">{(r.confidence||0).toFixed(0)}</td><td className="px-2 py-1 tabular">{(r.weight||0).toFixed(2)}</td></tr>))}</tbody>
        </table>
      </div>
    </section>
  );
}
function badge(r:string){const cls=r==='buy'?'cell-buy':r==='sell'?'cell-sell':'cell-neutral';return <span className={`${cls} px-2 py-0.5 rounded text-[10px] font-semibold`}>{(r||'').toUpperCase()}</span>;}
