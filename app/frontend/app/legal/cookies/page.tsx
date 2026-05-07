import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function CookiesPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">Cookies Policy</h1>
        <p>The Market Lion uses cookies and similar technologies to operate the platform, improve performance, and remember your preferences. This page explains what we use and how you can control them.</p>
        <h2>Types of cookies we use</h2>
        <ul>
          <li><strong>Essential</strong> — required for authentication, session management, and security (CSRF tokens, JWT refresh). These cannot be disabled without breaking the platform.</li>
          <li><strong>Preferences</strong> — store your language, timezone, theme, and watchlist so the dashboard renders the way you left it.</li>
          <li><strong>Analytics</strong> — aggregate usage telemetry that helps us improve the product. No personal trading data is sent to analytics providers.</li>
        </ul>
        <h2>Managing cookies</h2>
        <p>You can clear cookies at any time through your browser settings. Disabling essential cookies will sign you out and prevent you from logging back in. We do not use cookies for advertising or third-party tracking.</p>
        <p>For questions about how we use cookies, write to <a href="mailto:razan.tawfiq@gmail.com" className="text-gold">razan.tawfiq@gmail.com</a>.</p>
        <hr />
        <h2>عربي</h2>
        <p>تستخدم منصة "أسد السوق" ملفات تعريف الارتباط (Cookies) لتشغيل المنصة وتحسين الأداء وحفظ تفضيلاتك.</p>
        <ul>
          <li><strong>أساسية</strong>: لازمة لتسجيل الدخول وإدارة الجلسة والأمان (لا يمكن تعطيلها).</li>
          <li><strong>تفضيلات</strong>: تحفظ اللغة والمنطقة الزمنية وقائمة المتابعة.</li>
          <li><strong>تحليلات</strong>: مقاييس استخدام مجمّعة لتحسين المنتج، بدون بيانات تداول شخصية.</li>
        </ul>
        <p>يمكنك حذف الكوكيز من إعدادات المتصفّح في أي وقت. تعطيل الكوكيز الأساسية سيمنعك من تسجيل الدخول. لا نستخدم كوكيز للإعلانات أو التتبّع الخارجي.</p>
      </main>
      <Footer />
    </>
  );
}
