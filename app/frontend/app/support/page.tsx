'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { api } from '@/lib/api';

export default function SupportPage() {
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('sending');
    try {
      await api.post('/support/contact', { email, subject, message });
      setStatus('sent');
      setEmail(''); setSubject(''); setMessage('');
    } catch {
      setStatus('error');
    }
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-2xl px-6 py-12">
        <h1 className="text-gold font-display text-3xl mb-2">Support</h1>
        <p className="text-muted mb-6">We respond within one business day. For account-billing issues attach your subscription ID.</p>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1">Email</label>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full bg-bg-secondary border border-[rgba(201,162,39,0.2)] rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm mb-1">Subject</label>
            <input type="text" required minLength={2} maxLength={200} value={subject} onChange={e => setSubject(e.target.value)}
              className="w-full bg-bg-secondary border border-[rgba(201,162,39,0.2)] rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm mb-1">Message</label>
            <textarea required minLength={10} maxLength={5000} rows={6} value={message} onChange={e => setMessage(e.target.value)}
              className="w-full bg-bg-secondary border border-[rgba(201,162,39,0.2)] rounded px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={status === 'sending'}
            className="bg-gold text-black font-semibold px-6 py-2 rounded disabled:opacity-50">
            {status === 'sending' ? 'Sending…' : 'Send message'}
          </button>
          {status === 'sent' && <p className="text-bull text-sm">Message received. We will reply to {email}.</p>}
          {status === 'error' && <p className="text-bear text-sm">Something went wrong. Email us directly at razan.tawfiq@gmail.com.</p>}
        </form>

        <div className="mt-10 text-sm text-muted">
          <p>Direct email: <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a></p>
          <hr className="my-6 border-[rgba(201,162,39,0.15)]" />
          <h2 className="text-gold text-lg mb-2">عربي</h2>
          <p>للدعم الفني وأسئلة الفوترة وتفعيل الحساب، عبّئ النموذج أعلاه أو راسل: <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a>. نردّ خلال يوم عمل واحد. أرفق رقم الاشتراك إن كان السؤال متعلّقاً بالفوترة.</p>
        </div>
      </main>
      <Footer />
    </>
  );
}
