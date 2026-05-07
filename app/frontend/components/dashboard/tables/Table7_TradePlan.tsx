'use client';
import { useTranslations } from 'next-intl';

export function Table7_TradePlan({ plan }: { plan: any }) {
  const t = useTranslations('dashboard');
  const rows: [string, any][] = [
    ['Capital', plan?.balance || '—'],
    ['Risk %', plan?.risk_pct || '—'],
    ['Risk Amount $', plan?.risk_amount || '—'],
    ['Leverage', plan?.leverage || '—'],
    ['Lot size', plan?.lot || '—'],
    ['Asset', plan?.symbol || '—'],
    ['Side', plan?.side || '—'],
    ['Timeframe', plan?.tf || '—'],
    ['Entry', plan?.entry || '—'],
    ['TP1 (R 1:1)', plan?.tp1 || '—'],
    ['TP2 (R 1:2)', plan?.tp2 || '—'],
    ['TP3 (R 1:3)', plan?.tp3 || '—'],
    ['Final TP', plan?.final_tp || '—'],
    ['Stop Loss', plan?.sl || '—'],
    ['Trailing SL', 'Auto after each TP'],
    ['Pip $ value', plan?.pip_value || '—'],
    ['Expected profit @ TP1', plan?.expected_profit_at_tp1 || '—'],
    ['Expected loss @ SL', plan?.expected_loss_at_sl || '—'],
  ];
  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
      <h3 className="mb-3 text-sm font-semibold text-gold">7. {t('trade_plan')}</h3>
      <div className="grid gap-2 md:grid-cols-3 text-xs">
        {rows.map(([k,v]) => (<div key={k} className="flex justify-between rounded-md border border-[rgba(201,162,39,0.1)] bg-bg-primary px-3 py-1.5"><span className="text-muted">{k}</span><span className="tabular text-gold">{String(v)}</span></div>))}
      </div>
    </section>
  );
}
