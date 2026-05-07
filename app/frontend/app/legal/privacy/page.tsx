import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">Privacy Policy</h1>

        <p>We respect your privacy. This policy explains what data we collect, how we use it, and the rights you have over it. The Market Lion complies with the Saudi Personal Data Protection Law (PDPL) and the EU General Data Protection Regulation (GDPR).</p>

        <h2>1. Data we collect</h2>
        <ul>
          <li><strong>Account data</strong> — full name, email, hashed password, optional phone, language and timezone preferences.</li>
          <li><strong>Trading preferences</strong> — symbols watched, timeframes, risk percentage, notification settings.</li>
          <li><strong>Broker keys</strong> — when you link Capital.com or another broker, the API key is encrypted at rest with AES-GCM. Plain-text keys are never stored or logged.</li>
          <li><strong>Usage telemetry</strong> — page views, feature interactions, error reports. Aggregated and anonymous.</li>
          <li><strong>Operational logs</strong> — request IPs, user agents, session timestamps. Retained 90 days for security.</li>
          <li><strong>Trade records</strong> — entries, exits, PL, the confluence reasoning for each signal. Retained for the lifetime of the account plus 7 years for regulatory compliance.</li>
        </ul>

        <h2>2. How we use your data</h2>
        <ul>
          <li>To provide the analysis, signals, and bot execution you subscribe to</li>
          <li>To bill you and prevent fraud</li>
          <li>To improve the platform's accuracy via the self-learning weight loop (training data is aggregated and de-identified)</li>
          <li>To comply with anti-money-laundering and KYC requirements</li>
          <li>To respond to support requests</li>
        </ul>

        <h2>3. Sharing</h2>
        <p>We share data only with:</p>
        <ul>
          <li><strong>Payment processors</strong> (HyperPay, Stripe, PayPal) — only the minimum required for billing</li>
          <li><strong>Brokers you explicitly link</strong> — only the API calls you authorise</li>
          <li><strong>Hosting and monitoring providers</strong> (DigitalOcean, Sentry) — under contractual data-protection obligations</li>
          <li><strong>Authorities</strong> — only when legally compelled, and we will notify you unless prohibited by law</li>
        </ul>
        <p>We never sell your data.</p>

        <h2>4. Your rights</h2>
        <p>You have the right to:</p>
        <ul>
          <li>Access a copy of all personal data we hold about you</li>
          <li>Rectify inaccurate data</li>
          <li>Erase your data when it is no longer needed</li>
          <li>Object to specific processing</li>
          <li>Port your data to another provider</li>
          <li>Withdraw consent at any time</li>
        </ul>
        <p>Submit any request to <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a>. We respond within 30 days.</p>

        <h2>5. Security</h2>
        <p>Passwords are hashed with Argon2id. Broker API keys are encrypted with AES-GCM. Sessions use HttpOnly secure cookies. Two-factor authentication (TOTP) is available and recommended for all accounts.</p>

        <h2>6. International transfers</h2>
        <p>Hosting is in DigitalOcean's region of your choice (default: Frankfurt, EU). Cross-border transfers are protected by Standard Contractual Clauses where applicable.</p>

        <h2>7. Cookies</h2>
        <p>See the <a href="/legal/cookies" className="text-gold">Cookies Policy</a> for details on essential, preferences, and analytics cookies.</p>

        <h2>8. Children</h2>
        <p>The platform is not directed at persons under 18. We do not knowingly collect data from minors. If you believe a minor has registered, contact us and we will delete the account.</p>

        <hr />
        <h2>عربي — سياسة الخصوصية</h2>

        <p>نحترم خصوصيتك. هذه السياسة توضّح ما نجمعه من بيانات، وكيف نستخدمها، وحقوقك تجاهها. تلتزم منصّة «أسد السوق» بنظام حماية البيانات الشخصية السعودي (PDPL) واللائحة الأوروبية (GDPR).</p>

        <h3>١. البيانات التي نجمعها</h3>
        <ul>
          <li>بيانات الحساب: الاسم الكامل، البريد، كلمة المرور المُجزَّأة، الهاتف الاختياري، اللغة والمنطقة الزمنية.</li>
          <li>تفضيلات التداول: الرموز، الأُطر الزمنية، نسبة المخاطرة، إعدادات التنبيهات.</li>
          <li>مفاتيح الوسطاء: مشفّرة بـ AES-GCM، لا تُحفظ أبداً نصاً صريحاً.</li>
          <li>القياس عن بُعد: مشاهدات الصفحات، تفاعلات الميزات، تقارير الأخطاء — مجمّعة ومجهّلة.</li>
          <li>سجلّات التشغيل: عناوين IP، وكيل المتصفح، أوقات الجلسات — تُحفظ 90 يوماً للأمان.</li>
          <li>سجلّات التداول: الدخول والخروج والربح/الخسارة وتعليل Confluence لكل إشارة — تُحفظ طوال عمر الحساب + 7 سنوات للامتثال التنظيمي.</li>
        </ul>

        <h3>٢. كيف نستخدم البيانات</h3>
        <ul>
          <li>تقديم التحليل والإشارات وتنفيذ البوت الذي اشتركت فيه</li>
          <li>الفوترة ومنع الاحتيال</li>
          <li>تحسين دقّة المنصّة عبر حلقة التعلّم الذاتي (بيانات مجمّعة وغير معرّفة)</li>
          <li>الامتثال لمتطلّبات مكافحة غسل الأموال والتعرّف على الهوية</li>
          <li>الردّ على طلبات الدعم</li>
        </ul>

        <h3>٣. المشاركة</h3>
        <p>نشاركها فقط مع: مزوّدي الدفع (HyperPay/Stripe/PayPal)، الوسطاء المربوطين بإذنك، مزوّدي الاستضافة والمراقبة، الجهات القانونية عند الإلزام. لا نبيع بياناتك.</p>

        <h3>٤. حقوقك</h3>
        <p>الوصول، التصحيح، الحذف، الاعتراض، نقل البيانات، سحب الموافقة. للطلبات: <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a> ونردّ خلال 30 يوماً.</p>

        <h3>٥. الأمان</h3>
        <p>كلمات المرور مُجزَّأة Argon2id، مفاتيح الوسطاء مشفّرة AES-GCM، الجلسات بكوكيز آمنة HttpOnly، يدعم 2FA TOTP لكل الحسابات.</p>

        <h3>٦. النقل الدولي</h3>
        <p>الاستضافة في منطقة DigitalOcean المختارة (افتراضياً: فرانكفورت، الاتحاد الأوروبي). النقل العابر للحدود محمي بشروط تعاقدية معيارية.</p>
      </main>
      <Footer />
    </>
  );
}
