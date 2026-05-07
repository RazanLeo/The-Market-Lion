'use client';
import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

export function Table2_Fundamental({ symbol, tf }: { symbol: string; tf: string }) {
  const t = useTranslations('dashboard');
  const [news, setNews] = useState<any[]>([]); const [events, setEvents] = useState<any[]>([]);
  useEffect(() => {
    let alive = true;
    const f = async () => { try { const r = await api.get(`/analysis/fundamental?symbol=${symbol}&tf=${tf}`); if (alive){ setNews(r.data?.news??[]); setEvents(r.data?.events??[]); } } catch {} };
    f(); const i = setInterval(f, 15000);
    return () => { alive = false; clearInterval(i); };
  }, [symbol, tf]);

  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
      <h3 className="mb-3 text-sm font-semibold text-gold">2. {t('fundamental')} (20%)</h3>
      <div className="overflow-x-auto scrollbar-thin">
        <table className="min-w-full text-xs">
          <thead><tr>{['Time','Source/Country','Title','Prev','Forecast','Actual','Sentiment','Impact','Bias'].map(h=><th key={h} className="px-2 py-1 text-start text-muted font-normal">{h}</th>)}</tr></thead>
          <tbody>
            {events.map(e=>(<tr key={e.id} className="border-t border-[rgba(201,162,39,0.05)]"><td className="px-2 py-1 tabular">{e.ts?.slice(0,16)}</td><td className="px-2 py-1">{e.country}</td><td className="px-2 py-1">{e.title}</td><td className="px-2 py-1 tabular">{e.previous??'—'}</td><td className="px-2 py-1 tabular">{e.forecast??'—'}</td><td className="px-2 py-1 tabular">{e.actual??'—'}</td><td className="px-2 py-1">—</td><td className="px-2 py-1">{e.impact}</td><td className="px-2 py-1">—</td></tr>))}
            {news.map(n=>(<tr key={n.id} className="border-t border-[rgba(201,162,39,0.05)]"><td className="px-2 py-1 tabular">{n.ts?.slice(0,16)}</td><td className="px-2 py-1">{n.source}</td><td className="px-2 py-1">{(n.title||'').slice(0,80)}</td><td className="px-2 py-1">—</td><td className="px-2 py-1">—</td><td className="px-2 py-1">—</td><td className="px-2 py-1 tabular">{n.sentiment}</td><td className="px-2 py-1 tabular">{n.impact}</td><td className="px-2 py-1">{n.sentiment>5?<span className="cell-buy px-1">BUY</span>:n.sentiment<-5?<span className="cell-sell px-1">SELL</span>:'—'}</td></tr>))}
            {(news.length===0&&events.length===0)&&<tr><td className="px-2 py-3 text-muted" colSpan={9}>—</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  );
}
