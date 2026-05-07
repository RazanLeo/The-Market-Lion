'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, saveTokens } from '@/lib/api';
import { Logo } from '@/components/brand/Logo';

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [need2fa, setNeed2fa] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(null); setBusy(true);
    try {
      const { data } = await api.post('/auth/login', {
        email, password, totp_code: totp || null,
      });
      // Verify the user has admin/super_admin role before sending them to /admin
      saveTokens(data.access_token, data.refresh_token);
      const me = await api.get('/users/me');
      if (!['admin', 'super_admin'].includes(me.data?.role)) {
        setErr('not_admin');
        return;
      }
      router.push('/admin');
    } catch (e: any) {
      const code = e?.response?.data?.detail;
      if (code === 'totp_required') { setNeed2fa(true); setErr(null); }
      else setErr(code || 'login_failed');
    } finally { setBusy(false); }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-bg-primary p-6">
      <form onSubmit={submit} className="w-full max-w-md rounded-2xl border-2 border-[rgba(201,162,39,0.4)] bg-bg-secondary p-8 shadow-glow">
        <div className="mb-4 flex justify-center"><Logo /></div>
        <div className="mb-6 text-center">
          <span className="inline-block px-3 py-1 text-[10px] uppercase tracking-widest bg-gold/10 border border-gold/30 text-gold rounded">
            Administrator console
          </span>
          <h2 className="mt-3 text-xl text-gold font-display">Admin Sign-in</h2>
          <p className="mt-1 text-xs text-muted">دخول إدارة المنصة فقط — مستقل عن دخول المستخدم</p>
        </div>

        <label className="block">
          <span className="mb-1 block text-xs text-muted">Admin email</span>
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required
            className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-2 text-sm focus:border-gold focus:outline-none" />
        </label>
        <label className="mt-4 block">
          <span className="mb-1 block text-xs text-muted">Password</span>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={10}
            className="w-full rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-2 text-sm focus:border-gold focus:outline-none" />
        </label>
        {need2fa && (
          <label className="mt-4 block">
            <span className="mb-1 block text-xs text-muted">2FA code (6 digits)</span>
            <input value={totp} onChange={e=>setTotp(e.target.value)} required pattern="[0-9]{6}"
              className="w-full tabular rounded-md border border-[rgba(201,162,39,0.2)] bg-bg-primary p-2 text-center text-lg focus:border-gold focus:outline-none" />
          </label>
        )}

        {err === 'not_admin' && <p className="mt-3 text-xs text-bear">This account is not an administrator. Use the regular sign-in.</p>}
        {err && err !== 'not_admin' && <p className="mt-3 text-xs text-bear">{err}</p>}

        <button type="submit" disabled={busy}
          className="mt-6 w-full rounded-md bg-gold py-2 text-bg-primary font-semibold hover:shadow-glow disabled:opacity-50">
          {busy ? '…' : 'Sign in to Admin'}
        </button>
        <p className="mt-4 text-center text-xs text-muted">
          User sign-in: <a href="/auth/login" className="text-gold underline">/auth/login</a>
        </p>
      </form>
    </div>
  );
}
