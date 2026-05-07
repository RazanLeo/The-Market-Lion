'use client';
import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

export function Table6_OrderFlow({ symbol }: { symbol: string }) {
  const t = useTranslations('dashboard');
  const [data, setData] = useState<any>({ buckets:{}, buy_volume_usd:0, sell_volume_usd:0, direction:'neutral' });
  useEffect(() => {
    let alive = true;
    const f = async () => { try { const r = await api.get(`/analysis/flow?symbol=${symbol}`); if (alive) setData(r.data); } catch {} };
    f(); const i = setInterval(f, 5000);
    return () => { alive = false; clearInterval(i); };
  }, [symbol]);
  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
      <h3 className="mb-3 text-sm font-semibold text-gold">6. {t('flow')} (10%)</h3>
      <div className="grid gap-3 md:grid-cols-4">
        {['10K','100K','500K','1M+'].map(b => (<div key={b} className="rounded-md border border-[rgba(201,162,39,0.1)] bg-bg-primary p-3 text-center"><div className="text-[10px] text-muted">{b}</div><div className="text-lg text-gold tabular">{(data.buckets?.[b]||0).toLocaleString?.()}</div></div>))}
        <div className="rounded-md border border-bull/40 bg-[rgba(14,122,44,0.05)] p-3 text-center md:col-span-2"><div className="text-[10px] text-muted">Buy Volume $</div><div className="text-lg text-bull tabular">{(data.buy_volume_usd||0).toLocaleString?.()}</div></div>
        <div className="rounded-md border border-bear/40 bg-[rgba(176,20,12,0.05)] p-3 text-center md:col-span-2"><div className="text-[10px] text-muted">Sell Volume $</div><div className="text-lg text-bear tabular">{(data.sell_volume_usd||0).toLocaleString?.()}</div></div>
        <div className="rounded-md border border-[rgba(201,162,39,0.3)] bg-[rgba(201,162,39,0.05)] p-3 text-center md:col-span-4"><div className="text-[10px] text-muted">Direction</div><div className="text-lg text-gold uppercase">{data.direction}</div></div>
      </div>
    </section>
  );
}
