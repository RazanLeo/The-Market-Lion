'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'

const TF_LABELS = ['1M', '5M', '15M', '30M', '1H', '4H']
type Signal = 'buy' | 'sell' | 'neutral'
const rand = (): Signal => (['buy', 'sell', 'neutral'] as Signal[])[Math.floor(Math.random() * 3)]

const INDICATORS = [
  // Trend
  { id: 1, cat: 'أ. مؤشرات الاتجاه', name: 'Parabolic SAR', weight: 0.0019 },
  { id: 2, cat: 'أ. مؤشرات الاتجاه', name: 'Supertrend', weight: 0.0019 },
  { id: 3, cat: 'أ. مؤشرات الاتجاه', name: 'WMA — Weighted Moving Average', weight: 0.0009 },
  { id: 4, cat: 'أ. مؤشرات الاتجاه', name: 'HMA — Hull Moving Average', weight: 0.0009 },
  { id: 5, cat: 'أ. مؤشرات الاتجاه', name: 'VWMA — Volume Weighted MA', weight: 0.0009 },
  { id: 6, cat: 'أ. مؤشرات الاتجاه', name: 'DEMA — Double Exponential MA', weight: 0.0009 },
  { id: 7, cat: 'أ. مؤشرات الاتجاه', name: 'TEMA — Triple Exponential MA', weight: 0.0009 },
  { id: 8, cat: 'أ. مؤشرات الاتجاه', name: 'KAMA — Kaufman Adaptive MA', weight: 0.0019 },
  { id: 9, cat: 'أ. مؤشرات الاتجاه', name: 'ALMA — Arnaud Legoux MA', weight: 0.0009 },
  { id: 10, cat: 'أ. مؤشرات الاتجاه', name: 'McGinley Dynamic', weight: 0.0009 },
  { id: 11, cat: 'أ. مؤشرات الاتجاه', name: 'Volatility Stop', weight: 0.0009 },
  // Momentum
  { id: 12, cat: 'ب. مؤشرات الزخم', name: 'MACD', weight: 0.0019 },
  { id: 13, cat: 'ب. مؤشرات الزخم', name: 'Stochastic Oscillator', weight: 0.0019 },
  { id: 14, cat: 'ب. مؤشرات الزخم', name: 'Stochastic RSI', weight: 0.0019 },
  { id: 15, cat: 'ب. مؤشرات الزخم', name: 'ADX + DMI', weight: 0.0019 },
  { id: 16, cat: 'ب. مؤشرات الزخم', name: 'CCI — Commodity Channel Index', weight: 0.0019 },
  { id: 17, cat: 'ب. مؤشرات الزخم', name: 'Williams %R', weight: 0.0009 },
  { id: 18, cat: 'ب. مؤشرات الزخم', name: 'ROC — Rate of Change', weight: 0.0009 },
  { id: 19, cat: 'ب. مؤشرات الزخم', name: 'Momentum', weight: 0.0009 },
  { id: 20, cat: 'ب. مؤشرات الزخم', name: 'Awesome Oscillator', weight: 0.0009 },
  { id: 21, cat: 'ب. مؤشرات الزخم', name: 'Ultimate Oscillator', weight: 0.0009 },
  { id: 22, cat: 'ب. مؤشرات الزخم', name: 'TRIX', weight: 0.0009 },
  { id: 23, cat: 'ب. مؤشرات الزخم', name: 'Aroon Indicator + Aroon Oscillator', weight: 0.0009 },
  { id: 24, cat: 'ب. مؤشرات الزخم', name: 'Vortex Indicator (VI)', weight: 0.0009 },
  { id: 25, cat: 'ب. مؤشرات الزخم', name: 'Coppock Curve', weight: 0.0009 },
  { id: 26, cat: 'ب. مؤشرات الزخم', name: 'Chande Momentum Oscillator', weight: 0.0009 },
  // Volatility
  { id: 27, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Bollinger Bands', weight: 0.0019 },
  { id: 28, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'ATR — Average True Range', weight: 0.0019 },
  { id: 29, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Keltner Channels', weight: 0.0009 },
  { id: 30, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Donchian Channels', weight: 0.0009 },
  { id: 31, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Historical Volatility', weight: 0.0009 },
  { id: 32, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Choppiness Index', weight: 0.0009 },
  { id: 33, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Chaikin Volatility', weight: 0.0009 },
  { id: 34, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Mass Index', weight: 0.0009 },
  { id: 35, cat: 'ج. مؤشرات التذبذب والتقلب', name: 'Volatility Index', weight: 0.0009 },
  // Volume/Flow
  { id: 36, cat: 'د. مؤشرات الحجم والتدفق', name: 'OBV — On Balance Volume', weight: 0.0019 },
  { id: 37, cat: 'د. مؤشرات الحجم والتدفق', name: 'MFI — Money Flow Index', weight: 0.0019 },
  { id: 38, cat: 'د. مؤشرات الحجم والتدفق', name: 'Accumulation / Distribution', weight: 0.0009 },
  { id: 39, cat: 'د. مؤشرات الحجم والتدفق', name: 'Chaikin Money Flow', weight: 0.0009 },
  { id: 40, cat: 'د. مؤشرات الحجم والتدفق', name: 'Chaikin Oscillator', weight: 0.0009 },
  { id: 41, cat: 'د. مؤشرات الحجم والتدفق', name: 'Klinger Oscillator', weight: 0.0009 },
  { id: 42, cat: 'د. مؤشرات الحجم والتدفق', name: 'Force Index', weight: 0.0009 },
  { id: 43, cat: 'د. مؤشرات الحجم والتدفق', name: 'Ease of Movement', weight: 0.0009 },
  { id: 44, cat: 'د. مؤشرات الحجم والتدفق', name: 'Volume Oscillator', weight: 0.0009 },
  { id: 45, cat: 'د. مؤشرات الحجم والتدفق', name: 'PVI — Positive Volume Index', weight: 0.0009 },
  { id: 46, cat: 'د. مؤشرات الحجم والتدفق', name: 'NVI — Negative Volume Index', weight: 0.0009 },
  // Institutional
  { id: 47, cat: 'هـ. مؤشرات السلوك المؤسسي', name: 'VWAP الأساسي', weight: 0.0019 },
  { id: 48, cat: 'هـ. مؤشرات السلوك المؤسسي', name: 'Anchored VWAP', weight: 0.0019 },
  { id: 49, cat: 'هـ. مؤشرات السلوك المؤسسي', name: 'VWAP with Standard Deviation Bands', weight: 0.0009 },
  // Systems
  { id: 50, cat: 'و. مؤشرات الأنظمة المتكاملة', name: 'Ichimoku Cloud (Kinko Hyo)', weight: 0.0019 },
  { id: 51, cat: 'و. مؤشرات الأنظمة المتكاملة', name: 'Bollinger %B + Bandwidth', weight: 0.0009 },
  { id: 52, cat: 'و. مؤشرات الأنظمة المتكاملة', name: 'McClellan Oscillator', weight: 0.0009 },
  { id: 53, cat: 'و. مؤشرات الأنظمة المتكاملة', name: 'Arms Index (TRIN)', weight: 0.0009 },
  { id: 54, cat: 'و. مؤشرات الأنظمة المتكاملة', name: 'Advance / Decline Line', weight: 0.0009 },
]

const catColor: Record<string, string> = {
  'أ. مؤشرات الاتجاه': 'text-blue-400',
  'ب. مؤشرات الزخم': 'text-purple-400',
  'ج. مؤشرات التذبذب والتقلب': 'text-orange-400',
  'د. مؤشرات الحجم والتدفق': 'text-green-400',
  'هـ. مؤشرات السلوك المؤسسي': 'text-gold',
  'و. مؤشرات الأنظمة المتكاملة': 'text-red-400',
}

const SignalBadge = ({ s }: { s: Signal }) => {
  if (s === 'buy') return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-buy text-white">شراء</span>
  if (s === 'sell') return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-sell text-white">بيع</span>
  return <span className="px-1.5 py-0.5 rounded text-xs font-bold bg-dark-600 text-gray-400">محايد</span>
}

export default function IndicatorsTable() {
  const { language, selectedSymbol, selectedTimeframe } = useAppStore()
  const isRtl = language === 'ar'
  const [collapsed, setCollapsed] = useState(false)
  const [chartToggles, setChartToggles] = useState<Record<number, boolean>>({})
  const [catFilter, setCatFilter] = useState('all')
  const [lastUpdate, setLastUpdate] = useState(new Date())

  const [indData] = useState(() =>
    INDICATORS.map(ind => ({
      ...ind,
      signals: TF_LABELS.map(() => rand()),
      value: (Math.random() * 100).toFixed(2),
      confidence: 40 + Math.random() * 55,
    }))
  )

  useEffect(() => {
    const t = setInterval(() => setLastUpdate(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

  const cats = ['all', ...Array.from(new Set(INDICATORS.map(i => i.cat)))]
  const filtered = catFilter === 'all' ? indData : indData.filter(i => i.cat === catFilter)

  const tfIdx = Math.max(0, TF_LABELS.indexOf(selectedTimeframe))
  const buyW = indData.reduce((s, i) => i.signals[tfIdx] === 'buy' ? s + i.weight : s, 0)
  const sellW = indData.reduce((s, i) => i.signals[tfIdx] === 'sell' ? s + i.weight : s, 0)
  const decision: Signal = buyW > sellW ? 'buy' : sellW > buyW ? 'sell' : 'neutral'

  // Group by category for display
  const groups = cats.filter(c => c !== 'all').map(cat => ({
    cat,
    items: filtered.filter(i => i.cat === cat),
  })).filter(g => g.items.length > 0)

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">📈</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٥ — التحليل الفني / جميع المؤشرات الفنية — الوزن <span className="text-white">10٪</span> من التحليل الكامل • 54 مؤشر
            </div>
            <div className="text-gray-500 text-xs">
              {selectedSymbol} — {selectedTimeframe} • آخر تحديث: {lastUpdate.toLocaleTimeString('ar-SA')}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <SignalBadge s={decision} />
          <span className="text-gray-400 text-xs">{(Math.max(buyW, sellW) / 0.1 * 100).toFixed(0)}%</span>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <>
          {/* Category Filter */}
          <div className="flex flex-wrap gap-1 p-3 border-b border-gold/20 bg-dark-700/20 overflow-x-auto">
            <button
              onClick={() => setCatFilter('all')}
              className={`px-2 py-1 rounded text-xs whitespace-nowrap transition-colors ${
                catFilter === 'all' ? 'bg-gold text-dark-900 font-bold' : 'bg-dark-600 text-gray-400 hover:text-gold'
              }`}
            >
              الكل (54)
            </button>
            {cats.filter(c => c !== 'all').map(cat => (
              <button
                key={cat}
                onClick={() => setCatFilter(cat)}
                className={`px-2 py-1 rounded text-xs whitespace-nowrap transition-colors ${
                  catFilter === cat ? 'bg-gold text-dark-900 font-bold' : 'bg-dark-600 text-gray-400 hover:text-gold'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
              <thead className="bg-dark-700/50">
                <tr>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 w-8">#</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 min-w-[180px]">المؤشر الفني</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 hidden md:table-cell">التصنيف</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">القيمة الحالية</th>
                  {TF_LABELS.map(tf => (
                    <th key={tf} className="px-1 py-2 text-gold text-center font-medium border-b border-gold/20 w-14">{tf}</th>
                  ))}
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">نتيجة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">وزن</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">ثقة</th>
                  <th className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20">شارت</th>
                </tr>
              </thead>
              <tbody>
                {(catFilter === 'all' ? groups : [{ cat: catFilter, items: filtered }]).map(group => (
                  <>
                    {catFilter === 'all' && (
                      <tr key={`cat-${group.cat}`} className="bg-dark-700/40">
                        <td colSpan={13} className={`px-3 py-1.5 font-bold text-xs ${catColor[group.cat] || 'text-gold'}`}>
                          {group.cat} ({group.items.length} مؤشر)
                        </td>
                      </tr>
                    )}
                    {group.items.map(ind => {
                      const buyCnt = ind.signals.filter(s => s === 'buy').length
                      const sellCnt = ind.signals.filter(s => s === 'sell').length
                      const overall: Signal = buyCnt > sellCnt ? 'buy' : sellCnt > buyCnt ? 'sell' : 'neutral'
                      const isOn = chartToggles[ind.id] || false

                      return (
                        <tr key={ind.id} className="border-b border-dark-600 hover:bg-dark-700/30">
                          <td className="px-2 py-2 text-gray-500">{ind.id}</td>
                          <td className="px-2 py-2 text-white">{ind.name}</td>
                          <td className={`px-2 py-2 hidden md:table-cell text-xs ${catColor[ind.cat] || 'text-gray-400'}`}>{ind.cat}</td>
                          <td className="px-2 py-2 text-gold font-bold">{ind.value}</td>
                          {ind.signals.map((sig, i) => (
                            <td key={i} className="px-1 py-2 text-center"><SignalBadge s={sig} /></td>
                          ))}
                          <td className="px-2 py-2"><SignalBadge s={overall} /></td>
                          <td className="px-2 py-2 text-gold">{(ind.weight * 100).toFixed(3)}%</td>
                          <td className="px-2 py-2">
                            <div className="flex items-center gap-1">
                              <div className="bg-dark-600 rounded-full h-1 w-8">
                                <div className="h-full rounded-full bg-gold" style={{ width: `${ind.confidence}%` }} />
                              </div>
                              <span className="text-gray-400 text-xs">{ind.confidence.toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="px-2 py-2">
                            <button
                              onClick={() => setChartToggles(p => ({ ...p, [ind.id]: !p[ind.id] }))}
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
                  </>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="p-3 border-t border-gold/20 bg-dark-700/30">
            <div className="text-gold font-bold text-xs mb-2">🎯 القرار النهائي — جدول ٥ (المؤشرات الفنية 10٪)</div>
            <div className="grid grid-cols-6 gap-2">
              {TF_LABELS.map((tf, i) => {
                const bw = indData.reduce((s, t) => t.signals[i] === 'buy' ? s + t.weight : s, 0)
                const sw = indData.reduce((s, t) => t.signals[i] === 'sell' ? s + t.weight : s, 0)
                const d: Signal = bw > sw ? 'buy' : sw > bw ? 'sell' : 'neutral'
                return (
                  <div key={tf} className="bg-dark-800 rounded-lg p-2 text-center">
                    <div className="text-gray-500 text-xs mb-1">{tf}</div>
                    <SignalBadge s={d} />
                    <div className="text-gray-500 text-xs mt-1">{(Math.max(bw, sw) / 0.1 * 100).toFixed(0)}%</div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
