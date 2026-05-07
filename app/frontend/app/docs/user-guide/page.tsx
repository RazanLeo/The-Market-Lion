import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function UserGuidePage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">User Guide / كتيب الاستخدام</h1>

        <h2>1. Accounts and 2FA</h2>
        <p>Each user has an isolated account. After registration, enable 2FA (Time-based OTP) from Settings.</p>

        <h2>2. Subscriptions</h2>
        <p>Two plans: Individual (1 user, 1 broker) — 2,000 SAR/mo. Institution (up to 20 sub-users, multiple brokers) — 6,000 SAR/mo.</p>

        <h2>3. Broker linking</h2>
        <p>Capital.com is supported at launch (Demo + Live). Provide your API key, identifier and password in Settings → Broker links. Keys are AES-GCM encrypted.</p>

        <h2>4. Trader options table</h2>
        <p>Choose: Asset, Account balance, Risk %, Timeframe, Trade mode (Manual/Auto), Broker account.</p>

        <h2>5. Eight analysis tables</h2>
        <ul>
          <li>Fundamental — news, economic events, sentiment, FOMC/NFP halt gate.</li>
          <li>Basic tools — Pivot HL, Support/Resistance, Trendlines, EMAs/SMAs, Channels, Chart patterns, Candlestick patterns, SMC/ICT, Killzones, Supply/Demand, OB, Accumulation/Distribution, Smart Money, Fibonacci, RSI Divergence, Bookmap reader, ARC, Liquidity Theory, Stop hunts, Buy/Sell Cub, Buy/Sell Lion.</li>
          <li>Schools — 89+ trading schools with weighted voting.</li>
          <li>Indicators — 120+ technical indicators by category.</li>
          <li>Flow / Bookmap — heatmap, CVD, iceberg, absorption, sweep.</li>
          <li>Decision — final BUY/SELL/WAIT with Confluence Score.</li>
          <li>Trade plan — entry, SL, TP1/TP2/TP3/Final TP, lot size, leverage, pip values, P/L expectations.</li>
        </ul>

        <h2>6. Bot mode vs manual</h2>
        <p>In Auto mode, the bot opens trades when Confluence ≥ 80% and no Red News in the next 30 minutes. Manual mode gives BUY/SELL buttons that execute the current proposed plan.</p>

        <h2>7. Risk management</h2>
        <p>Position sizing uses ATR-based SL distance, respects daily / weekly / monthly loss limits, and applies trailing SL: breakeven after TP1, lock 1R after TP2, ATR Trailing after TP3.</p>

        <h2>8. AI chat</h2>
        <p>Ask the embedded AI to explain the decision, summarize news, or generate a daily report. Function calls are scoped to your account only.</p>
      </main>
      <Footer />
    </>
  );
}
