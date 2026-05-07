'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

const SYMBOLS = ['XAUUSD','USOIL','BRENT','EURUSD','GBPUSD','USDJPY','USDCHF','USDCAD','AUDUSD','NZDUSD','XAGUSD','DXY'];

type Ticker = { symbol: string; price: number; changePct: number; ts?: string; source?: string };

export function TickersStrip() {
  const t = useTranslations();
  const [tickers, setTickers] = useState<Ticker[]>([]);

  useEffect(() => {
    let alive = true;

    const fetchOnce = async () => {
      try {
        const r = await api.get('/market/tickers');
        if (!alive) return;
        const list: Ticker[] = r.data?.tickers ?? [];
        const byCode: Record<string, Ticker> = Object.fromEntries(list.map(x => [x.symbol, x]));
        setTickers(SYMBOLS.map(s => byCode[s]).filter(Boolean));
      } catch {
        // Keep last good snapshot on transient errors.
      }
    };

    fetchOnce();
    const i = setInterval(fetchOnce, 5000);
    return () => { alive = false; clearInterval(i); };
  }, []);

  return (
    <div className="border-b border-[rgba(201,162,39,0.15)] bg-bg-secondary/50">
      <div className="mx-auto flex max-w-[1500px] items-center gap-6 overflow-x-auto px-4 py-2 text-xs scrollbar-thin">
        <span className="shrink-0 text-muted">{t('tickers_strip')}:</span>
        {tickers.map(d => {
          const up = d.changePct >= 0;
          return (
            <div key={d.symbol} className="flex shrink-0 items-center gap-2 tabular">
              <span className="font-semibold text-[var(--text-primary)]">{d.symbol}</span>
              <span className={up ? 'text-bull' : 'text-bear'}>{Number(d.price).toFixed(Number(d.price) < 10 ? 4 : 2)}</span>
              <span className={up ? 'text-bull' : 'text-bear'}>{up ? '▲' : '▼'} {Number(d.changePct).toFixed(2)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
