'use client';
import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { api } from '@/lib/api';

export default function SubscribePage() {
  const t = useTranslations('subscribe');
  const [plans, setPlans] = useState<any[]>([]);
  useEffect(() => { api.get('/subscriptions/plans').then(r => setPlans(r.data || [])).catch(() => {}); }, []);

  async function checkout(plan_code: string, provider: string) {
    try {
      const r = await api.post('/payments/checkout', { plan_code, provider });
      if (r.data?.redirect_url) window.location.href = r.data.redirect_url;
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'payment_failed');
    }
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-[1100px] px-6 py-12">
        <h1 className="mb-2 text-center font-display text-3xl text-gold">{t('title')}</h1>
        <p className="mb-8 text-center text-xs text-muted">{t('small_disclaimer')}</p>
        <div className="grid gap-6 md:grid-cols-2">
          {plans.map((p) => (
            <div key={p.code} className="rounded-2xl border border-[rgba(201,162,39,0.25)] bg-bg-secondary p-6 hover:shadow-glow">
              <h3 className="mb-1 text-2xl text-gold font-display">{p.name_ar} / {p.name_en}</h3>
              <p className="mb-4 text-3xl tabular text-[var(--text-primary)]">{p.monthly_price.toLocaleString()} {p.currency}<span className="text-sm text-muted">{t('monthly')}</span></p>
              <ul className="mb-4 space-y-1 text-xs text-muted">
                {Object.entries(p.features || {}).map(([k, v]) => <li key={k}>• {k}: {String(v)}</li>)}
              </ul>
              <div className="grid gap-2">
                <button onClick={() => checkout(p.code, 'mada')} className="rounded-md bg-gold py-2 text-sm font-semibold text-bg-primary hover:shadow-glow">MADA</button>
                <button onClick={() => checkout(p.code, 'visa_hyperpay')} className="rounded-md border border-gold py-2 text-sm text-gold">Visa / Mastercard (HyperPay)</button>
                <button onClick={() => checkout(p.code, 'stripe')} className="rounded-md border border-gold py-2 text-sm text-gold">Stripe (intl. cards + Apple Pay)</button>
                <button onClick={() => checkout(p.code, 'paypal')} className="rounded-md border border-gold py-2 text-sm text-gold">PayPal</button>
                <button onClick={() => checkout(p.code, 'applepay')} className="rounded-md border border-gold py-2 text-sm text-gold">Apple Pay</button>
              </div>
            </div>
          ))}
        </div>
      </main>
      <Footer />
    </>
  );
}
