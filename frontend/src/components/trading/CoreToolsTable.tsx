'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'

const TF_LABELS = ['1M', '5M', '15M', '30M', '1H', '4H']

const SIGNALS = ['buy', 'sell', 'neutral'] as const
type Signal = typeof SIGNALS[number]

const rand = () => SIGNALS[Math.floor(Math.random() * 3)]
const randPct = (min: number, max: number) => (min + Math.random() * (max - min)).toFixed(1)

const CORE_TOOLS = [
  { id: 1, tier: 'S', name: 'هيكل السوق — القمم والقيعان (HH/HL/LH/LL, EQH, EQL)', cat: 'الأصول التاريخية والبرايس أكشن', weight: 0.017, chartDefault: false, desc: 'تحليل بنية السوق عبر القمم والقيعان. ترند صاعد = HH/HL، ترند هابط = LH/LL' },
  { id: 2, tier: 'S', name: 'Pivot Points (Standard, Fibonacci, Camarilla, Woodie, DeMark)', cat: 'الأصول التاريخية والبرايس أكشن', weight: 0.017, chartDefault: false, desc: 'مستويات حسابية يومية/أسبوعية مشتقة من High/Low/Close: PP + R1/R2/R3 + S1/S2/S3' },
  { id: 3, tier: 'A', name: 'نماذج الشموع اليابانية + Price Action — حصر شامل', cat: 'الأصول التاريخية والبرايس أكشن', weight: 0.013, chartDefault: false, desc: 'تشكيلات الشموع الفردية والمركبة — دوجي، مطرقة، ابتلاع، نجوم، 3 جنود...' },
  { id: 4, tier: 'A', name: 'خطوط الدعم والمقاومة الأساسية', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.013, chartDefault: false, desc: 'مستويات أفقية تاريخية رئيسية من قمم وقيعان واضحة على إطار 4H وأعلى' },
  { id: 5, tier: 'B', name: 'خطوط الدعم والمقاومة الفرعية', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.008, chartDefault: false, desc: 'مستويات داخلية أصغر مرسومة من قمم وقيعان على إطارات 15M-30M' },
  { id: 6, tier: 'A', name: 'خطوط الاتجاه (Trend Lines)', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.013, chartDefault: false, desc: 'خطوط مائلة تربط القمم في الترند الهابط والقيعان في الصاعد' },
  { id: 7, tier: 'B', name: 'SMA 200 — متوسط بسيط ٢٠٠', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.008, chartDefault: false, desc: 'متوسط حسابي بسيط لـ 200 شمعة — الاتجاه الكلي طويل المدى' },
  { id: 8, tier: 'B', name: 'SMA 60 — متوسط بسيط ٦٠', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.008, chartDefault: false, desc: 'متوسط حسابي لـ 60 شمعة — الاتجاه متوسط المدى' },
  { id: 9, tier: 'A', name: 'EMA 7 و EMA 21 (مع التقاطع)', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.013, chartDefault: false, desc: 'متوسطان أسيّان قصيران للسكالبينج — يستخدمان معاً كنظام' },
  { id: 10, tier: 'B', name: 'FRAMA 126 — Fractal Adaptive Moving Average', cat: 'دمج التحليل الكلاسيكي والمتوسطات', weight: 0.008, chartDefault: false, desc: 'متوسط Fractal يتكيف مع تعقيد السوق رياضياً — يتباطأ في المتذبذب ويتسارع في الترند' },
  { id: 11, tier: 'B', name: 'القناة السعرية الانحراف المعياري (Std Dev Channel)', cat: 'القنوات والبولنجر', weight: 0.008, chartDefault: false, desc: 'قناة من متوسط مركزي ± 2 انحراف معياري — تحتوي 95% من حركة السعر إحصائياً' },
  { id: 12, tier: 'B', name: 'القناة السعرية الانحدار الخطي (Linear Regression Channel)', cat: 'القنوات والبولنجر', weight: 0.008, chartDefault: false, desc: 'قناة بناءً على الانحدار الخطي — تأخذ ميل الترند في الاعتبار' },
  { id: 13, tier: 'A', name: 'النماذج الفنية السعرية — حصر شامل لجميع الأنماط', cat: 'الأصول التاريخية والبرايس أكشن', weight: 0.013, chartDefault: false, desc: 'H&S، قمة/قاع مزدوج وثلاثي، أعلام، أوتاد، مثلثات، كوب وعروة، Quasimodo...' },
  { id: 14, tier: 'S', name: 'مدرسة الأموال الذكية SMC / ICT (OB, BOS, CHoCH, FVG, Breaker, Imbalance)', cat: 'السعر الخام والتداول المؤسسي', weight: 0.017, chartDefault: false, desc: 'نظام تحليل مؤسسي كامل: Order Blocks، BOS، CHoCH، FVG، Breaker Blocks، Mitigation' },
  { id: 15, tier: 'S', name: 'ICT الكاملة (Killzones London/NY, OTE 61.8%, Power of 3 AMD)', cat: 'السعر الخام والتداول المؤسسي', weight: 0.017, chartDefault: false, desc: 'منهجية Michael Huddleston: London Killzone، NY Killzone، Silver Bullet، Judas Swing' },
  { id: 16, tier: 'S', name: 'مناطق العرض والطلب (Supply & Demand Zones)', cat: 'السعر الخام والتداول المؤسسي', weight: 0.017, chartDefault: false, desc: 'تحديد مناطق الانفجار السعري — RBR و DBD = أقوى الأنواع' },
  { id: 17, tier: 'S', name: 'مناطق البلوك أوردر (Order Blocks) مع Volume بالدولار', cat: 'السعر الخام والتداول المؤسسي', weight: 0.017, chartDefault: false, desc: 'آخر شمعة هابطة/صاعدة قبل حركة قوية — تحتوي أوامر مؤسسية لم تُنفَّذ' },
  { id: 18, tier: 'A', name: 'Volume — حجم التداول الخام', cat: 'الحجم والتدفق', weight: 0.013, chartDefault: false, desc: 'حجم الصفقات الخام لكل شمعة — يؤكد قوة الحركة أو يكشف ضعفها' },
  { id: 19, tier: 'A', name: 'Order Flow — تدفق الأوامر (DOM, Cumulative Delta, Iceberg)', cat: 'الحجم والتدفق', weight: 0.013, chartDefault: false, desc: 'تتبع تدفق الأوامر الحقيقي — Bid/Ask pressure، Aggressive Buys vs Sells' },
  { id: 20, tier: 'S', name: 'نظرية السيولة والفخاخ — ICT/Wyckoff (BSL, SSL, Liquidity Sweep)', cat: 'السيولة والفخاخ', weight: 0.017, chartDefault: false, desc: 'تحديد مناطق السيولة: BSL فوق القمم وSSL تحت القيعان — فخاخ المؤسسات' },
  { id: 21, tier: 'S', name: 'تصحيح فيبوناتشي (Fibonacci Retracement)', cat: 'الهندسة والرياضيات', weight: 0.017, chartDefault: false, desc: 'مستويات: 23.6%, 38.2%, 50%, 61.8%, 78.6% — Golden Zone (0.618-0.786)' },
  { id: 22, tier: 'A', name: 'امتداد فيبوناتشي (Fibonacci Extension)', cat: 'الهندسة والرياضيات', weight: 0.013, chartDefault: false, desc: 'أهداف الموجة: 1.272, 1.414, 1.618 (الذهبي), 2.0, 2.618' },
  { id: 23, tier: 'A', name: 'RSI مع كشف الدايفرجنس (Regular & Hidden Divergence)', cat: 'المؤشرات الفنية', weight: 0.013, chartDefault: false, desc: 'RSI (14) مع Bullish/Bearish Divergence العادي والخفي' },
]

const tierColor = (tier: string) => {
  if (tier === 'S') return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30'
  if (tier === 'A') return 'text-gold bg-gold/10 border-gold/30'
  if (tier === 'B') return 'text-blue-400 bg-blue-400/10 border-blue-400/30'
  return 'text-gray-400 bg-gray-400/10 border-gray-400/30'
}

const SignalBadge = ({ s }: { s: Signal }) => {
  if (s === 'buy') return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-buy text-white">شراء</span>
  if (s === 'sell') return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-sell text-white">بيع</span>
  return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-dark-600 text-gray-400">محايد</span>
}

export default function CoreToolsTable() {
  const { language, selectedSymbol, selectedTimeframe } = useAppStore()
  const isRtl = language === 'ar'
  const [collapsed, setCollapsed] = useState(false)
  const [chartToggles, setChartToggles] = useState<Record<number, boolean>>({})
  const [lastUpdate, setLastUpdate] = useState(new Date())

  const [toolData] = useState(() =>
    CORE_TOOLS.map(tool => ({
      ...tool,
      signals: TF_LABELS.map(() => rand()),
      confidence: parseFloat(randPct(40, 95)),
    }))
  )

  useEffect(() => {
    const t = setInterval(() => setLastUpdate(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

  const toggleChart = (id: number) => {
    setChartToggles(prev => ({ ...prev, [id]: !prev[id] }))
  }

  // Calculate summary
  const tfIdx = TF_LABELS.indexOf(selectedTimeframe) !== -1 ? TF_LABELS.indexOf(selectedTimeframe) : 2
  const buyWeight = toolData.reduce((sum, t) => t.signals[tfIdx] === 'buy' ? sum + t.weight : sum, 0)
  const sellWeight = toolData.reduce((sum, t) => t.signals[tfIdx] === 'sell' ? sum + t.weight : sum, 0)
  const netScore = ((buyWeight - sellWeight) / 0.3 * 100).toFixed(1)
  const confidence = (Math.max(buyWeight, sellWeight) / 0.3 * 100).toFixed(1)
  const decision: Signal = buyWeight > sellWeight ? 'buy' : sellWeight > buyWeight ? 'sell' : 'neutral'

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🛠️</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٣ — التحليل الفني / الأدوات الرئيسية الأساسية — الوزن <span className="text-white">30٪</span> من التحليل الكامل • 23 أداة
            </div>
            <div className="text-gray-500 text-xs">
              إطار التداول: {selectedTimeframe} • الأصل: {selectedSymbol} • آخر تحديث: {lastUpdate.toLocaleTimeString('ar-SA')}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <SignalBadge s={decision} />
          <span className="text-gray-400 text-xs">{confidence}%</span>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
              <thead className="bg-dark-700/50">
                <tr>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 w-8">#</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 min-w-[200px]">الأداة / المدرسة / المؤشر</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">تصنيف</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 hidden lg:table-cell">شرح الاستراتيجية</th>
                  {TF_LABELS.map(tf => (
                    <th key={tf} className="px-1 py-2 text-gold text-center font-medium border-b border-gold/20 w-14">{tf}</th>
                  ))}
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">نتيجة شاملة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">توافق</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">وزن</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">ثقة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">شارت</th>
                </tr>
              </thead>
              <tbody>
                {toolData.map(tool => {
                  const overallSignal = tool.signals.filter(s => s === 'buy').length > tool.signals.filter(s => s === 'sell').length ? 'buy' as Signal
                    : tool.signals.filter(s => s === 'sell').length > tool.signals.filter(s => s === 'buy').length ? 'sell' as Signal : 'neutral' as Signal
                  const alignment = `${tool.signals.filter(s => s === 'buy').length} شراء • ${tool.signals.filter(s => s === 'sell').length} بيع • ${tool.signals.filter(s => s === 'neutral').length} محايد`
                  const isOn = chartToggles[tool.id] || false

                  return (
                    <tr key={tool.id} className="border-b border-dark-600 hover:bg-dark-700/30 transition-colors">
                      <td className="px-2 py-2 text-gray-500">{tool.id}</td>
                      <td className="px-2 py-2">
                        <div className="flex items-start gap-2">
                          <span className={`inline-block px-1.5 py-0.5 rounded border text-xs font-bold shrink-0 ${tierColor(tool.tier)}`}>
                            {tool.tier}
                          </span>
                          <span className="text-white">{tool.name}</span>
                        </div>
                      </td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap">{tool.cat}</td>
                      <td className="px-2 py-2 text-gray-500 text-xs hidden lg:table-cell max-w-[200px]">{tool.desc}</td>
                      {tool.signals.map((sig, i) => (
                        <td key={i} className="px-1 py-2 text-center">
                          <SignalBadge s={sig} />
                        </td>
                      ))}
                      <td className="px-2 py-2"><SignalBadge s={overallSignal} /></td>
                      <td className="px-2 py-2 text-gray-400 text-xs">{alignment}</td>
                      <td className="px-2 py-2 text-gold font-bold">{(tool.weight * 100).toFixed(1)}%</td>
                      <td className="px-2 py-2">
                        <div className="flex items-center gap-1">
                          <div className="flex-1 bg-dark-600 rounded-full h-1 min-w-[40px]">
                            <div className="h-full rounded-full bg-gold" style={{ width: `${tool.confidence}%` }} />
                          </div>
                          <span className="text-gray-400 text-xs w-8">{tool.confidence.toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-2 py-2">
                        <button
                          onClick={() => toggleChart(tool.id)}
                          className={`px-2 py-1 rounded text-xs font-bold transition-colors ${
                            isOn ? 'bg-gold text-dark-900' : 'bg-dark-600 text-gray-400 hover:bg-dark-500'
                          }`}
                        >
                          {isOn ? 'ON' : 'OFF'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="p-3 border-t border-gold/20 bg-dark-700/30">
            <div className="text-gold font-bold text-xs mb-2">🎯 القرار النهائي — جدول ٣ (الأدوات الأساسية 30٪)</div>
            <div className="grid grid-cols-6 gap-2">
              {TF_LABELS.map((tf, i) => {
                const bw = toolData.reduce((s, t) => t.signals[i] === 'buy' ? s + t.weight : s, 0)
                const sw = toolData.reduce((s, t) => t.signals[i] === 'sell' ? s + t.weight : s, 0)
                const d: Signal = bw > sw ? 'buy' : sw > bw ? 'sell' : 'neutral'
                return (
                  <div key={tf} className="bg-dark-800 rounded-lg p-2 text-center">
                    <div className="text-gray-500 text-xs mb-1">{tf}</div>
                    <SignalBadge s={d} />
                    <div className="text-gray-500 text-xs mt-1">{(Math.max(bw, sw) / 0.3 * 100).toFixed(0)}%</div>
                  </div>
                )
              })}
            </div>
            <div className="mt-2 flex flex-wrap gap-4 text-xs text-gray-400">
              <span>شراء مرجح: <span className="text-buy font-bold">{(buyWeight * 100).toFixed(1)}%</span></span>
              <span>بيع مرجح: <span className="text-sell font-bold">{(sellWeight * 100).toFixed(1)}%</span></span>
              <span>صافي: <span className="text-white font-bold">{netScore}%</span></span>
              <span>مساهمة الجدول: <span className="text-gold font-bold">{(Math.max(buyWeight, sellWeight) * 100).toFixed(1)}% من 30%</span></span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
