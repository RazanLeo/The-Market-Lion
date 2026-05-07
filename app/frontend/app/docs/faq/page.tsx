import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

const QA: { q: string; a: string }[] = [
  { q: 'How do I link my Capital.com account?', a: 'Go to Settings → Broker links → Add account → choose Capital.com → enter your API key, identifier and password (Demo or Live). The platform will validate by fetching balance.' },
  { q: 'Is my broker key safe?', a: 'Yes. All broker keys are encrypted at rest using AES-GCM with a key stored in environment variables, never in plaintext in the database.' },
  { q: 'What is the Confluence Score?', a: 'A 0..100 weighted aggregate across 5 categories: Fundamental (20%), Basic Tools (30%), Schools (30%), Indicators (10%), Order Flow + Bookmap (10%). Trades open only when confluence ≥ threshold (default 80).' },
  { q: 'Can I run on Demo before going Live?', a: 'Yes. Capital.com Demo accounts are supported from day one. Toggle Demo/Live when adding your broker link.' },
  { q: 'How are historical success rates calculated?', a: 'They are computed on Backtest + Walk-Forward over historical data and are NOT a promise of future performance.' },
  { q: 'Which assets are supported?', a: 'XAU/USD, USOIL, Brent, EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, NZD/USD, USD/CAD, XAG/USD, DXY at launch. More via partner brokers later.' },
  { q: 'What payment methods are supported?', a: 'MADA (Saudi), Visa, Mastercard, PayPal, Apple Pay. PayTabs will be activated later.' },
  { q: 'Can I switch language without reload?', a: 'Yes — the language switcher at the top changes the UI instantly across 12 languages including Arabic with full RTL.' },
];

export default function FAQPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">FAQ / الأسئلة الشائعة</h1>
        <dl>{QA.map(({q, a}, i) => (
          <div key={i} className="my-3"><dt className="text-gold font-semibold">{q}</dt><dd className="mt-1">{a}</dd></div>
        ))}</dl>
      </main>
      <Footer />
    </>
  );
}
