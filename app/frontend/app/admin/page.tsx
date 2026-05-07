'use client';
import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { api } from '@/lib/api';

export default function AdminPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [audit, setAudit] = useState<any[]>([]);
  const [toggles, setToggles] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    api.get('/admin/dashboard').then(r => setStats(r.data));
    api.get('/admin/users').then(r => setUsers(r.data || []));
    api.get('/admin/payments').then(r => setPayments(r.data || []));
    api.get('/admin/audit').then(r => setAudit(r.data || []));
    api.get('/admin/feature-toggles').then(r => setToggles(r.data || []));
  }, []);

  return (
    <>
      <Header />
      <main className="mx-auto max-w-[1500px] px-6 py-6 space-y-6">
        <h1 className="text-2xl text-gold font-display">Admin Console</h1>

        {stats && (
          <section className="grid gap-4 md:grid-cols-3">
            <Stat label="Users" value={stats.users}/>
            <Stat label="Active subs" value={stats.active_subscriptions}/>
            <Stat label="Successful payments" value={stats.successful_payments}/>
          </section>
        )}

        <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
          <h2 className="mb-2 text-gold">Users</h2>
          <table className="w-full text-xs">
            <thead><tr>{['Email','Role','Status','Lang','Created'].map(h => <th key={h} className="px-2 py-1 text-start text-muted font-normal">{h}</th>)}</tr></thead>
            <tbody>{users.map(u => <tr key={u.id} className="border-t border-[rgba(201,162,39,0.05)]"><td className="px-2 py-1">{u.email}</td><td className="px-2 py-1">{u.role}</td><td className="px-2 py-1">{u.status}</td><td className="px-2 py-1">{u.lang}</td><td className="px-2 py-1">{u.created?.slice(0,10)}</td></tr>)}</tbody>
          </table>
        </section>

        <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
          <h2 className="mb-2 text-gold">Feature toggles</h2>
          {toggles.map(t => (
            <div key={t.key} className="flex items-center justify-between border-b border-[rgba(201,162,39,0.05)] py-1.5 text-sm">
              <span>{t.key}</span>
              <button onClick={async () => { await api.post('/admin/feature-toggles', { key: t.key, enabled: !t.enabled }); setToggles(prev => prev.map(x => x.key === t.key ? { ...x, enabled: !x.enabled } : x)); }} className={`rounded-md px-3 py-1 text-xs ${t.enabled ? 'bg-bull text-white' : 'bg-bear text-white'}`}>{t.enabled ? 'ON' : 'OFF'}</button>
            </div>
          ))}
        </section>

        <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
          <h2 className="mb-2 text-gold">Payments</h2>
          <table className="w-full text-xs">
            <thead><tr>{['Provider','Amount','Status','Time'].map(h => <th key={h} className="px-2 py-1 text-start text-muted font-normal">{h}</th>)}</tr></thead>
            <tbody>{payments.map(p => <tr key={p.id} className="border-t border-[rgba(201,162,39,0.05)]"><td className="px-2 py-1">{p.provider}</td><td className="px-2 py-1 tabular">{p.amount} {p.currency}</td><td className="px-2 py-1">{p.status}</td><td className="px-2 py-1">{p.ts?.slice(0,16)}</td></tr>)}</tbody>
          </table>
        </section>

        <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
          <h2 className="mb-2 text-gold">Audit log</h2>
          <table className="w-full text-xs">
            <thead><tr>{['Time','Role','Action','Resource'].map(h => <th key={h} className="px-2 py-1 text-start text-muted font-normal">{h}</th>)}</tr></thead>
            <tbody>{audit.map(a => <tr key={a.id} className="border-t border-[rgba(201,162,39,0.05)]"><td className="px-2 py-1">{a.ts?.slice(0,16)}</td><td className="px-2 py-1">{a.actor_role}</td><td className="px-2 py-1">{a.action}</td><td className="px-2 py-1">{a.resource}/{a.resource_id || ''}</td></tr>)}</tbody>
          </table>
        </section>
      </main>
      <Footer />
    </>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return <div className="rounded-md border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4 text-center"><div className="text-3xl text-gold tabular">{value ?? '—'}</div><div className="text-xs text-muted mt-1">{label}</div></div>;
}
