'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, type IChartApi, type ISeriesApi } from 'lightweight-charts';

export type Drawing =
  | { type: 'line'; x1: string; y1: number; x2: string; y2: number; color?: string; label?: string; thickness?: number }
  | { type: 'rect'; x1: string; y1: number; x2: string; y2: number; color?: string; label?: string }
  | { type: 'marker'; x: string; y: number; shape?: string; color?: string; label?: string; size?: string }
  | { type: 'label'; x: string; y: number; text: string; color?: string; label?: string };

const tsToTime = (s: string): number => {
  // Accepts ISO/UTC string and returns unix seconds for lightweight-charts
  const t = new Date(s).getTime();
  return Math.floor(isNaN(t) ? Date.now() : t / 1000);
};

const mapShape = (shape?: string): 'arrowUp' | 'arrowDown' | 'circle' | 'square' => {
  if (!shape) return 'circle';
  if (shape.includes('arrow_up') || shape === 'triangle_up' || shape === 'star') return 'arrowUp';
  if (shape.includes('arrow_down') || shape === 'triangle_down') return 'arrowDown';
  if (shape === 'diamond' || shape === 'square') return 'square';
  return 'circle';
};

export function Chart({
  symbol = 'XAUUSD',
  height = 480,
  drawings = [],
  candles,
}: {
  symbol?: string;
  height?: number;
  drawings?: Drawing[];
  candles?: { time: number; open: number; high: number; low: number; close: number }[];
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const apiRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const overlayRefs = useRef<ISeriesApi<any>[]>([]);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      width: ref.current.clientWidth,
      height,
      layout: { background: { type: ColorType.Solid, color: '#0A0A0A' }, textColor: '#B8B8B8' },
      grid: { vertLines: { color: 'rgba(201,162,39,0.06)' }, horzLines: { color: 'rgba(201,162,39,0.06)' } },
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderColor: 'rgba(201,162,39,0.2)' },
      crosshair: { vertLine: { color: 'rgba(201,162,39,0.4)' }, horzLine: { color: 'rgba(201,162,39,0.4)' } },
    });
    const series = (chart as any).addCandlestickSeries({
      upColor: '#0E7A2C', downColor: '#B0140C', borderVisible: false, wickUpColor: '#0E7A2C', wickDownColor: '#B0140C',
    });
    apiRef.current = chart; seriesRef.current = series;

    const now = Math.floor(Date.now() / 1000);
    const seed = candles ?? Array.from({ length: 200 }, (_, i) => {
      const t = now - (200 - i) * 60 * 15;
      const o = 2300 + Math.sin(i / 7) * 30 + Math.random() * 4;
      const c = o + (Math.random() - 0.5) * 8;
      const h = Math.max(o, c) + Math.random() * 4;
      const l = Math.min(o, c) - Math.random() * 4;
      return { time: t as any, open: o, high: h, low: l, close: c };
    });
    series.setData(seed as any);
    const ro = new ResizeObserver(() => chart.applyOptions({ width: ref.current?.clientWidth }));
    ro.observe(ref.current);
    return () => { ro.disconnect(); chart.remove(); };
  }, [height, symbol, candles]);

  // Drawings overlay effect — runs whenever drawings change
  useEffect(() => {
    const chart = apiRef.current; const series = seriesRef.current;
    if (!chart || !series) return;
    // clear previous overlays
    overlayRefs.current.forEach(s => { try { (chart as any).removeSeries(s); } catch (_) {} });
    overlayRefs.current = [];

    const markers: any[] = [];
    for (const d of drawings) {
      if (d.type === 'marker') {
        markers.push({
          time: tsToTime(d.x) as any,
          position: (d.shape && d.shape.includes('down')) ? 'aboveBar' : 'belowBar',
          color: d.color || '#C9A227',
          shape: mapShape(d.shape),
          text: d.label || '',
        });
      } else if (d.type === 'line') {
        try {
          const ls = (chart as any).addLineSeries({
            color: d.color || '#C9A227',
            lineWidth: d.thickness || 1,
            priceLineVisible: false, lastValueVisible: false, crossHairMarkerVisible: false,
          });
          ls.setData([
            { time: tsToTime(d.x1) as any, value: d.y1 },
            { time: tsToTime(d.x2) as any, value: d.y2 },
          ]);
          overlayRefs.current.push(ls);
        } catch (e) { /* ignore individual draw failures */ }
      } else if (d.type === 'rect') {
        // Approximate a rectangle with two horizontal lines (top / bottom)
        try {
          const top = (chart as any).addLineSeries({ color: d.color || 'rgba(201,162,39,0.4)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
          const bot = (chart as any).addLineSeries({ color: d.color || 'rgba(201,162,39,0.4)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
          top.setData([{ time: tsToTime(d.x1) as any, value: Math.max(d.y1, d.y2) }, { time: tsToTime(d.x2) as any, value: Math.max(d.y1, d.y2) }]);
          bot.setData([{ time: tsToTime(d.x1) as any, value: Math.min(d.y1, d.y2) }, { time: tsToTime(d.x2) as any, value: Math.min(d.y1, d.y2) }]);
          overlayRefs.current.push(top, bot);
        } catch (e) { /* ignore */ }
      } else if (d.type === 'label') {
        markers.push({
          time: tsToTime(d.x) as any,
          position: 'aboveBar',
          color: d.color || '#C9A227',
          shape: 'square',
          text: d.text,
        });
      }
    }
    if (markers.length) {
      try { (series as any).setMarkers(markers.sort((a, b) => a.time - b.time)); } catch (e) {}
    }
  }, [drawings]);

  return <div ref={ref} className="w-full rounded-md border border-[rgba(201,162,39,0.15)]" />;
}

export function drawSignal(api: IChartApi | null, series: ISeriesApi<'Candlestick'> | null, sig: { time: number; price: number; kind: 'Buy Lion' | 'Sell Lion' | 'Buy Cub' | 'Sell Cub' | 'ARC' | 'BUMP' | 'DUMP' }) {
  if (!series) return;
  const isBuy = sig.kind.startsWith('Buy');
  (series as any).setMarkers([
    ...((series as any).markers?.() ?? []),
    {
      time: sig.time as any,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#0E7A2C' : '#B0140C',
      shape: sig.kind.includes('Lion') ? 'arrowUp' : 'circle',
      text: sig.kind,
    },
  ]);
}
