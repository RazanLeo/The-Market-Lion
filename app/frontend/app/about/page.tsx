import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';

export default function AboutPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-12 prose prose-invert">
        <h1 className="text-gold font-display text-3xl">About — The Market Lion</h1>

        <p>The Market Lion is a Saudi-built, AI-powered trading platform that brings institutional-grade decision-making within reach of every trader. The platform unifies <strong>140 trading schools</strong>, <strong>135 technical indicators</strong>, <strong>20 essential chart tools</strong>, real-time fundamental data, order-flow inspection, and Bookmap-style liquidity mapping into a single Multi-School Voting Engine that produces a transparent 0–100 Confluence Score on every (symbol, timeframe).</p>

        <h2>Vision</h2>
        <p>To empower the individual trader with institutional-grade decisions through a fully transparent multi-school confluence engine and a multi-layered risk framework.</p>

        <h2>Mission</h2>
        <p>Combine 140+ analysis schools, 135+ indicators, 20 essential tools, and live fundamental + flow data into one decisive Buy / Sell / Wait signal — with strict per-trade risk controls, a self-learning weight loop, and full audit trails on every decision.</p>

        <h2>Objectives</h2>
        <ul>
          <li>Confluence Score per (symbol, timeframe) every minute</li>
          <li>R-multiple risk plans (1:1, 1:2, 1:3, 1:5) with ATR-based stops</li>
          <li>Self-learning weights that adjust after each closed trade</li>
          <li>Transparent reasoning for every signal — no black box</li>
          <li>12-language UI with full RTL Arabic support</li>
        </ul>

        <h2>Founder</h2>
        <p><strong>Razan Tawfiq Al-Farraj</strong> — Saudi Arabia. Owner and product lead of The Market Lion.</p>

        <hr />
        <h2>عربي — أسد السوق</h2>
        <p>«أسد السوق» منصّة تداول سعودية مدعومة بالذكاء الاصطناعي، تضع قرارات بمستوى المؤسسات بين يدي كل متداول. توحّد المنصّة <strong>140 مدرسة تداول</strong> و<strong>135 مؤشّراً فنّياً</strong> و<strong>20 أداة شارت</strong> وتحليلاً أساسياً حياً وفحص تدفّق الأوامر وخريطة سيولة على نمط Bookmap داخل محرّك تصويت متعدّد المدارس يُخرج درجة Confluence شفّافة من 0 إلى 100 لكل (رمز، إطار زمني).</p>

        <h3>الرؤية</h3>
        <p>تمكين كل متداول فرد من اتخاذ قرارات بمستوى المؤسسات، عبر محرّك Confluence شفّاف بالكامل وإطار مخاطر متعدّد الطبقات.</p>

        <h3>الرسالة</h3>
        <p>دمج 140 مدرسة و135 مؤشّراً و20 أداة جوهرية مع البيانات الأساسية وتدفّق الأوامر الحيّ في إشارة واحدة حاسمة شراء/بيع/انتظار — مع ضوابط مخاطر صارمة، حلقة تعلّم ذاتي للأوزان، وسجلّ تدقيق كامل لكل قرار.</p>

        <h3>الأهداف</h3>
        <ul>
          <li>درجة Confluence لكل (رمز، إطار زمني) كل دقيقة</li>
          <li>خطط مخاطر بنسب R (1:1، 1:2، 1:3، 1:5) مع وقف خسارة مبنى على ATR</li>
          <li>أوزان متعلِّمة تتعدّل بعد كل صفقة مغلقة</li>
          <li>تعليل شفّاف لكل إشارة — بلا صناديق سوداء</li>
          <li>واجهة بـ 12 لغة ودعم RTL كامل للعربية</li>
        </ul>

        <h3>المؤسِّسة</h3>
        <p><strong>رزان توفيق الفرّاج</strong> — المملكة العربية السعودية. مالكة وقائدة منتج «أسد السوق».</p>
      </main>
      <Footer />
    </>
  );
}
