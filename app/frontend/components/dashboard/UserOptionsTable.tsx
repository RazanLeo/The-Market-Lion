'use client';
import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

const ASSETS = ['XAUUSD','USOIL','BRENT','EURUSD','GBPUSD','USDJPY','USDCHF','AUDUSD','NZDUSD','USDCAD','XAGUSD','DXY'];
const TFS = ['1M','5M','15M','30M','1H','4H'];

export function UserOptionsTable({ onChange }: { onChange?: (state: any) => void }) {
  const t = useTranslations('dashboard');
  const [symbol, setSymbol] = useState('XAUUSD');
  const [balance, setBalance] = useState<number>(10000);
  const [riskPct, setRiskPct] = useState<number>(1);
  const [tf, setTf] = useState('15M');
  const [mode, setMode] = useState<'manual' | 'auto'>('manual');
  const [brokers, setBrokers] = useState<any[]>([]);
  const [brokerId, setBrokerId] = useState<string>('');

  const refTf = referenceTf(tf);

  useEffect(() => { onChange?.({ symbol, balance, riskPct, tf, refTf, mode, brokerId }); }, [symbol, balance, riskPct, tf, refTf, mode, brokerId, onChange]);

  useEffect(() => {
    api.get('/broker-links').then(r => setBrokers(r.data || [])).catch(() => {});
  }, []);

  const riskAmount = (balance * riskPct / 100).toFixed(2);

  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
      <h3 className="mb-3 text-sm font-semibold text-gold">{t('your_options')}</h3>
      <div className="grid gap-3 md:grid-cols-4">
        <Field label={t('asset')}>
          <select value={symbol} onChange={e=>setSymbol(e.target.value)} className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary px-2 py-1.5 text-sm">
            {ASSETS.map(a => <option key={a}>{a}</option>)}
          </select>
        </Field>
        <Field label={t('balance')}>
          <input type="number" min={50} step={50} value={balance} onChange={e=>setBalance(parseFloat(e.target.value)||0)} className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary px-2 py-1.5 text-sm tabular"/>
        </Field>
        <Field label={t('risk_pct')}>
          <select value={riskPct} onChange={e=>setRiskPct(parseFloat(e.target.value))} className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary px-2 py-1.5 text-sm">
            {[1,1.5,2,2.5,3,4,5,6,7,8,9,10].map(p => <option key={p}>{p}</option>)}
          </select>
        </Field>
        <Field label={t('risk_amount')}>
          <div className="rounded-md border border-[rgba(201,162,39,0.1)] bg-bg-primary px-2 py-1.5 text-sm tabular text-gold">{riskAmount}</div>
        </Field>
        <Field label={t('tf')}>
          <select value={tf} onChange={e=>setTf(e.target.value)} className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary px-2 py-1.5 text-sm">
            {TFS.map(f => <option key={f}>{f}</option>)}
          </select>
        </Field>
        <Field label={t('ref_tf')}>
          <div className="rounded-md border border-[rgba(201,162,39,0.1)] bg-bg-primary px-2 py-1.5 text-sm text-muted">{refTf}</div>
        </Field>
        <Field label={t('trade_mode')}>
          <div className="flex gap-2">
            {(['manual','auto'] as const).map(m => (
              <button key={m} type="button" onClick={()=>setMode(m)} className={`flex-1 rounded-md border px-2 py-1.5 text-xs ${mode===m ? 'border-gold bg-[rgba(201,162,39,0.1)] text-gold' : 'border-[rgba(201,162,39,0.15)] text-muted'}`}>
                {m === 'manual' ? t('manual') : t('auto')}
              </button>
            ))}
          </div>
        </Field>
        <Field label="Broker">
          <select value={brokerId} onChange={e=>setBrokerId(e.target.value)} className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary px-2 py-1.5 text-sm">
            <option value="">— select —</option>
            {brokers.map(b => <option key={b.id} value={b.id}>{b.broker} {b.account_login} ({b.account_type})</option>)}
          </select>
        </Field>
      </div>

      {mode === 'manual' ? (
        <div className="mt-4 grid gap-2 md:grid-cols-2">
          <button className="rounded-md bg-bull py-2 text-sm font-semibold text-white hover:opacity-90" onClick={()=>placeOrder(brokerId, symbol, 'buy', riskPct, tf)}>{t('buy').toUpperCase()}</button>
          <button className="rounded-md bg-bear py-2 text-sm font-semibold text-white hover:opacity-90" onClick={()=>placeOrder(brokerId, symbol, 'sell', riskPct, tf)}>{t('sell').toUpperCase()}</button>
        </div>
      ) : (
        <div className="mt-4">
          <button className="w-full rounded-md bg-gold py-2 text-sm font-bold text-bg-primary hover:shadow-glow" onClick={()=>toggleBot(brokerId, true)}>{t('start_bot')}</button>
          <button className="mt-2 w-full rounded-md border border-[rgba(201,162,39,0.3)] py-2 text-sm text-gold" onClick={()=>toggleBot(brokerId, false)}>{t('stop_bot')}</button>
        </div>
      )}
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] text-muted">{label}</span>
      {children}
    </label>
  );
}

function referenceTf(tf: string): string {
  return ({ '1M':'15M','5M':'1H','15M':'4H','30M':'4H','1H':'1D','4H':'1W' } as Record<string,string>)[tf] ?? '4H';
}

async function placeOrder(brokerId: string, symbol: string, side: 'buy'|'sell', risk: number, tf: string) {
  if (!brokerId) { alert('Select a broker first'); return; }
  try {
    const r = await api.post('/trades/manual', { broker_account_id: brokerId, symbol, side, risk_pct: risk, tf });
    alert(`Order opened: ticket ${r.data?.deal?.dealReference || r.data?.deal?.dealId}`);
  } catch (e: any) {
    alert(e?.response?.data?.detail || 'open_failed');
  }
}

async function toggleBot(brokerId: string, enable: boolean) {
  if (!brokerId) { alert('Select a broker first'); return; }
  await api.post('/trades/auto/toggle', { broker_account_id: brokerId, enable });
}
