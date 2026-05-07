'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';
import { api, saveTokens } from '@/lib/api';
import { Logo } from '@/components/brand/Logo';

export default function RegisterPage() {
  const t = useTranslations('auth');
  const locale = useLocale();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(null); setBusy(true);
    try {
      const { data } = await api.post('/auth/register', {
        email, password, full_name: fullName, preferred_lang: locale,
      });
      saveTokens(data.access_token, data.refresh_token);
      router.push('/subscribe');
    } catch (e: any) { setErr(e?.response?.data?.detail || 'register_failed'); }
    finally { setBusy(false); }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-bg-primary p-6">
      <form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-[rgba(201,162,39,0.2)] bg-bg-secondary p-8 shadow-glow">
        <div className="mb-6 flex justify-center"><Logo /></div>
        <h2 className="mb-6 text-center text-xl text-gold">{t('create_account')}</h2>
        <label className="block">
          <span className="mb-1 block text-xs text-muted">{t('fullName')}</span>
          <input value={fullName} onChange={e=>setFullName(e.target.value)} required className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-2 text-sm text-[var(--text-primary)] focus:border-gold focus:outline-none"/>
        </label>
        <label className="mt-4 block">
          <span className="mb-1 block text-xs text-muted">{t('email')}</span>
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-2 text-sm focus:border-gold focus:outline-none"/>
        </label>
        <label className="mt-4 block">
          <span className="mb-1 block text-xs text-muted">{t('password')}</span>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={10} className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-2 text-sm focus:border-gold focus:outline-none"/>
        </label>
        {err && <p className="mt-3 text-xs text-bear">{err}</p>}
        <button type="submit" disabled={busy} className="mt-6 w-full rounded-md bg-gold py-2 text-bg-primary font-semibold hover:shadow-glow disabled:opacity-50">{busy ? '…' : t('register')}</button>
        <p className="mt-4 text-center text-xs text-muted">
          {t('already_have')} <Link href="/auth/login" className="text-gold underline">{t('login')}</Link>
        </p>
      </form>
    </div>
  );
}
