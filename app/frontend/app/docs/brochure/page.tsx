import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function BrochurePage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-4xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-4xl text-center">The Market Lion · أسد السوق</h1>
        <p className="text-center text-muted">Razan AI Trading Platform · Institutional analysis. Multi-school confluence. One platform.</p>

        <h2>Why The Market Lion?</h2>
        <ul>
          <li>89+ trading schools voting in one transparent confluence engine.</li>
          <li>120+ technical indicators across trend, momentum, volatility, volume, S/R, breadth.</li>
          <li>Real-time fundamental analysis: news, FOMC, NFP, CPI, OPEC, EIA, COT.</li>
          <li>Order flow + Bookmap heatmap with iceberg, absorption, sweep detection.</li>
          <li>Direct broker connection (Capital.com at launch) — no MetaTrader middleware.</li>
          <li>Auto and manual modes. Multi-layer risk management with daily/weekly/monthly stops.</li>
          <li>12 languages including Arabic RTL, instant switch with no reload.</li>
        </ul>

        <h2>Pricing</h2>
        <table>
          <thead><tr><th>Plan</th><th>Monthly</th><th>Limits</th></tr></thead>
          <tbody>
            <tr><td>Individual</td><td>2,000 SAR</td><td>1 user · 1 broker · 5 concurrent trades</td></tr>
            <tr><td>Institution</td><td>6,000 SAR</td><td>Up to 20 sub-users · multiple brokers · 50 concurrent trades · API access</td></tr>
          </tbody>
        </table>

        <h2>Compliance</h2>
        <p>Saudi PDPL + EU GDPR aligned. Risk disclosure prominently displayed in footer. Historical success rates always presented as Backtest + Walk-Forward — not promises.</p>
      </main>
      <Footer />
    </>
  );
}
