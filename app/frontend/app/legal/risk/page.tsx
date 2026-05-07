import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function RiskPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">Risk Disclosure</h1>

        <div className="border border-bear/40 bg-bear/5 p-4 rounded my-6">
          <p className="font-semibold text-bear">Trading carries substantial risk and may result in the total loss of capital. Past performance is not a guarantee of future results.</p>
        </div>

        <h2>1. Nature of leveraged trading</h2>
        <p>CFDs (Contracts for Difference), forex, commodities futures, and other leveraged instruments allow you to gain market exposure many times larger than your deposit. Leverage amplifies both profit and loss; small adverse price moves can wipe out your entire account.</p>

        <h2>2. The Market Lion is an analysis tool, not advice</h2>
        <p>The platform aggregates analysis from 140+ schools, 135+ indicators, and 20+ tools, plus live fundamental data, to produce a Confluence Score and trade plans. <strong>This is decision-support, not personalised investment advice.</strong> You alone choose whether to act on any signal.</p>

        <h2>3. Historical performance</h2>
        <p>Any historical success rate, win rate, or P/L number shown anywhere on the platform is the output of <strong>Backtest + Walk-Forward analysis on historical data.</strong> Backtests have well-known limitations: survivorship bias, look-ahead bias, slippage assumptions, and overfitting. Live results often differ. Historical numbers are <strong>not</strong> a promise or projection of future returns.</p>

        <h2>4. Specific risk factors</h2>
        <ul>
          <li><strong>Market risk</strong> — prices move against you; gaps and spreads widen during news.</li>
          <li><strong>Liquidity risk</strong> — illiquid sessions amplify slippage.</li>
          <li><strong>Counter-party risk</strong> — your broker may default, freeze withdrawals, or restrict trading.</li>
          <li><strong>Technology risk</strong> — internet outages, broker API failures, exchange halts.</li>
          <li><strong>Regulatory risk</strong> — trading rules vary by jurisdiction and may change suddenly.</li>
          <li><strong>Algorithmic risk</strong> — past algorithm performance does not guarantee future performance; the self-learning loop adjusts weights based on recent trades and may produce unexpected behaviour.</li>
        </ul>

        <h2>5. Bot mode requires your continuous oversight</h2>
        <p>When you enable auto-execution via a linked broker, the platform places trades on your behalf within the parameters you set (risk %, daily trade cap, allowed symbols). You retain full responsibility for monitoring the bot and disabling it whenever you choose. The platform sets per-trade risk caps but cannot prevent all losses.</p>

        <h2>6. Capital you should risk</h2>
        <p>Never trade money you cannot afford to lose. Do not borrow to fund a trading account. Treat trading capital as venture-style risk capital.</p>

        <h2>7. Educational use</h2>
        <p>If you are new to trading, use Demo / Paper-trading mode for at least 90 days before risking real capital, and complete the User Guide.</p>

        <hr />

        <h2>عربي — إفصاح المخاطر</h2>

        <div className="border border-bear/40 bg-bear/5 p-4 rounded my-6">
          <p className="font-semibold text-bear">التداول ينطوي على مخاطر كبيرة وقد يؤدّي إلى خسارة رأس المال بالكامل. الأداء السابق ليس ضماناً للأداء المستقبلي.</p>
        </div>

        <h3>١. طبيعة التداول بالرافعة</h3>
        <p>عقود الفروقات (CFDs) والفوركس وعقود السلع الآجلة وغيرها من الأدوات ذات الرافعة تتيح لك مكشوفاً يفوق إيداعك بأضعاف. الرافعة تضخّم الربح والخسارة معاً؛ تحرّكات بسيطة عكسية قد تمحو كامل حسابك.</p>

        <h3>٢. «أسد السوق» أداة تحليل، وليست نصيحة</h3>
        <p>تجمع المنصّة تحليل 140 مدرسة و135 مؤشّراً و20 أداة وبيانات أساسية حيّة لتُنتج درجة Confluence وخطط تداول. <strong>هذا دعم قرار وليس نصيحة استثمارية شخصية.</strong> أنت وحدك تختار التصرّف بأي إشارة.</p>

        <h3>٣. الأداء التاريخي</h3>
        <p>أيّ نسبة نجاح أو ربح/خسارة تاريخية معروضة في المنصّة هي نتاج <strong>Backtest + Walk-Forward على بيانات تاريخية</strong>. للاختبار الخلفي قيود معروفة (تحيّز البقاء، النظر إلى الأمام، افتراضات الانزلاق، الإفراط في الملاءمة). النتائج الحيّة قد تختلف. الأرقام التاريخية <strong>ليست</strong> وعداً بنتائج مستقبلية.</p>

        <h3>٤. عوامل مخاطر محدّدة</h3>
        <ul>
          <li>مخاطر السوق — حركة الأسعار العكسية وفجوات الأخبار</li>
          <li>مخاطر السيولة — جلسات قليلة السيولة تضخّم الانزلاق</li>
          <li>مخاطر الطرف المقابل — تعثّر الوسيط أو تجميد السحب</li>
          <li>مخاطر التقنية — انقطاع الإنترنت، أعطال API، توقّف التداول</li>
          <li>مخاطر تنظيمية — قواعد التداول تختلف وتتغيّر</li>
          <li>مخاطر خوارزمية — الأداء السابق لا يضمن المستقبل، وحلقة التعلّم الذاتي قد تنتج سلوكاً غير متوقّع</li>
        </ul>

        <h3>٥. وضع البوت يتطلّب إشرافك المستمرّ</h3>
        <p>عند تفعيل التنفيذ الآلي عبر وسيط مربوط، تنفّذ المنصّة الصفقات نيابةً عنك ضمن الحدود التي تضعها. تظلّ المسؤولية الكاملة عليك لمراقبة البوت وإيقافه متى شئت.</p>

        <h3>٦. رأس المال الذي تستحقّ المخاطرة به</h3>
        <p>لا تتداول إلا بأموال تستطيع فقدانها. لا تقترض لتمويل حساب تداول. اعتبر رأس مال التداول رأس مال مخاطرة.</p>

        <h3>٧. الاستخدام التعليمي</h3>
        <p>إن كنتَ مبتدئاً، استخدم وضع التجريبي/Paper trading لمدّة 90 يوماً على الأقل قبل المخاطرة برأس مال حقيقي، وأكمل دليل المستخدم.</p>
      </main>
      <Footer />
    </>
  );
}
