'use client';
import { useEffect, useRef } from 'react';

declare global { interface Window { TradingView?: any } }

export function TradingViewEmbed({ symbol = 'OANDA:XAUUSD', interval = '15', theme = 'dark' }: { symbol?: string; interval?: string; theme?: 'light' | 'dark' }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const id = `tv_${Math.random().toString(36).slice(2, 9)}`;
    ref.current.innerHTML = `<div id="${id}" style="width:100%;height:100%"></div>`;
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (window.TradingView && ref.current?.querySelector(`#${id}`)) {
        new window.TradingView.widget({
          autosize: true,
          symbol,
          interval,
          timezone: 'Etc/UTC',
          theme,
          style: '1', // candles
          locale: 'en',
          toolbar_bg: '#0A0A0A',
          enable_publishing: false,
          hide_top_toolbar: false,
          allow_symbol_change: true,
          studies: ['RSI@tv-basicstudies', 'MACD@tv-basicstudies', 'BB@tv-basicstudies', 'MAExp@tv-basicstudies', 'VWAP@tv-basicstudies'],
          container_id: id,
        });
      }
    };
    document.body.appendChild(script);
    return () => { script.remove(); };
  }, [symbol, interval, theme]);

  return <div ref={ref} className="w-full rounded-md border border-[rgba(201,162,39,0.15)] bg-bg-primary" style={{ height: 520 }} />;
}
