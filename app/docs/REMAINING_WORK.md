# REMAINING_WORK.md — The Market Lion

> هذه القائمة هي العمل المتبقي بعد الجلسة الأولى من التنفيذ. النواة الكاملة للمنصة (Foundation + Backend + Frontend + 18 محلّلاً تطبيقياً + Capital.com adapter + 4 بوابات دفع + Admin + Static legal + CI/CD + Deploy script) **تم تسليمها**. الباقي توسعات وتعميقات لتحقيق الالتزام الحرفي بكل بنود البرومبت.

## تنفيذ مكتمل في الجلسة الأولى ✅

- [x] Monorepo + Docker Compose dev/prod + Caddy + .env.example + .gitignore
- [x] PostgreSQL + TimescaleDB + Redis + Alembic + Migration init كامل (16 جدول + 6 hypertables) + seed plans + feature toggles
- [x] Backend FastAPI: Auth + Argon2id + JWT + 2FA TOTP + Refresh + Logout + Sessions
- [x] Routers: users, subscriptions, payments, broker_links, analysis, signals, positions, admin, chat, webhooks, health
- [x] WebSocket realtime channels (analysis + news)
- [x] Voting Engine (Confluence Score 0..100 + decision)
- [x] Risk Engine (Position sizing + ATR-based SL + R-multiple targets + leverage selector + trailing rules)
- [x] News pipeline (NewsAPI ingest + sentiment + asset mapping)
- [x] Capital.com adapter (REST: session, account, positions, prices, open/close/modify; streaming poll-based)
- [x] Payments: HyperPay (MADA + Visa) + Stripe (cards + Apple Pay) + PayPal + webhooks (PayTabs disabled by default)
- [x] Frontend Next.js 14 + Tailwind + 12 لغة (en + ar كاملة، 10 placeholder تنسخ من en) + RTL + LangSwitcher + Brand tokens + Logo
- [x] Pages: Home, Login, Register, Dashboard, Subscribe, Admin, Legal (risk/terms/privacy)
- [x] Components: Header, Footer (with Risk Disclosure), TickersStrip, Logo, Chart (lightweight-charts), UserOptionsTable, AnalysisTables
- [x] 18 محلّلاً تطبيقياً كاملاً (production-quality):
  - Indicators (7): RSI, EMA Stack, MACD, VWAP, Bollinger, ATR Volatility, ADX
  - Schools (9): SMC, Wyckoff, Fib Retracement 61.8%, Elliott Basic, Supply/Demand, Killzones, Power of 3, OTE 61.8%, Pairs Z-Score
  - Flow (3): Volume Profile (POC/HVN/LVN), Order Flow Basic, Bookmap Basic
  - Fundamental (2): News Sentiment, FOMC/NFP Halt Gate
- [x] Confluence aggregator + decision policy
- [x] Backtest + Walk-Forward engine
- [x] Admin Console (dashboard + users + payments + audit + feature toggles + voting weights)
- [x] CI workflow (tests + builds + GHCR push) + Deploy workflow (SSH to DO Droplet) + bootstrap script

## عمل متبقٍ بترتيب الأولوية للجلسات القادمة

### الأولوية 1 — تكامل MVP الحقيقي (الجلسة 2)
- [ ] **بقية المحللات الـ 65+ مدرسة** — كل مدرسة تأخذ ~150 سطر تنفيذ + اختبارات. الترتيب الموصى:
  - Candlesticks Patterns Detector (60+ pattern via TA-Lib + custom multi-bar)
  - Dow Theory + Higher-High/Lower-Low Engine
  - Naked Trading + Pin Bar/Inside Bar/Outside Bar/Fakey
  - VSA (Tom Williams) — Stopping Volume / No Demand / Effort vs Result
  - Wyckoff Full (PS/SC/AR/ST/Spring/LPS/SOS/BC/UT/LPSY/DSTOP)
  - Elliott Wave Full (5-3 with Fibonacci validation)
  - Harmonic Patterns (Gartley, Butterfly, Bat, Crab, Shark, Cypher, AB=CD, 5-0, Three Drives)
  - Andrews Pitchfork
  - Point & Figure
  - Darvas Box
  - Weinstein Stage
  - Fractal/Chaos (Bill Williams) Alligator + Awesome
  - Turtle Trading (20-bar high/low + ATR sizing)
  - Hurst Cycles + FLD
  - DeMark Sequential & Combo
  - Kondratiev Wave
  - Market Profile (TPO + Value Area + IB)
  - Gann (Angles 1×1, Fan, Square of 9, Wheel)
  - Sacred Geometry
  - Renko / Heikin Ashi / Kagi / Three Line Break / Range Bars / Tick Charts (chart-mode signals)
  - Quant / Mean Reversion / Pairs Trading deeper
  - Intermarket Analysis (DXY↔Gold, SPX↔Bonds correlations)
  - COT report parser + extreme positioning
  - Options Flow + Put/Call Ratio + GEX
  - Market Breadth (A/D, McClellan, TRIN, BPI)
  - Seasonality
  - Mansfield RS
  - CANSLIM
  - Momentum (Driehaus, Antonacci Dual)
  - Gann Time analysis + Fibonacci Time Zones
  - LuxAlgo equivalents under Lion-prefixed names: Smart Money Flow, OverFlow, HyperWave, Confluence Meter, Sigmoid Trailing, Inertial Stochastic, BSL/SSL Map
  - KFOO equivalents: Lion ARC Breakout, Lion Whale Tracker, Lion Cloud RSI, Lion Buy/Sell Cub, Lion Buy/Sell Lion (Buy/Sell signals already wired in `signals.py`)
- [ ] **بقية المؤشرات الـ 100+** — TA-Lib wrapper + analyzer for each: Stochastic, Stochastic RSI, Williams %R, ROC, Awesome Oscillator, Momentum, MFI, Ultimate Oscillator, Aroon, Vortex, Coppock, Chande, Schaff Trend Cycle, KST, TSI, Fisher Transform, Keltner Channels, Donchian, Standard Deviation, Historical Volatility, Chaikin Volatility, Mass Index, Choppiness, Volatility Index, OBV, Accumulation/Distribution, Chaikin Money Flow, Klinger, Force Index, Ease of Movement, Volume Oscillator, NVI, PVI, VWAP, Anchored VWAP, CVD, Up/Down Volume, Fibonacci Fan/Time Zones/Arcs, Pivot Points (Standard, Fibonacci, Camarilla, Woodie, DeMark), Auto S/R, Ichimoku Cloud full system, Bollinger %B+Bandwidth, McClellan Oscillator, A/D Line, A/D Volume, High-Low Index, BPI, Coppock with EMA Filter, DeMarker, TPO Profile, Cumulative Delta, Iceberg detector.
- [ ] **News pipeline expansion**: Twitter/X polling (Trump, MBS, Fed governors), ForexFactory + Investing scraping, FRED API, EIA inventories, OPEC monthly, WGC reports, CFTC COT weekly. FinBERT model loaded in worker.
- [ ] **Bookmap real**: L2 stream از Capital.com (when available) + heatmap API for frontend.
- [ ] **TradingView Charting Library** licensed embed (replace lightweight-charts in chart panel).
- [ ] **Self-Learning RL loop**: post-trade weight update + XGBoost filter trained on closed trade history.
- [ ] **Email + 2FA email backup** (Resend) + welcome/invoice emails.
- [ ] **Stripe live webhook signature** verification end-to-end test.
- [ ] **Full localization for 10 remaining languages** (currently en + ar). pt-BR, pt-PT, es, fr, de, ru, tr, zh-CN, ja, ko via translation team review of en.json baseline.

### الأولوية 2 — تشديد الإنتاج (الجلسة 3)
- [ ] **Sentry + Prometheus + Grafana dashboards** wired from sample configs in `infra/`.
- [ ] **k6 load tests** for /api/v1/auth/login, /analysis/confluence, ws/analysis.
- [ ] **Playwright E2E** flows: register → login → 2FA setup → broker link demo → manual buy → position close.
- [ ] **Backtest UI** (page) with Plotly chart of equity curve + drawdown.
- [ ] **Walk-Forward report** generator (PDF) with monthly windows.
- [ ] **Pen test** — OWASP Top 10 + JWT replay + rate limit.
- [ ] **AML/KYC** flow for institution plan: document upload (S3) + manual admin review.

### الأولوية 3 — توسيع البروكرز (الجلسة 4)
- [ ] **Exness Partner-API negotiation** (business action by رزان) → adapter implementation when granted.
- [ ] **MT5 Connect Direct** alternative (if Exness partner-API unavailable).
- [ ] **Generic BrokerInterface** + adapters for IC Markets / Pepperstone / FxPro.

### الأولوية 4 — التوسعات الذكية (الجلسة 5+)
- [ ] **Embedded Chat AI** with full tool-calling (`get_user_context`, `explain_decision`, `generate_report`).
- [ ] **Mobile app** (React Native + Expo) — Phase 2.
- [ ] **PayTabs activation** when رزان completes the merchant subscription.

## ملاحظات تنفيذية

1. **الالتزام بعدم ذكر منافسين**: تم. أي مرجعية في الكود (داخل الـ docstrings) فقط.
2. **الإفصاح القانوني**: في الفوتر فقط (Footer.tsx) + سطر صغير في Subscribe (subscribe.small_disclaimer). لا يظهر في Dashboard أو في تقارير الصفقات الفردية.
3. **الشعار**: `frontend/public/brand/logo.jpg` نسخة من `LOGO_ORIGINAL.jpg`. مستخدم في Logo component فقط.
4. **CMA license + الكيان التجاري**: مهام رزان البزنس، خارج نطاق التنفيذ التقني.
5. **Capital.com epic mapping**: قائمة مبدئية في `capital.py::_symbol_to_epic` — يجب التحقق من القائمة الفعلية بعد الحصول على API key.
6. **Encryption key rotation**: تنفيذ شهري عبر Admin → System Settings (يضاف في الجلسة 3).
