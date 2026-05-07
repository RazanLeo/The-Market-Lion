import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function QuickstartPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">Quickstart / إرشادات سريعة</h1>
        <ol>
          <li><strong>Sign up</strong> — register with email + password ≥ 10 chars. Optional: enable 2FA in Settings.</li>
          <li><strong>Subscribe</strong> — choose Individual (2,000 SAR/mo) or Institution (6,000 SAR/mo). Pay via MADA, Visa/MC, PayPal, or Apple Pay.</li>
          <li><strong>Link broker</strong> — Settings → Broker links → Capital.com → enter Demo (or Live) API key + identifier + password.</li>
          <li><strong>Open dashboard</strong> — pick asset (XAU/USD by default), set risk %, choose timeframe, choose Manual or Auto Bot mode.</li>
          <li><strong>Watch the tables</strong> — Fundamental → Basics → Schools → Indicators → Flow → Decision. The Confluence Score updates every minute.</li>
          <li><strong>Execute</strong> — Manual: click BUY or SELL. Auto: press Start Bot — the platform opens trades when confluence ≥ 80% and risk allows.</li>
          <li><strong>Manage positions</strong> — view in Trades tab. Trailing SL moves automatically after each TP hit.</li>
        </ol>
      </main>
      <Footer />
    </>
  );
}
