import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function AmlPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">AML / KYC Policy</h1>
        <p>The Market Lion is committed to preventing money laundering, terrorist financing, and financial fraud. We comply with the Saudi Anti-Money Laundering Law, the Capital Market Authority guidelines, and applicable international standards (FATF).</p>
        <h2>Customer due diligence</h2>
        <p>Before activating live-trading or paid subscriptions, we verify each user's identity using government-issued ID, proof of address, and — where required — beneficial-ownership disclosure. Trading API keys are encrypted at rest with AES-GCM and bound to the verified account.</p>
        <h2>Verification limits</h2>
        <ul>
          <li><strong>Free / demo</strong> — email verification only.</li>
          <li><strong>Individual paid plans</strong> — full identity verification (KYC) before live broker linking.</li>
          <li><strong>Institutional</strong> — corporate documentation, beneficial-owner disclosure, and source-of-funds declaration.</li>
        </ul>
        <h2>Monitoring & reporting</h2>
        <p>We monitor account activity for suspicious patterns and reserve the right to suspend any account pending review. We report suspicious activity to the relevant authorities as required by law. We do not custody client funds — all trading capital remains with regulated brokers (e.g. Capital.com).</p>
        <hr />
        <h2>عربي</h2>
        <p>تلتزم منصة "أسد السوق" بقواعد مكافحة غسل الأموال وتمويل الإرهاب وفقاً لنظام مكافحة غسل الأموال السعودي ولوائح هيئة السوق المالية والمعايير الدولية (FATF).</p>
        <p>قبل تفعيل التداول الحقيقي أو الاشتراكات المدفوعة، نتحقّق من هوية كل مستخدم عبر هوية رسمية وإثبات عنوان وإفصاح المالك المستفيد عند الاقتضاء. مفاتيح API الخاصة بالوسطاء مشفّرة بـ AES-GCM وتُربط بالحساب المُتحقّق منه فقط.</p>
        <ul>
          <li><strong>التجريبي</strong>: تحقّق بريد إلكتروني فقط.</li>
          <li><strong>الفردي المدفوع</strong>: تحقّق هوية كامل (KYC) قبل ربط الوسيط الحقيقي.</li>
          <li><strong>المؤسسي</strong>: مستندات الشركة، المالك المستفيد، إقرار مصدر الأموال.</li>
        </ul>
        <p>لا نحتفظ بأموال العملاء؛ يبقى رأس المال لدى وسطاء منظَّمين. نراقب الأنشطة المريبة ونبلّغ عنها للجهات المختصّة عند اللزوم.</p>
      </main>
      <Footer />
    </>
  );
}
