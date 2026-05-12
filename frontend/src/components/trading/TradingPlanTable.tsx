'use client'

import { useState } from 'react'
import { useAppStore } from '@/lib/store'

const LEVERAGE_OPTIONS = [1, 2, 5, 10, 20, 50, 100, 200, 500]

export default function TradingPlanTable() {
  const { language, selectedSymbol, selectedTimeframe } = useAppStore()
  const isRtl = language === 'ar'
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<'plan' | 'ratios' | 'portfolio'>('plan')

  const [capital, setCapital] = useState(10000)
  const [riskPct, setRiskPct] = useState(2)
  const [leverage, setLeverage] = useState(10)
  const [direction, setDirection] = useState<'buy' | 'sell'>('buy')

  const [entry, setEntry] = useState(1983.50)
  const [sl, setSl] = useState(1978.00)
  const [tp1, setTp1] = useState(1990.00)
  const [tp2, setTp2] = useState(1997.00)
  const [tp3, setTp3] = useState(2005.00)
  const [tp4, setTp4] = useState(2015.00)

  const [trailingOn, setTrailingOn] = useState(false)
  const [trailingPct, setTrailingPct] = useState(0.5)
  const [chartToggles, setChartToggles] = useState<Record<string, boolean>>({})

  const riskAmount = (capital * riskPct) / 100
  const slPips = Math.abs(entry - sl)
  const lotSize = slPips > 0 ? riskAmount / (slPips * 10) : 0.01
  const margin = (capital / leverage) * 0.01
  const positionSize = lotSize * leverage

  const rr1 = slPips > 0 ? (Math.abs(tp1 - entry) / slPips).toFixed(2) : '—'
  const rr2 = slPips > 0 ? (Math.abs(tp2 - entry) / slPips).toFixed(2) : '—'
  const rr3 = slPips > 0 ? (Math.abs(tp3 - entry) / slPips).toFixed(2) : '—'
  const rr4 = slPips > 0 ? (Math.abs(tp4 - entry) / slPips).toFixed(2) : '—'

  const dir = direction === 'buy' ? 1 : -1
  const pl1 = ((tp1 - entry) * lotSize * 100 * dir).toFixed(2)
  const pl2 = ((tp2 - entry) * lotSize * 100 * dir).toFixed(2)
  const pl3 = ((tp3 - entry) * lotSize * 100 * dir).toFixed(2)
  const pl4 = ((tp4 - entry) * lotSize * 100 * dir).toFixed(2)
  const maxLoss = (riskAmount * -1).toFixed(2)

  function toggleChart(id: string) {
    setChartToggles(prev => ({ ...prev, [id]: !prev[id] }))
  }

  const trapZones = [
    { label: 'فخ الثيران (Bull Trap)', price: (entry + slPips * 0.3).toFixed(2), risk: 'عالي', color: 'sell' },
    { label: 'فخ الدببة (Bear Trap)', price: (entry - slPips * 0.3).toFixed(2), risk: 'عالي', color: 'buy' },
    { label: 'منطقة اصطياد SL', price: (sl - slPips * 0.1).toFixed(2), risk: 'متوسط', color: 'sell' },
  ]

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">📋</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٨ — خطة التداول الكاملة (Full Trading Plan)
            </div>
            <div className="text-gray-500 text-xs">
              الدخول • SL • TP1-TP4 • حجم اللوت • الرافعة • الهامش • الربح والخسارة المتوقعة
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className={`px-3 py-1 rounded-lg text-xs font-bold border ${
            direction === 'buy' ? 'bg-buy/20 text-buy border-buy/30' : 'bg-sell/20 text-sell border-sell/30'
          }`}>
            {direction === 'buy' ? '▲ شراء' : '▼ بيع'} — {selectedSymbol}
          </div>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4">
          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b border-gold/20 pb-2">
            {[
              { key: 'plan', label: '📋 خطة الصفقة' },
              { key: 'ratios', label: '📐 الأهداف والنسب' },
              { key: 'portfolio', label: '💼 تقييم المحفظة' },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-gold text-dark-900'
                    : 'bg-dark-700 text-gray-400 hover:text-gold'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab: Plan */}
          {activeTab === 'plan' && (
            <div className="space-y-4">
              {/* Settings row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-dark-700/50 rounded-lg p-3">
                  <div className="text-gray-500 text-xs mb-1">الاتجاه</div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setDirection('buy')}
                      className={`flex-1 py-1.5 rounded text-xs font-bold transition-colors ${
                        direction === 'buy' ? 'bg-buy text-white' : 'bg-dark-600 text-gray-400'
                      }`}
                    >
                      ▲ شراء
                    </button>
                    <button
                      onClick={() => setDirection('sell')}
                      className={`flex-1 py-1.5 rounded text-xs font-bold transition-colors ${
                        direction === 'sell' ? 'bg-sell text-white' : 'bg-dark-600 text-gray-400'
                      }`}
                    >
                      ▼ بيع
                    </button>
                  </div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3">
                  <div className="text-gray-500 text-xs mb-1">رأس المال ($)</div>
                  <input
                    type="number"
                    value={capital}
                    onChange={e => setCapital(Number(e.target.value))}
                    className="w-full bg-dark-600 border border-gold/20 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-gold"
                  />
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3">
                  <div className="text-gray-500 text-xs mb-1">نسبة المخاطرة ٪</div>
                  <select
                    value={riskPct}
                    onChange={e => setRiskPct(Number(e.target.value))}
                    className="w-full bg-dark-600 border border-gold/20 rounded px-2 py-1 text-gold text-sm focus:outline-none focus:border-gold"
                  >
                    {[1,2,3,4,5,6,7,8,9,10].map(n => (
                      <option key={n} value={n}>{n}٪</option>
                    ))}
                  </select>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3">
                  <div className="text-gray-500 text-xs mb-1">الرافعة المالية</div>
                  <select
                    value={leverage}
                    onChange={e => setLeverage(Number(e.target.value))}
                    className="w-full bg-dark-600 border border-gold/20 rounded px-2 py-1 text-gold text-sm focus:outline-none focus:border-gold"
                  >
                    {LEVERAGE_OPTIONS.map(l => (
                      <option key={l} value={l}>1:{l}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Entry and SL */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { label: 'سعر الدخول (Entry)', val: entry, set: setEntry, color: 'gold', id: 'entry' },
                  { label: 'وقف الخسارة (Stop Loss)', val: sl, set: setSl, color: 'sell', id: 'sl' },
                ].map(item => (
                  <div key={item.id} className="bg-dark-700/50 rounded-lg p-3">
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-500 text-xs">{item.label}</span>
                      <button
                        onClick={() => toggleChart(item.id)}
                        className={`text-xs px-1.5 py-0.5 rounded transition-colors ${
                          chartToggles[item.id] ? 'bg-gold text-dark-900 font-bold' : 'bg-dark-600 text-gray-500'
                        }`}
                      >
                        {chartToggles[item.id] ? 'ON' : 'OFF'}
                      </button>
                    </div>
                    <input
                      type="number"
                      step="0.01"
                      value={item.val}
                      onChange={e => item.set(Number(e.target.value))}
                      className={`w-full bg-dark-600 border rounded px-2 py-1.5 text-sm font-bold focus:outline-none ${
                        item.color === 'gold' ? 'text-gold border-gold/30 focus:border-gold' :
                        'text-sell border-sell/30 focus:border-sell'
                      }`}
                    />
                  </div>
                ))}
                <div className="bg-dark-700/50 rounded-lg p-3">
                  <div className="text-gray-500 text-xs mb-1">نقاط الـ SL (مسافة الخطر)</div>
                  <div className="text-sell font-bold text-lg">{slPips.toFixed(2)} نقطة</div>
                  <div className="text-gray-500 text-xs">الخسارة القصوى: <span className="text-sell">{maxLoss}$</span></div>
                </div>
              </div>

              {/* Calculated values */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-dark-700/30 rounded-lg p-3 border border-buy/20">
                  <div className="text-gray-500 text-xs">حجم اللوت (Lot Size)</div>
                  <div className="text-buy font-bold text-xl">{lotSize.toFixed(3)}</div>
                  <div className="text-gray-500 text-xs">لوت</div>
                </div>
                <div className="bg-dark-700/30 rounded-lg p-3 border border-gold/20">
                  <div className="text-gray-500 text-xs">حجم المركز</div>
                  <div className="text-gold font-bold text-xl">{positionSize.toFixed(3)}</div>
                  <div className="text-gray-500 text-xs">عقد</div>
                </div>
                <div className="bg-dark-700/30 rounded-lg p-3 border border-purple-500/20">
                  <div className="text-gray-500 text-xs">الهامش المطلوب</div>
                  <div className="text-purple-300 font-bold text-xl">{margin.toFixed(2)}$</div>
                  <div className="text-gray-500 text-xs">رافعة 1:{leverage}</div>
                </div>
                <div className="bg-dark-700/30 rounded-lg p-3 border border-sell/20">
                  <div className="text-gray-500 text-xs">مبلغ المخاطرة</div>
                  <div className="text-sell font-bold text-xl">{riskAmount.toFixed(2)}$</div>
                  <div className="text-gray-500 text-xs">{riskPct}٪ من رأس المال</div>
                </div>
              </div>

              {/* Trailing Stop */}
              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-gold font-bold text-sm">🔁 وقف متحرك (Trailing Stop)</div>
                  <button
                    onClick={() => setTrailingOn(!trailingOn)}
                    className={`px-3 py-1 rounded text-xs font-bold transition-colors ${
                      trailingOn ? 'bg-buy text-white' : 'bg-dark-600 text-gray-400'
                    }`}
                  >
                    {trailingOn ? '✅ مفعّل' : '○ معطّل'}
                  </button>
                </div>
                {trailingOn && (
                  <div className="flex items-center gap-3">
                    <span className="text-gray-400 text-xs">نسبة التحرك:</span>
                    <input
                      type="number"
                      step="0.1"
                      value={trailingPct}
                      onChange={e => setTrailingPct(Number(e.target.value))}
                      className="w-20 bg-dark-600 border border-gold/20 rounded px-2 py-1 text-gold text-sm focus:outline-none focus:border-gold"
                    />
                    <span className="text-gray-500 text-xs">٪ يتبع السعر ويحمي الربح تلقائياً</span>
                  </div>
                )}
              </div>

              {/* Trap Zones */}
              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-3">⚠️ مناطق الفخ (Trap Zones)</div>
                <div className="space-y-2">
                  {trapZones.map((z, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className={z.color === 'sell' ? 'text-sell' : 'text-buy'}>▶</span>
                        <span className="text-gray-300">{z.label}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-white font-bold">{z.price}</span>
                        <span className={`px-2 py-0.5 rounded ${
                          z.risk === 'عالي' ? 'bg-sell/20 text-sell' : 'bg-yellow-700/20 text-yellow-400'
                        }`}>
                          خطر: {z.risk}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab: Targets & Ratios */}
          {activeTab === 'ratios' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { label: 'الهدف الأول (TP1)', val: tp1, set: setTp1, rr: rr1, pl: pl1, id: 'tp1', pct: '٢٥٪ خروج جزئي' },
                  { label: 'الهدف الثاني (TP2)', val: tp2, set: setTp2, rr: rr2, pl: pl2, id: 'tp2', pct: '٢٥٪ خروج جزئي' },
                  { label: 'الهدف الثالث (TP3)', val: tp3, set: setTp3, rr: rr3, pl: pl3, id: 'tp3', pct: '٢٥٪ خروج جزئي' },
                  { label: 'الهدف الرابع (TP4)', val: tp4, set: setTp4, rr: rr4, pl: pl4, id: 'tp4', pct: '٢٥٪ الخروج الكامل' },
                ].map(tp => (
                  <div key={tp.id} className="bg-dark-700/30 rounded-lg p-4 border border-buy/20">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="text-buy font-bold text-sm">{tp.label}</div>
                        <div className="text-gray-500 text-xs">{tp.pct}</div>
                      </div>
                      <button
                        onClick={() => toggleChart(tp.id)}
                        className={`text-xs px-2 py-0.5 rounded transition-colors ${
                          chartToggles[tp.id] ? 'bg-gold text-dark-900 font-bold' : 'bg-dark-600 text-gray-500'
                        }`}
                      >
                        {chartToggles[tp.id] ? 'ON' : 'OFF'}
                      </button>
                    </div>
                    <input
                      type="number"
                      step="0.01"
                      value={tp.val}
                      onChange={e => tp.set(Number(e.target.value))}
                      className="w-full mb-3 bg-dark-600 border border-buy/30 rounded px-2 py-1.5 text-buy text-sm font-bold focus:outline-none focus:border-buy"
                    />
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-dark-600 rounded p-2 text-center">
                        <div className="text-gray-500">نسبة R:R</div>
                        <div className="text-gold font-bold text-lg">1:{tp.rr}</div>
                      </div>
                      <div className="bg-dark-600 rounded p-2 text-center">
                        <div className="text-gray-500">الربح المتوقع</div>
                        <div className="text-buy font-bold text-lg">+{parseFloat(tp.pl).toFixed(0)}$</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Summary table */}
              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-3">ملخص أهداف الصفقة</div>
                <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
                  <thead>
                    <tr className="border-b border-gold/20">
                      <th className="text-gold text-right pb-2 font-medium">الهدف</th>
                      <th className="text-gold text-center pb-2 font-medium">السعر</th>
                      <th className="text-gold text-center pb-2 font-medium">R:R</th>
                      <th className="text-gold text-center pb-2 font-medium">الربح ($)</th>
                      <th className="text-gold text-center pb-2 font-medium">٪ من رأس المال</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: 'TP1 (٢٥٪)', price: tp1, rr: rr1, pl: pl1 },
                      { label: 'TP2 (٢٥٪)', price: tp2, rr: rr2, pl: pl2 },
                      { label: 'TP3 (٢٥٪)', price: tp3, rr: rr3, pl: pl3 },
                      { label: 'TP4 (٢٥٪)', price: tp4, rr: rr4, pl: pl4 },
                    ].map((row, i) => (
                      <tr key={i} className="border-b border-dark-600">
                        <td className="py-2 text-white font-medium">{row.label}</td>
                        <td className="py-2 text-center text-buy font-bold">{row.price.toFixed(2)}</td>
                        <td className="py-2 text-center text-gold font-bold">1:{row.rr}</td>
                        <td className="py-2 text-center text-buy font-bold">+{parseFloat(row.pl).toFixed(0)}</td>
                        <td className="py-2 text-center text-green-400">+{((parseFloat(row.pl) / capital) * 100).toFixed(2)}٪</td>
                      </tr>
                    ))}
                    <tr className="border-t border-sell/30 bg-sell/5">
                      <td className="py-2 text-sell font-bold">SL (وقف الخسارة)</td>
                      <td className="py-2 text-center text-sell font-bold">{sl.toFixed(2)}</td>
                      <td className="py-2 text-center text-gray-500">—</td>
                      <td className="py-2 text-center text-sell font-bold">{maxLoss}$</td>
                      <td className="py-2 text-center text-sell">-{riskPct}٪</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab: Portfolio */}
          {activeTab === 'portfolio' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="bg-dark-700/50 rounded-lg p-4 border border-gold/20 text-center">
                  <div className="text-gray-500 text-xs mb-1">رأس المال الإجمالي</div>
                  <div className="text-gold font-bold text-2xl">{capital.toLocaleString()}$</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-4 border border-sell/20 text-center">
                  <div className="text-gray-500 text-xs mb-1">الحد الأقصى للمخاطرة</div>
                  <div className="text-sell font-bold text-2xl">{riskAmount.toFixed(0)}$</div>
                  <div className="text-gray-500 text-xs">{riskPct}٪ من المحفظة</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-4 border border-buy/20 text-center">
                  <div className="text-gray-500 text-xs mb-1">الربح المحتمل (TP4)</div>
                  <div className="text-buy font-bold text-2xl">+{parseFloat(pl4).toFixed(0)}$</div>
                  <div className="text-gray-500 text-xs">نسبة 1:{rr4}</div>
                </div>
              </div>

              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-3">📊 تقييم المحفظة — {selectedSymbol}</div>
                <div className="space-y-3 text-sm">
                  {[
                    { label: 'إجمالي رأس المال المعرَّض للخطر', value: `${riskAmount.toFixed(2)}$ (${riskPct}٪)`, status: riskPct <= 2 ? 'ممتاز' : riskPct <= 5 ? 'جيد' : 'خطر', color: riskPct <= 2 ? 'buy' : riskPct <= 5 ? 'gold' : 'sell' },
                    { label: 'الرافعة المالية المستخدمة', value: `1:${leverage}`, status: leverage <= 10 ? 'آمن' : leverage <= 50 ? 'معتدل' : 'عالي المخاطر', color: leverage <= 10 ? 'buy' : leverage <= 50 ? 'gold' : 'sell' },
                    { label: 'نسبة المخاطرة/المكافأة الكلية (TP4)', value: `1:${rr4}`, status: parseFloat(rr4 as string) >= 3 ? 'ممتاز' : parseFloat(rr4 as string) >= 2 ? 'جيد' : 'ضعيف', color: parseFloat(rr4 as string) >= 3 ? 'buy' : parseFloat(rr4 as string) >= 2 ? 'gold' : 'sell' },
                    { label: 'حجم اللوت نسبةً لرأس المال', value: `${lotSize.toFixed(3)} لوت`, status: 'محسوب آلياً', color: 'gold' },
                    { label: 'الهامش المحجوز', value: `${margin.toFixed(2)}$`, status: `${((margin / capital) * 100).toFixed(1)}٪ من المحفظة`, color: 'gold' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center justify-between border-b border-dark-600 pb-2">
                      <span className="text-gray-400 text-xs">{item.label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium text-xs">{item.value}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          item.color === 'buy' ? 'bg-buy/20 text-buy' :
                          item.color === 'sell' ? 'bg-sell/20 text-sell' :
                          'bg-gold/20 text-gold'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-3">📋 قواعد إدارة رأس المال — أسد السوق</div>
                <div className="space-y-2 text-xs text-gray-400">
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>لا تُخاطر أبداً بأكثر من ٢٪ من رأس المال في صفقة واحدة</span></div>
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>لا تفتح أكثر من ٣ صفقات متزامنة على نفس الأصل</span></div>
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>إذا خسرت ٦٪ من المحفظة في يوم واحد، أوقف التداول فوراً</span></div>
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>لا تُبقي صفقة خاسرة مفتوحة أملاً في الانعكاس — وقف الخسارة قانون</span></div>
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>اخرج جزئياً عند TP1 وTP2 وحرّك وقف الخسارة لنقطة الدخول</span></div>
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>الرافعة الموصى بها للمبتدئين: 1:10 — للمحترفين: حتى 1:100</span></div>
                  <div className="flex gap-2"><span className="text-gold">◆</span><span>لا تتداول قبل بيانات FOMC أو NFP بدون سبب مؤكد وSL ضيق</span></div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
