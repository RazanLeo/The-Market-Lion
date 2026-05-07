import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function TermsPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">Terms of Service</h1>

        <h2>1. Acceptance of terms</h2>
        <p>By creating an account or using The Market Lion ("the platform", "we", "us") you accept these Terms of Service in full. If you do not accept any part of these terms, you must not use the platform.</p>

        <h2>2. Eligibility</h2>
        <p>You must be at least 18 years old and legally capable of entering into binding contracts in your jurisdiction. The platform is not directed at residents of jurisdictions where its use would be unlawful.</p>

        <h2>3. Nature of the service</h2>
        <p>The Market Lion is an analytical and educational platform. It provides AI-driven market analysis, signals, and risk-management calculations. <strong>It does NOT provide personalised investment advice, asset management, or portfolio management.</strong> All trading decisions are taken by the user.</p>

        <h2>4. Account and security</h2>
        <p>You are responsible for maintaining the confidentiality of your account credentials and 2FA tokens, and for all activity that occurs under your account. You must notify support immediately of any unauthorised use.</p>

        <h2>5. Subscription and payment</h2>
        <p>Subscription fees are billed monthly in advance. Plans: Individual (2,000 SAR / month), Institution (6,000 SAR / month). You may cancel at any time; no refunds are issued for the current billing period.</p>

        <h2>6. Broker integration</h2>
        <p>Linking a broker account (e.g. Capital.com) is voluntary. The platform stores broker API keys encrypted at rest using AES-GCM. You authorise the platform to place trades on your linked broker account only when the bot mode is explicitly enabled by you, within risk limits you set yourself.</p>

        <h2>7. Prohibited use</h2>
        <ul>
          <li>Unlawful activity, market manipulation, or money laundering</li>
          <li>Reverse-engineering, scraping, or redistributing the platform's content</li>
          <li>Attempting to access other users' data or breach security controls</li>
          <li>Using automated abuse to bypass rate limits</li>
        </ul>

        <h2>8. Intellectual property</h2>
        <p>All content, code, designs, trademarks, and the multi-school voting algorithm are the property of The Market Lion and its founder. Your subscription grants you a non-exclusive, non-transferable licence for personal use only.</p>

        <h2>9. Risk and liability</h2>
        <p>Trading carries substantial risk. We do not guarantee any profit. Historical performance is shown as Backtest + Walk-Forward — it is not a promise of future results. To the maximum extent permitted by law, our liability is limited to the fees you paid in the preceding three months.</p>

        <h2>10. Termination</h2>
        <p>We may suspend or terminate accounts that violate these terms, with or without notice. You may close your account at any time from Settings.</p>

        <h2>11. Governing law</h2>
        <p>These terms are governed by the laws of the Kingdom of Saudi Arabia. Disputes shall be settled in the competent Saudi courts.</p>

        <h2>12. Contact</h2>
        <p>Questions: <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a>.</p>

        <hr />
        <h2>عربي — شروط الاستخدام</h2>

        <h3>١. القبول</h3>
        <p>بإنشاء حساب أو استخدام «أسد السوق» («المنصّة»، «نحن») فإنك تقبل هذه الشروط بالكامل. إن لم تقبل أيّ جزء منها فلا يحقّ لك استخدام المنصّة.</p>

        <h3>٢. الأهلية</h3>
        <p>يجب أن تكون قد بلغت 18 عاماً وأن تكون أهلاً قانونياً لإبرام عقود ملزمة في نطاق ولايتك القضائية.</p>

        <h3>٣. طبيعة الخدمة</h3>
        <p>«أسد السوق» منصّة تحليلية وتعليمية تقدّم تحليلاً وإشارات وحسابات إدارة مخاطر مدعومة بالذكاء الاصطناعي. <strong>لا تقدّم نصيحة استثمارية شخصية ولا إدارة محافظ.</strong> جميع قرارات التداول يتّخذها المستخدم بنفسه.</p>

        <h3>٤. الحساب والأمان</h3>
        <p>أنت مسؤول عن سرّية بيانات حسابك ورموز 2FA وكل نشاط يتم من حسابك. عليك إبلاغ الدعم فوراً عند أي استخدام غير مصرّح به.</p>

        <h3>٥. الاشتراك والدفع</h3>
        <p>تُحصَّل رسوم الاشتراك شهرياً مقدّماً. الخطط: الفردي 2,000 ر.س/شهر، المؤسسي 6,000 ر.س/شهر. يمكنك الإلغاء في أي وقت دون استرجاع الفترة الحالية.</p>

        <h3>٦. ربط الوسيط</h3>
        <p>ربط حساب الوسيط (مثل Capital.com) اختياري. تُحفظ مفاتيح API للوسطاء مشفّرة بـ AES-GCM. تُفوِّض المنصّة بتنفيذ الصفقات على حسابك المرتبط فقط عند تفعيلك لوضع البوت صراحةً وضمن حدود المخاطر التي تحدّدها.</p>

        <h3>٧. الاستخدام المحظور</h3>
        <ul>
          <li>الأنشطة غير القانونية، التلاعب بالسوق، أو غسل الأموال</li>
          <li>الهندسة العكسية أو السحب الآلي أو إعادة توزيع المحتوى</li>
          <li>محاولة الوصول لبيانات مستخدمين آخرين أو خرق ضوابط الأمان</li>
          <li>تجاوز حدود المعدّل عبر الأتمتة المسيئة</li>
        </ul>

        <h3>٨. الملكية الفكرية</h3>
        <p>جميع المحتوى والشفرة والتصاميم والعلامات وخوارزمية محرّك التصويت ملك حصري لـ«أسد السوق» ومؤسِّستها. اشتراكك يمنحك ترخيصاً غير حصري وغير قابل للنقل للاستخدام الشخصي فقط.</p>

        <h3>٩. المخاطر والمسؤولية</h3>
        <p>التداول ينطوي على مخاطر كبيرة. لا نضمن أي ربح. الأداء السابق المعروض هو Backtest + Walk-Forward وليس وعداً بنتائج مستقبلية. مسؤوليتنا محصورة بالرسوم المدفوعة خلال آخر ثلاثة أشهر.</p>

        <h3>١٠. الإنهاء</h3>
        <p>يحقّ لنا تعليق أو إنهاء الحسابات المخالفة بإشعار أو دونه. ويمكنك إغلاق حسابك متى شئت من الإعدادات.</p>

        <h3>١١. القانون الحاكم</h3>
        <p>تخضع هذه الشروط لأنظمة المملكة العربية السعودية، وتختص المحاكم السعودية بالفصل في أي نزاع.</p>
      </main>
      <Footer />
    </>
  );
}
