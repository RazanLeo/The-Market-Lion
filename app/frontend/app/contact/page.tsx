import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function ContactPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">Contact</h1>

        <p>We are committed to responding within one business day. For account-billing issues please include your subscription ID; for technical issues please describe the symbol, timeframe, and time when the issue occurred so we can reproduce.</p>

        <h2>Direct contact</h2>
        <ul>
          <li><strong>Owner & founder</strong>: Razan Tawfiq Al-Farraj — <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a></li>
          <li><strong>Country</strong>: Kingdom of Saudi Arabia</li>
          <li><strong>Support form</strong>: <a href="/support" className="text-gold">/support</a> (web form, replies by email)</li>
        </ul>

        <h2>Channels by topic</h2>
        <table className="w-full text-sm">
          <thead>
            <tr><th className="text-start">Topic</th><th className="text-start">Channel</th><th className="text-start">Response</th></tr>
          </thead>
          <tbody>
            <tr><td>Subscription &amp; billing</td><td>Support form / email</td><td>Within 1 business day</td></tr>
            <tr><td>Technical issues</td><td>Support form (include symbol, timeframe, timestamp)</td><td>Within 1 business day</td></tr>
            <tr><td>Bot / broker linking</td><td>Email — include broker name and account type</td><td>Within 24 hours</td></tr>
            <tr><td>Privacy / data requests</td><td>Email — subject "GDPR" or "PDPL"</td><td>Within 30 days (legal max)</td></tr>
            <tr><td>Institutional inquiries</td><td>Email — subject "Institution"</td><td>Within 3 business days</td></tr>
            <tr><td>Press &amp; partnerships</td><td>Email — subject "Press" or "Partner"</td><td>Within 5 business days</td></tr>
          </tbody>
        </table>

        <h2>Status &amp; outages</h2>
        <p>For platform availability issues, also check that the backend `/api/v1/health` endpoint returns 200. If the platform is fully unreachable, please email so we can investigate.</p>

        <hr />
        <h2>عربي — تواصل معنا</h2>
        <p>نلتزم بالردّ خلال يوم عمل واحد. لمسائل الفوترة أرفق رقم الاشتراك؛ للمسائل التقنية اذكر الرمز والإطار الزمني ووقت المشكلة لإعادة إنتاجها.</p>

        <ul>
          <li><strong>المالكة والمؤسِّسة</strong>: رزان توفيق الفرّاج — <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a></li>
          <li><strong>الدولة</strong>: المملكة العربية السعودية</li>
          <li><strong>نموذج الدعم</strong>: <a href="/support" className="text-gold">/support</a></li>
        </ul>

        <h3>القنوات حسب الموضوع</h3>
        <ul>
          <li><strong>الاشتراك والفوترة</strong> — نموذج/بريد، ردّ خلال يوم عمل</li>
          <li><strong>المشاكل التقنية</strong> — نموذج (مع الرمز والإطار والوقت)، ردّ خلال يوم عمل</li>
          <li><strong>البوت وربط الوسيط</strong> — بريد، ردّ خلال 24 ساعة</li>
          <li><strong>طلبات الخصوصية</strong> — بريد بعنوان "PDPL/GDPR"، ردّ خلال 30 يوماً</li>
          <li><strong>الاستفسارات المؤسسية</strong> — بريد بعنوان "Institution"، ردّ خلال 3 أيام عمل</li>
          <li><strong>الإعلام والشراكات</strong> — بريد بعنوان "Press" أو "Partner"، ردّ خلال 5 أيام عمل</li>
        </ul>
      </main>
      <Footer />
    </>
  );
}
