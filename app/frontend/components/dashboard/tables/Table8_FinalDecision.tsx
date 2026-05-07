'use client';
import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

export function Table8_FinalDecision({ symbol, tf }: { symbol: string; tf: string }) {
  const t = useTranslations('dashboard');
  const [c, setC] = useState<any>(null);
  useEffect(() => {
    let alive = true;
    const f = async () => { try { const r = await api.get(`/analysis/confluence?symbol=${symbol}&tf=${tf}`); if (alive) setC(r.data); } catch {} };
    f(); const i = setInterval(f, 5000);
    return () => { alive = false; clearInterval(i); };
  }, [symbol, tf]);
  const dec = c?.decision || 'wait';
  const color = dec==='buy' ? 'text-bull' : dec==='sell' ? 'text-bear' : 'text-muted';
  return (
    <section className="rounded-lg border border-gold/40 bg-[rgba(201,162,39,0.05)] p-4 shadow-glow-soft">
      <h3 className="mb-3 text-sm font-semibold text-gold">8. {t('decision')}</h3>
      <div className="grid gap-3 md:grid-cols-6">
        <KV k="Fundamental /20" v={c?.fundamental_pct?.toFixed(2) || '—'} />
        <KV k="Basics /30" v={c?.basics_pct?.toFixed(2) || '—'} />
        <KV k="Schools /30" v={c?.schools_pct?.toFixed(2) || '—'} />
        <KV k="Indicators /10" v={c?.indicators_pct?.toFixed(2) || '—'} />
        <KV k="Flow /10" v={c?.flow_pct?.toFixed(2) || '—'} />
        <div className="col-span-1 rounded-md border border-gold bg-bg-primary p-3 text-center">
          <div className="text-[10px] text-muted">{t('confluence_score')}</div>
          <div className="text-3xl font-bold text-gold tabular">{c?.total_pct?.toFixed(1) ?? '—'}%</div>
        </div>
      </div>
      <div className="mt-3 rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-4 text-center">
        <div className="text-[10px] text-muted">{t('decision')}</div>
        <div className={`text-4xl font-display ${color}`}>{dec.toUpperCase()}</div>
        <div className="mt-1 text-[10px] text-muted">{c?.payload?.direction ?? '-'} · ts {c?.ts?.slice(11,16) ?? '—'}</div>
      </div>
    </section>
  );
}
function KV({ k, v }: { k: string; v: any }){return <div className="rounded-md border border-[rgba(201,162,39,0.1)] bg-bg-primary p-3 text-center"><div className="text-[10px] text-muted">{k}</div><div className="text-lg text-gold tabular">{v}</div></div>;}
