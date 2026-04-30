'use client'
import Link from 'next/link'
import { LionLogo } from '@/components/ui/LionLogo'

const PLANS = [
  {
    id: 'free',
    name: 'مجاني',
    nameEn: 'Free',
    price: 0,
    priceYear: 0,
    color: 'border-dark-50',
    badge: '',
    features: [
      '3 أصول فقط',
      '10 إشارات / شهر',
      'تحليل 24 مدرسة',
      'لوحة تحكم أساسية',
      'تطبيق الجوال',
    ],
    disabled: ['تداول تلقائي', 'الباكتستينج', 'إشعارات تيليغرام', 'وصول API'],
    cta: 'ابدأ مجاناً',
    ctaHref: '/auth/register',
    ctaStyle: 'btn-outline-gold',
  },
  {
    id: 'starter',
    name: 'مبتدئ',
    nameEn: 'Starter',
    price: 49,
    priceYear: 470,
    color: 'border-dark-50',
    badge: '',
    features: [
      '5 أصول',
      '50 إشارة / شهر',
      'تحليل 65+ مدرسة',
      'إشعارات تيليغرام',
      'تطبيق الجوال',
      'دعم الدردشة',
    ],
    disabled: ['تداول تلقائي', 'الباكتستينج', 'وصول API'],
    cta: 'ابدأ الآن',
    ctaHref: '/auth/register?plan=starter',
    ctaStyle: 'btn-outline-gold',
  },
  {
    id: 'pro',
    name: 'احترافي',
    nameEn: 'Pro',
    price: 149,
    priceYear: 1430,
    color: 'border-gold-500',
    badge: 'الأكثر شعبية',
    features: [
      '20 أصل',
      '500 إشارة / شهر',
      'تحليل 65+ مدرسة',
      'تداول شبه تلقائي',
      'الباكتستينج (10 سنوات)',
      'إشعارات تيليغرام + ديسكورد',
      'تطبيق الجوال والسطح المكتبي',
      'أولوية الدعم الفني',
    ],
    disabled: ['وصول API', 'دعم VIP'],
    cta: 'ابدأ 7 أيام مجاناً',
    ctaHref: '/auth/register?plan=pro',
    ctaStyle: 'btn-gold',
  },
  {
    id: 'vip',
    name: 'في آي بي',
    nameEn: 'VIP',
    price: 399,
    priceYear: 3830,
    color: 'border-gold-500',
    badge: '🦁 الأفضل',
    features: [
      'جميع الأصول (غير محدود)',
      'إشارات غير محدودة',
      'تداول تلقائي كامل',
      'باكتستينج متقدم + Monte Carlo',
      'وصول API كامل',
      'إشعارات كاملة (تيليغرام، ديسكورد، واتساب، إيميل)',
      'ربط مع 10+ وسطاء',
      'دعم VIP على مدار الساعة',
      'جلسات تدريب شخصية',
    ],
    disabled: [],
    cta: 'ابدأ 7 أيام مجاناً',
    ctaHref: '/auth/register?plan=vip',
    ctaStyle: 'btn-gold',
  },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-dark-900 text-white" dir="rtl">
      {/* Nav */}
      <nav className="border-b border-dark-50 px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <LionLogo size={36} />
          <span className="font-bold text-gold-500">أسد السوق</span>
        </Link>
        <div className="flex gap-4 text-sm">
          <Link href="/dashboard" className="text-gray-400 hover:text-white">لوحة التحكم</Link>
          <Link href="/auth/login" className="btn-outline-gold px-4 py-1.5 rounded-lg text-sm">دخول</Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="text-center py-16 px-4">
        <h1 className="text-4xl font-bold mb-3">
          <span className="text-gold-gradient">اختر خطتك</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          ابدأ مجاناً وطوّر نتائجك مع باقة تناسب مستوى تداولك
        </p>
        <div className="inline-flex items-center gap-2 mt-4 bg-dark-300 rounded-full px-4 py-2 text-sm">
          <span className="text-gray-400">اشتراك سنوي</span>
          <span className="text-bull font-bold">وفر 20%</span>
        </div>
      </div>

      {/* Plans grid */}
      <div className="max-w-6xl mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map(plan => (
            <div key={plan.id} className={`relative card-dark rounded-2xl p-6 border-2 ${plan.color} flex flex-col`}>
              {plan.badge && (
                <div className="absolute -top-3 right-4 bg-gold-500 text-dark-900 text-xs font-bold px-3 py-1 rounded-full">
                  {plan.badge}
                </div>
              )}

              <div className="mb-4">
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <p className="text-xs text-gray-500">{plan.nameEn}</p>
              </div>

              <div className="mb-6">
                <span className="text-4xl font-bold text-gold-500">${plan.price}</span>
                {plan.price > 0 && <span className="text-gray-500 text-sm"> / شهر</span>}
                {plan.price === 0 && <span className="text-gray-500 text-sm"> دائماً</span>}
                {plan.priceYear > 0 && (
                  <p className="text-xs text-gray-600 mt-1">${plan.priceYear} / سنة</p>
                )}
              </div>

              <ul className="space-y-2 mb-6 flex-1">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-bull mt-0.5">✓</span>
                    <span>{f}</span>
                  </li>
                ))}
                {plan.disabled.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="mt-0.5">✗</span>
                    <span className="line-through">{f}</span>
                  </li>
                ))}
              </ul>

              <Link href={plan.ctaHref}
                className={`${plan.ctaStyle} w-full py-3 rounded-xl text-center font-bold text-sm block`}>
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Enterprise */}
        <div className="mt-8 card-dark rounded-2xl p-8 border border-gold-500/30 text-center">
          <h3 className="text-2xl font-bold text-gold-500 mb-2">المؤسسي — Enterprise</h3>
          <p className="text-gray-400 mb-4">لشركات الوساطة، صناديق التحوط، ومديري المحافظ</p>
          <div className="flex flex-wrap gap-6 justify-center text-sm text-gray-300 mb-6">
            {['White-Label كامل', 'API غير محدود', 'خوادم مخصصة', 'SLA 99.9%', 'مدير حساب مخصص', 'تكامل مع أي وسيط'].map(f => (
              <span key={f} className="flex items-center gap-1"><span className="text-gold-500">✦</span>{f}</span>
            ))}
          </div>
          <Link href="mailto:enterprise@marketlion.ai"
            className="btn-gold px-8 py-3 rounded-xl font-bold text-sm inline-block">
            تواصل مع فريق المبيعات
          </Link>
        </div>

        {/* FAQ / Guarantees */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          {[
            { icon: '🛡️', title: 'ضمان 30 يوم', desc: 'استرداد كامل إذا لم تكن راضياً' },
            { icon: '🔒', title: 'أمان تام', desc: 'ISO 27001 + تشفير AES-256' },
            { icon: '💳', title: 'دفع آمن', desc: 'Stripe، STC Pay، Mada، USDT' },
          ].map(g => (
            <div key={g.title} className="card-dark rounded-xl p-4 border border-dark-50">
              <div className="text-3xl mb-2">{g.icon}</div>
              <h4 className="font-bold text-white">{g.title}</h4>
              <p className="text-sm text-gray-500">{g.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
