'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'

const TF_LABELS = ['1M', '5M', '15M', '30M', '1H', '4H']
type Signal = 'buy' | 'sell' | 'neutral'
const rand = (): Signal => (['buy', 'sell', 'neutral'] as Signal[])[Math.floor(Math.random() * 3)]

const ALL_SCHOOLS = [
  { id: 1, tier: 'S', name: 'نظرية داو (Dow Theory)', cat: 'الأصول التاريخية', weight: 0.0084 },
  { id: 2, tier: 'S', name: 'IPDA — Interbank Price Delivery Algorithm', cat: 'التداول المؤسسي', weight: 0.0084 },
  { id: 3, tier: 'A', name: 'شوكة أندروز (Andrews Pitchfork)', cat: 'الكلاسيكية', weight: 0.0063 },
  { id: 4, tier: 'B', name: 'صندوق دارفاس (Darvas Box Theory)', cat: 'الكلاسيكية', weight: 0.0042 },
  { id: 5, tier: 'A', name: 'تحليل مراحل وينشتاين (Weinstein Stage Analysis)', cat: 'الكلاسيكية', weight: 0.0063 },
  { id: 6, tier: 'B', name: 'الفراكتل ونظرية الفوضى — Bill Williams', cat: 'الكلاسيكية', weight: 0.0042 },
  { id: 7, tier: 'A', name: 'نظام السلحفاة (Turtle Trading)', cat: 'تتبع الترند', weight: 0.0063 },
  { id: 8, tier: 'S', name: 'موجات إليوت (Elliott Wave Theory)', cat: 'الأمواج والدورات', weight: 0.0084 },
  { id: 9, tier: 'S', name: 'طريقة وايكوف (Wyckoff Method)', cat: 'التداول المؤسسي', weight: 0.0084 },
  { id: 10, tier: 'B', name: 'دورات هيرست (Hurst Cycle Analysis)', cat: 'الأمواج والدورات', weight: 0.0042 },
  { id: 11, tier: 'A', name: 'سلسلة دي مارك (DeMark Sequential & Combo)', cat: 'الكلاسيكية', weight: 0.0063 },
  { id: 12, tier: 'C', name: 'موجة كوندراتيف (Kondratieff Super Cycle)', cat: 'الأمواج والدورات', weight: 0.0021 },
  { id: 13, tier: 'A', name: 'تحليل الحجم والانتشار (VSA — Tom Williams)', cat: 'الحجم والتدفق', weight: 0.0063 },
  { id: 14, tier: 'S', name: 'ملف السوق (Market Profile — Steidlmayer)', cat: 'الحجم والتدفق', weight: 0.0084 },
  { id: 15, tier: 'A', name: 'نظرية مزاد السوق (Auction Market Theory)', cat: 'الحجم والتدفق', weight: 0.0063 },
  { id: 16, tier: 'A', name: 'البصمة والدلتا (Footprint Charts & Delta)', cat: 'الحجم والتدفق', weight: 0.0063 },
  { id: 17, tier: 'B', name: 'تداول المجمعات المظلمة (Dark Pool Trading)', cat: 'المؤسسي', weight: 0.0042 },
  { id: 18, tier: 'S', name: 'ملف الحجم الأفقي (Volume Profile VPVR/VPSR)', cat: 'الحجم والتدفق', weight: 0.0084 },
  { id: 19, tier: 'B', name: 'Fibonacci Fan', cat: 'الهندسة والرياضيات', weight: 0.0042 },
  { id: 20, tier: 'C', name: 'Fibonacci Arcs', cat: 'الهندسة والرياضيات', weight: 0.0021 },
  { id: 21, tier: 'C', name: 'Fibonacci Time Zones', cat: 'الهندسة والرياضيات', weight: 0.0021 },
  { id: 22, tier: 'C', name: 'Fibonacci Speed Resistance Fan', cat: 'الهندسة والرياضيات', weight: 0.0021 },
  { id: 23, tier: 'S', name: 'نظرية غان السعرية (Gann Angles, Square of Nine, Gann Box)', cat: 'الهندسة والرياضيات', weight: 0.0084 },
  { id: 24, tier: 'A', name: 'الأنماط التوافقية (Harmonic — Gartley, Butterfly, Bat, Crab, Cypher, Shark, ABCD, 5-0)', cat: 'الهندسة والرياضيات', weight: 0.0063 },
  { id: 25, tier: 'C', name: 'الهندسة المقدسة (Sacred Geometry / Golden Ratio)', cat: 'الهندسة والرياضيات', weight: 0.0021 },
  { id: 26, tier: 'B', name: 'Renko Charts', cat: 'أنواع الشارت البديلة', weight: 0.0042 },
  { id: 27, tier: 'B', name: 'Heikin Ashi', cat: 'أنواع الشارت البديلة', weight: 0.0042 },
  { id: 28, tier: 'C', name: 'Kagi Charts', cat: 'أنواع الشارت البديلة', weight: 0.0021 },
  { id: 29, tier: 'C', name: 'Three Line Break', cat: 'أنواع الشارت البديلة', weight: 0.0021 },
  { id: 30, tier: 'B', name: 'Range Bars', cat: 'أنواع الشارت البديلة', weight: 0.0042 },
  { id: 31, tier: 'B', name: 'Point & Figure', cat: 'أنواع الشارت البديلة', weight: 0.0042 },
  { id: 32, tier: 'B', name: 'Tick Charts', cat: 'أنواع الشارت البديلة', weight: 0.0042 },
  { id: 33, tier: 'A', name: 'التداول الكمي/الخوارزمي (Quantitative Algo Trading)', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 34, tier: 'A', name: 'ارتداد للمتوسط (Mean Reversion)', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 35, tier: 'A', name: 'التحليل بين الأسواق (Intermarket Analysis)', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 36, tier: 'A', name: 'تقرير COT (Commitment of Traders)', cat: 'التداول المؤسسي', weight: 0.0063 },
  { id: 37, tier: 'A', name: 'اتساع السوق (Market Breadth — A/D, McClellan)', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 38, tier: 'A', name: 'الذكاء الاصطناعي والتعلم الآلي في التحليل', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 39, tier: 'B', name: 'الموسمية (Seasonality)', cat: 'الكمية الحديثة', weight: 0.0042 },
  { id: 40, tier: 'B', name: 'منهجية أونيل (CANSLIM — William O\'Neil)', cat: 'الكمية الحديثة', weight: 0.0042 },
  { id: 41, tier: 'A', name: 'تداول الزخم (Momentum Trading)', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 42, tier: 'B', name: 'القوة النسبية مانسفيلد (Mansfield Relative Strength)', cat: 'الكمية الحديثة', weight: 0.0042 },
  { id: 43, tier: 'C', name: 'مربع غان الزمني (Gann Square of Time)', cat: 'الهندسة والرياضيات', weight: 0.0021 },
  { id: 44, tier: 'C', name: 'النجمة الزمنية لغان (Gann Star / Hexagon Chart)', cat: 'الهندسة والرياضيات', weight: 0.0021 },
  { id: 45, tier: 'B', name: 'التحليل الزمني الدوري (Cyclic Analysis)', cat: 'الأمواج والدورات', weight: 0.0042 },
  { id: 46, tier: 'C', name: 'التوقيت الفلكي (Financial Astrology)', cat: 'الأمواج والدورات', weight: 0.0021 },
  { id: 47, tier: 'A', name: 'تحليل جلسات الأسواق (Sydney / Tokyo / London / NY)', cat: 'الكمية الحديثة', weight: 0.0063 },
  { id: 48, tier: 'B', name: 'Volume Charts', cat: 'الحجم والتدفق', weight: 0.0042 },
]

const tierColor = (tier: string) => {
  if (tier === 'S') return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30'
  if (tier === 'A') return 'text-gold bg-gold/10 border-gold/30'
  if (tier === 'B') return 'text-blue-400 bg-blue-400/10 border-blue-400/30'
  return 'text-gray-500 bg-gray-500/10 border-gray-500/30'
}

const SignalBadge = ({ s }: { s: Signal }) => {
  if (s === 'buy') return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-buy text-white">شراء</span>
  if (s === 'sell') return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-sell text-white">بيع</span>
  return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-dark-600 text-gray-400">محايد</span>
}

export default function SchoolsTable() {
  const { language, selectedSymbol, selectedTimeframe } = useAppStore()
  const isRtl = language === 'ar'
  const [collapsed, setCollapsed] = useState(false)
  const [chartToggles, setChartToggles] = useState<Record<number, boolean>>({})
  const [filter, setFilter] = useState<string>('all')
  const [lastUpdate, setLastUpdate] = useState(new Date())

  const [schoolData] = useState(() =>
    ALL_SCHOOLS.map(s => ({
      ...s,
      signals: TF_LABELS.map(() => rand()),
      confidence: 40 + Math.random() * 55,
    }))
  )

  useEffect(() => {
    const t = setInterval(() => setLastUpdate(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

  const categories = ['all', ...Array.from(new Set(ALL_SCHOOLS.map(s => s.cat)))]

  const filtered = filter === 'all' ? schoolData : schoolData.filter(s => s.cat === filter)

  const tfIdx = Math.max(0, TF_LABELS.indexOf(selectedTimeframe))
  const buyWeight = schoolData.reduce((sum, s) => s.signals[tfIdx] === 'buy' ? sum + s.weight : sum, 0)
  const sellWeight = schoolData.reduce((sum, s) => s.signals[tfIdx] === 'sell' ? sum + s.weight : sum, 0)
  const decision: Signal = buyWeight > sellWeight ? 'buy' : sellWeight > buyWeight ? 'sell' : 'neutral'
  const confPct = (Math.max(buyWeight, sellWeight) / 0.25 * 100).toFixed(1)

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🏛️</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٤ — التحليل الفني / جميع مدارس التحليل الفني — الوزن <span className="text-white">25٪</span> من التحليل الكامل • 48 مدرسة
            </div>
            <div className="text-gray-500 text-xs">
              {selectedSymbol} — {selectedTimeframe} • آخر تحديث: {lastUpdate.toLocaleTimeString('ar-SA')}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <SignalBadge s={decision} />
          <span className="text-gray-400 text-xs">{confPct}%</span>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <>
          {/* Category Filter */}
          <div className="flex flex-wrap gap-2 p-3 border-b border-gold/20 bg-dark-700/20">
            {categories.slice(0, 8).map(cat => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  filter === cat
                    ? 'bg-gold text-dark-900 font-bold'
                    : 'bg-dark-600 text-gray-400 hover:text-gold'
                }`}
              >
                {cat === 'all' ? `الكل (${ALL_SCHOOLS.length})` : cat}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
              <thead className="bg-dark-700/50">
                <tr>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 w-8">#</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 min-w-[220px]">المدرسة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">تصنيف</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 hidden md:table-cell">التصنيف</th>
                  {TF_LABELS.map(tf => (
                    <th key={tf} className="px-1 py-2 text-gold text-center font-medium border-b border-gold/20 w-14">{tf}</th>
                  ))}
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">نتيجة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">توافق</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">وزن</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">ثقة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">شارت</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(school => {
                  const buyCnt = school.signals.filter(s => s === 'buy').length
                  const sellCnt = school.signals.filter(s => s === 'sell').length
                  const overall: Signal = buyCnt > sellCnt ? 'buy' : sellCnt > buyCnt ? 'sell' : 'neutral'
                  const isOn = chartToggles[school.id] || false

                  return (
                    <tr key={school.id} className="border-b border-dark-600 hover:bg-dark-700/30">
                      <td className="px-2 py-2 text-gray-500">{school.id}</td>
                      <td className="px-2 py-2">
                        <div className="flex items-center gap-1.5">
                          <span className={`inline-block px-1.5 py-0.5 rounded border text-xs font-bold shrink-0 ${tierColor(school.tier)}`}>
                            {school.tier}
                          </span>
                          <span className="text-white">{school.name}</span>
                        </div>
                      </td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap hidden md:table-cell">{school.cat}</td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap hidden md:table-cell">{school.cat}</td>
                      {school.signals.map((sig, i) => (
                        <td key={i} className="px-1 py-2 text-center"><SignalBadge s={sig} /></td>
                      ))}
                      <td className="px-2 py-2"><SignalBadge s={overall} /></td>
                      <td className="px-2 py-2 text-gray-400 text-xs whitespace-nowrap">
                        {buyCnt} ش • {sellCnt} ب • {6 - buyCnt - sellCnt} م
                      </td>
                      <td className="px-2 py-2 text-gold font-bold">{(school.weight * 100).toFixed(2)}%</td>
                      <td className="px-2 py-2">
                        <div className="flex items-center gap-1">
                          <div className="flex-1 bg-dark-600 rounded-full h-1 min-w-[30px]">
                            <div className="h-full rounded-full bg-gold" style={{ width: `${school.confidence}%` }} />
                          </div>
                          <span className="text-gray-400 text-xs">{school.confidence.toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-2 py-2">
                        <button
                          onClick={() => setChartToggles(p => ({ ...p, [school.id]: !p[school.id] }))}
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
            <div className="text-gold font-bold text-xs mb-2">🎯 القرار النهائي — جدول ٤ (مدارس التحليل الفني 25٪)</div>
            <div className="grid grid-cols-6 gap-2">
              {TF_LABELS.map((tf, i) => {
                const bw = schoolData.reduce((s, t) => t.signals[i] === 'buy' ? s + t.weight : s, 0)
                const sw = schoolData.reduce((s, t) => t.signals[i] === 'sell' ? s + t.weight : s, 0)
                const d: Signal = bw > sw ? 'buy' : sw > bw ? 'sell' : 'neutral'
                return (
                  <div key={tf} className="bg-dark-800 rounded-lg p-2 text-center">
                    <div className="text-gray-500 text-xs mb-1">{tf}</div>
                    <SignalBadge s={d} />
                    <div className="text-gray-500 text-xs mt-1">{(Math.max(bw, sw) / 0.25 * 100).toFixed(0)}%</div>
                  </div>
                )
              })}
            </div>
            <div className="mt-2 flex flex-wrap gap-4 text-xs text-gray-400">
              <span>شراء مرجح: <span className="text-buy font-bold">{(buyWeight * 100).toFixed(2)}%</span></span>
              <span>بيع مرجح: <span className="text-sell font-bold">{(sellWeight * 100).toFixed(2)}%</span></span>
              <span>مساهمة الجدول: <span className="text-gold font-bold">{(Math.max(buyWeight, sellWeight) * 100).toFixed(2)}% من 25%</span></span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
