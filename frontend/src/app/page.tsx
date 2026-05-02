'use client'

import Link from 'next/link'
import { useState } from 'react'

const LionLogo = ({ size = 80, hero = false }: { size?: number; hero?: boolean }) => (
  <img
    src="/logo.jpg"
    alt="أسد السوق"
    width={hero ? undefined : size}
    height={hero ? undefined : size}
    style={hero
      ? { maxWidth: 340, width: '100%', height: 'auto', borderRadius: 16, objectFit: 'contain' }
      : { borderRadius: '50%', objectFit: 'cover', width: size, height: size }
    }
  />
)

const features = [
  {
    icon: '📊',
    title: 'تحليل فني متكامل',
    titleEn: 'Complete Technical Analysis',
    desc: '74+ مدرسة تحليل تعمل معاً لتقديم إشارات دقيقة بنسبة ثقة عالية',
  },
  {
    icon: '🔗',
    title: 'ربط مباشر بالبروكر',
    titleEn: 'Direct Broker Connection',
    desc: 'تنفيذ تلقائي للصفقات عبر MT4/MT5 مع إدارة المخاطر المتكاملة',
  },
  {
    icon: '🏫',
    title: '74+ مدرسة تحليل',
    titleEn: '74+ Analysis Schools',
    desc: 'ICT، وايكوف، إليوت، داو، الفيبوناتشي، وأكثر من 70 منهجية أخرى',
  },
  {
    icon: '🛡️',
    title: 'حماية رأس المال',
    titleEn: 'Capital Protection',
    desc: 'نظام متكامل لإدارة المخاطر يضمن عدم تجاوز الخسارة اليومية للحد الأقصى',
  },
]

const plans = [
  {
    name: 'مجاني',
    nameEn: 'Free',
    price: 0,
    features: ['تحليل فني أساسي', '3 إشارات يومياً', 'بيانات متأخرة 15 دقيقة', 'دعم مجتمعي'],
    color: 'border-dark-600',
    btnClass: 'btn-outline-gold',
    popular: false,
  },
  {
    name: 'برو',
    nameEn: 'Pro',
    price: 79,
    features: ['تحليل فني كامل', 'إشارات غير محدودة', 'بيانات فورية', 'ربط مع MT4/MT5', 'دعم 24/7', 'تحليل 10 أزواج'],
    color: 'border-gold',
    btnClass: 'btn-gold',
    popular: true,
  },
  {
    name: 'VIP',
    nameEn: 'VIP',
    price: 199,
    features: ['كل مزايا برو', 'تداول تلقائي كامل', '74+ مدرسة تحليل', 'ذكاء اصطناعي متقدم', 'مدير حساب خاص', 'إشارات فورية SMS'],
    color: 'border-dark-600',
    btnClass: 'btn-outline-gold',
    popular: false,
  },
]

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-dark-900" dir="rtl">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-900/90 backdrop-blur-sm border-b border-dark-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LionLogo size={44} />
            <div>
              <div className="text-gold font-bold text-xl leading-none" style={{ fontFamily: 'Cairo' }}>
                أسد السوق
              </div>
              <div className="text-gray-400 text-xs">The Market Lion</div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-gray-300 hover:text-gold transition-colors text-sm">المميزات</a>
            <a href="#pricing" className="text-gray-300 hover:text-gold transition-colors text-sm">الأسعار</a>
            <Link href="/login" className="btn-outline-gold text-sm px-4 py-2">تسجيل الدخول</Link>
            <Link href="/register" className="btn-gold text-sm px-4 py-2">ابدأ مجاناً</Link>
          </div>
          <button
            className="md:hidden text-gold"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-dark-700 p-4 flex flex-col gap-3">
            <Link href="/login" className="btn-outline-gold text-sm text-center">تسجيل الدخول</Link>
            <Link href="/register" className="btn-gold text-sm text-center">ابدأ مجاناً</Link>
          </div>
        )}
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
        {/* Background effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(201,162,39,0.08) 0%, transparent 70%)' }} />
          <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-gold/30 to-transparent" />
        </div>

        <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
          {/* Lion Logo */}
          <div className="flex justify-center mb-8 animate-float">
            <LionLogo hero />
          </div>

          {/* Title */}
          <h1 className="text-6xl md:text-8xl font-black mb-2 animate-glow"
            style={{
              background: 'linear-gradient(135deg, #E8C547, #C9A227, #A07B0A)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontFamily: 'Cairo',
            }}>
            أسد السوق
          </h1>
          <h2 className="text-2xl md:text-3xl text-gray-300 mb-4" style={{ fontFamily: 'Inter, Cairo' }}>
            The Market Lion
          </h2>

          <p className="text-lg md:text-xl text-gray-300 mb-4 max-w-2xl mx-auto">
            أقوى بوت تداول بالذكاء الاصطناعي في العالم
          </p>
          <p className="text-gray-500 mb-10 max-w-xl mx-auto text-sm md:text-base">
            تحليل فني متكامل من 74+ مدرسة، ربط مباشر بالبروكر، وحماية احترافية لرأس المال
          </p>

          {/* Stats */}
          <div className="flex justify-center gap-8 mb-10">
            {[
              { num: '74+', label: 'مدرسة تحليل' },
              { num: '71%', label: 'معدل الفوز' },
              { num: '1247', label: 'مستخدم نشط' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-2xl md:text-3xl font-black text-gold">{stat.num}</div>
                <div className="text-gray-400 text-xs">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register" className="btn-green text-lg px-10 py-4">
              ابدأ مجاناً 🚀
            </Link>
            <Link href="/login" className="btn-outline-gold text-lg px-10 py-4">
              سجل الدخول
            </Link>
          </div>

          <p className="text-gray-600 text-xs mt-4">لا يحتاج بطاقة ائتمانية • إلغاء في أي وقت</p>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-white mb-3">لماذا أسد السوق؟</h2>
          <p className="text-gray-400">تقنية متقدمة مصممة لتمنحك أفضلية حقيقية في الأسواق</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => (
            <div key={i} className="card-gold p-6 hover:gold-glow transition-all duration-300 group">
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="text-gold font-bold text-lg mb-2 group-hover:text-gold-light transition-colors">
                {f.title}
              </h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Extra features grid */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            'تحليل ICT / Smart Money', 'موجات إليوت', 'وايكوف', 'Supply & Demand',
            'فيبوناتشي متقدم', 'تحليل الحجم (VSA)', 'أنماط الشموع', 'تحليل التوافقية',
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-gray-300 text-sm">
              <span className="text-gold">✓</span> {item}
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 bg-dark-800/50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-white mb-3">كيف يعمل؟</h2>
            <p className="text-gray-400">ثلاث خطوات بسيطة للبدء</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: '١', title: 'أنشئ حسابك', desc: 'سجل مجاناً وأضف بيانات حسابك لدى الوسيط' },
              { step: '٢', title: 'فعّل الروبوت', desc: 'اختر الأزواج والإطار الزمني وأنقر تشغيل' },
              { step: '٣', title: 'راقب الأرباح', desc: 'يتولى الروبوت التحليل والتنفيذ تلقائياً' },
            ].map((item, i) => (
              <div key={i} className="text-center">
                <div className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-black text-dark-900 mx-auto mb-4"
                  style={{ background: 'linear-gradient(135deg, #C9A227, #E8C547)' }}>
                  {item.step}
                </div>
                <h3 className="text-white font-bold text-lg mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-white mb-3">خطط الاشتراك</h2>
          <p className="text-gray-400">اختر الخطة المناسبة لأهدافك</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan, i) => (
            <div key={i} className={`relative rounded-2xl p-6 border ${plan.color} ${plan.popular ? 'gold-glow scale-105' : ''} bg-dark-800 transition-all duration-300 hover:gold-glow`}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold text-dark-900"
                  style={{ background: 'linear-gradient(135deg, #C9A227, #E8C547)' }}>
                  الأكثر شيوعاً
                </div>
              )}
              <div className="text-center mb-6">
                <h3 className={`text-2xl font-black mb-1 ${plan.popular ? 'text-gold' : 'text-white'}`}>
                  {plan.name}
                </h3>
                <div className="text-4xl font-black text-white">
                  {plan.price === 0 ? 'مجاناً' : `$${plan.price}`}
                </div>
                {plan.price > 0 && <div className="text-gray-400 text-sm">/شهر</div>}
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-center gap-2 text-gray-300 text-sm">
                    <span className="text-gold">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/register" className={`${plan.btnClass} block text-center w-full`}>
                {plan.price === 0 ? 'ابدأ مجاناً' : 'اشترك الآن'}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-700 py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <LionLogo size={32} />
            <span className="text-gold font-bold">أسد السوق</span>
          </div>
          <p className="text-gray-500 text-sm">
            © 2025 أسد السوق | The Market Lion. جميع الحقوق محفوظة.
          </p>
          <div className="flex gap-4 text-gray-500 text-sm">
            <a href="#" className="hover:text-gold transition-colors">الشروط والأحكام</a>
            <a href="#" className="hover:text-gold transition-colors">الخصوصية</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
