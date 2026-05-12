'use client'

import { useState } from 'react'
import { useAppStore } from '@/lib/store'

interface SectionScore {
  id: string
  name: string
  nameEn: string
  icon: string
  maxWeight: number
  score: number
  direction: 'buy' | 'sell' | 'neutral'
  confidence: number
  breakdown: string
}

const SECTION_WEIGHTS = [
  { id: 'fundamental', name: 'التحليل الأساسي', nameEn: 'Fundamental Analysis', icon: '📰', maxWeight: 20 },
  { id: 'core_tools', name: 'الأدوات الأساسية', nameEn: 'Core Tools Analysis', icon: '🔧', maxWeight: 30 },
  { id: 'schools', name: 'مدارس التحليل', nameEn: 'Analysis Schools', icon: '🏛️', maxWeight: 25 },
  { id: 'indicators', name: 'المؤشرات التقنية', nameEn: 'Technical Indicators', icon: '📊', maxWeight: 10 },
  { id: 'order_flow', name: 'تدفق الأوامر', nameEn: 'Order Flow & BookMap', icon: '💹', maxWeight: 15 },
]

const TIMEFRAMES = ['1M', '5M', '15M', '30M', '1H', '4H']

function ConfidenceBar({ value, color = 'gold' }: { value: number; color?: string }) {
  const colorClass = color === 'buy' ? 'bg-buy' : color === 'sell' ? 'bg-sell' : 'bg-gold'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-dark-600 rounded-full overflow-hidden">
        <div className={`h-full ${colorClass} rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{value}٪</span>
    </div>
  )
}

export default function FinalDecisionsTable() {
  const { language, selectedSymbol, selectedTimeframe } = useAppStore()
  const isRtl = language === 'ar'
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<'vote' | 'timeframes' | 'decision'>('vote')

  const sections: SectionScore[] = [
    {
      id: 'fundamental',
      name: 'التحليل الأساسي',
      nameEn: 'Fundamental Analysis',
      icon: '📰',
      maxWeight: 20,
      score: 14.4,
      direction: 'buy',
      confidence: 72,
      breakdown: 'البيانات الاقتصادية: +8 • الأخبار: +4 • الخطابات: +2.4',
    },
    {
      id: 'core_tools',
      name: 'الأدوات الأساسية',
      nameEn: 'Core Tools',
      icon: '🔧',
      maxWeight: 30,
      score: 22.5,
      direction: 'buy',
      confidence: 75,
      breakdown: 'هيكل السوق: +8 • الأدوات S+A: +9 • باقي الأدوات: +5.5',
    },
    {
      id: 'schools',
      name: 'مدارس التحليل',
      nameEn: 'Analysis Schools',
      icon: '🏛️',
      maxWeight: 25,
      score: 17.5,
      direction: 'buy',
      confidence: 70,
      breakdown: 'Tier S: +7 • Tier A: +6 • Tier B: +3.5 • Tier C: +1',
    },
    {
      id: 'indicators',
      name: 'المؤشرات التقنية',
      nameEn: 'Technical Indicators',
      icon: '📊',
      maxWeight: 10,
      score: 6.8,
      direction: 'buy',
      confidence: 68,
      breakdown: 'الاتجاه: +3 • الزخم: +2.2 • التذبذب: +1.6',
    },
    {
      id: 'order_flow',
      name: 'تدفق الأوامر',
      nameEn: 'Order Flow',
      icon: '💹',
      maxWeight: 15,
      score: 10.5,
      direction: 'buy',
      confidence: 70,
      breakdown: 'الأسد المؤسسي: +7 • Delta التراكمي: +2 • الشبل: +1.5',
    },
  ]

  const totalScore = sections.reduce((a, s) => a + s.score, 0)
  const buyScore = sections.filter(s => s.direction === 'buy').reduce((a, s) => a + s.score, 0)
  const sellScore = sections.filter(s => s.direction === 'sell').reduce((a, s) => a + s.score, 0)
  const confluenceScore = Math.round((buyScore / 100) * 100)
  const finalDirection: 'buy' | 'sell' | 'neutral' = confluenceScore >= 75 ? 'buy' : (100 - confluenceScore) >= 75 ? 'sell' : 'neutral'
  const threshold = 75

  const tfDecisions: Record<string, { dir: 'buy' | 'sell' | 'neutral'; score: number }> = {
    '1M': { dir: 'buy', score: 76 },
    '5M': { dir: 'buy', score: 78 },
    '15M': { dir: 'buy', score: 82 },
    '30M': { dir: 'neutral', score: 62 },
    '1H': { dir: 'buy', score: 77 },
    '4H': { dir: 'buy', score: 85 },
  }

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🗳️</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٧ — القرار النهائي والتصويت الموزون (Final Decision)
            </div>
            <div className="text-gray-500 text-xs">
              التجميع الموزون لكل الجداول الخمسة • نقطة التقاطع ≥ ٧٥٪ للدخول
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className={`px-3 py-1 rounded-lg text-xs font-bold border ${
            finalDirection === 'buy' ? 'bg-buy/20 text-buy border-buy/30' :
            finalDirection === 'sell' ? 'bg-sell/20 text-sell border-sell/30' :
            'bg-gray-700/30 text-gray-400 border-gray-600'
          }`}>
            {finalDirection === 'buy' ? '▲ شراء أسد' : finalDirection === 'sell' ? '▼ بيع أسد' : '— انتظار'}
            {' '}{confluenceScore}٪
          </div>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4">
          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b border-gold/20 pb-2">
            {[
              { key: 'vote', label: '🗳️ التصويت الموزون' },
              { key: 'timeframes', label: '⏱️ الأطر الزمنية' },
              { key: 'decision', label: '🦁 قرار الأسد النهائي' },
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

          {/* Tab: Weighted Vote */}
          {activeTab === 'vote' && (
            <div className="space-y-4">
              {/* Score Overview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-dark-700/50 rounded-lg p-3 border border-gold/20 text-center">
                  <div className="text-gray-500 text-xs mb-1">مجموع النقاط</div>
                  <div className="text-gold font-bold text-2xl">{totalScore.toFixed(1)}</div>
                  <div className="text-gray-500 text-xs">من أصل ١٠٠</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3 border border-buy/20 text-center">
                  <div className="text-gray-500 text-xs mb-1">نقاط الشراء</div>
                  <div className="text-buy font-bold text-2xl">{buyScore.toFixed(1)}</div>
                  <div className="text-gray-500 text-xs">٪ شراء</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3 border border-sell/20 text-center">
                  <div className="text-gray-500 text-xs mb-1">نقاط البيع</div>
                  <div className="text-sell font-bold text-2xl">{sellScore.toFixed(1)}</div>
                  <div className="text-gray-500 text-xs">٪ بيع</div>
                </div>
                <div className={`bg-dark-700/50 rounded-lg p-3 text-center border ${
                  confluenceScore >= threshold ? 'border-buy/30' : 'border-gold/20'
                }`}>
                  <div className="text-gray-500 text-xs mb-1">Confluence Score</div>
                  <div className={`font-bold text-2xl ${confluenceScore >= threshold ? 'text-buy' : 'text-gold'}`}>
                    {confluenceScore}٪
                  </div>
                  <div className={`text-xs ${confluenceScore >= threshold ? 'text-buy' : 'text-yellow-500'}`}>
                    {confluenceScore >= threshold ? '✅ أعلى من العتبة' : `⚠️ دون العتبة (${threshold}٪)`}
                  </div>
                </div>
              </div>

              {/* Threshold indicator */}
              <div className="bg-dark-700/30 rounded-lg p-3 border border-gold/10">
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-gray-500">نقطة التقاطع الفعلية</span>
                  <span className="text-gold font-bold">{confluenceScore}٪</span>
                </div>
                <div className="relative h-6 bg-dark-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${confluenceScore >= threshold ? 'bg-buy' : 'bg-yellow-600'}`}
                    style={{ width: `${confluenceScore}%` }}
                  />
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white/60"
                    style={{ left: `${threshold}%` }}
                  />
                  <span
                    className="absolute top-0 text-xs text-white/60 font-bold"
                    style={{ left: `${threshold}%`, transform: 'translateX(-50%)', lineHeight: '1.5rem', paddingLeft: '2px' }}
                  >
                    {threshold}٪
                  </span>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span className="text-sell">بيع</span>
                  <span className="text-gray-500">عتبة الدخول: {threshold}٪</span>
                  <span className="text-buy">شراء</span>
                </div>
              </div>

              {/* Per-section table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir={isRtl ? 'rtl' : 'ltr'}>
                  <thead>
                    <tr className="border-b border-gold/20">
                      <th className="text-gold text-right pb-2 pr-2 font-medium">#</th>
                      <th className="text-gold text-right pb-2 pr-3 font-medium">القسم</th>
                      <th className="text-gold text-center pb-2 font-medium">الوزن الأقصى</th>
                      <th className="text-gold text-center pb-2 font-medium">النقاط المحققة</th>
                      <th className="text-gold text-center pb-2 font-medium">الاتجاه</th>
                      <th className="text-gold text-right pb-2 pr-3 font-medium">شريط الثقة</th>
                      <th className="text-gold text-right pb-2 font-medium">التفاصيل</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sections.map((sec, idx) => (
                      <tr key={sec.id} className="border-b border-dark-600 hover:bg-dark-700/30 transition-colors">
                        <td className="py-3 pr-2 text-gray-500 font-bold">{idx + 1}</td>
                        <td className="py-3 pr-3">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{sec.icon}</span>
                            <div>
                              <div className="text-white font-medium text-sm">{sec.name}</div>
                              <div className="text-gray-500 text-xs">{sec.nameEn}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 text-center">
                          <span className="text-gold font-bold">{sec.maxWeight}٪</span>
                        </td>
                        <td className="py-3 text-center">
                          <span className={`font-bold text-lg ${
                            sec.direction === 'buy' ? 'text-buy' :
                            sec.direction === 'sell' ? 'text-sell' : 'text-gray-400'
                          }`}>
                            {sec.score.toFixed(1)}
                          </span>
                          <div className="text-gray-500 text-xs">
                            ({Math.round((sec.score / sec.maxWeight) * 100)}٪ من الوزن)
                          </div>
                        </td>
                        <td className="py-3 text-center">
                          {sec.direction === 'buy' ? (
                            <span className="text-buy font-bold text-xs bg-buy/10 px-2 py-1 rounded">▲ شراء</span>
                          ) : sec.direction === 'sell' ? (
                            <span className="text-sell font-bold text-xs bg-sell/10 px-2 py-1 rounded">▼ بيع</span>
                          ) : (
                            <span className="text-gray-400 text-xs bg-gray-700/30 px-2 py-1 rounded">— محايد</span>
                          )}
                        </td>
                        <td className="py-3 pr-3 min-w-[120px]">
                          <ConfidenceBar
                            value={sec.confidence}
                            color={sec.direction === 'buy' ? 'buy' : sec.direction === 'sell' ? 'sell' : 'gold'}
                          />
                        </td>
                        <td className="py-3 text-gray-400 text-xs max-w-[200px]">{sec.breakdown}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-gold/30 bg-dark-700/30">
                      <td colSpan={2} className="py-3 pr-2 text-gold font-bold">المجموع الموزون الكلي</td>
                      <td className="py-3 text-center text-gold font-bold">١٠٠٪</td>
                      <td className="py-3 text-center">
                        <span className={`font-bold text-xl ${finalDirection === 'buy' ? 'text-buy' : finalDirection === 'sell' ? 'text-sell' : 'text-gray-400'}`}>
                          {totalScore.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <span className={`font-bold text-sm ${finalDirection === 'buy' ? 'text-buy' : finalDirection === 'sell' ? 'text-sell' : 'text-gray-400'}`}>
                          {finalDirection === 'buy' ? '▲ شراء' : finalDirection === 'sell' ? '▼ بيع' : '— انتظار'}
                        </span>
                      </td>
                      <td className="py-3 pr-3 min-w-[120px]">
                        <ConfidenceBar value={confluenceScore} color={finalDirection === 'buy' ? 'buy' : finalDirection === 'sell' ? 'sell' : 'gold'} />
                      </td>
                      <td className="py-3 text-gray-400 text-xs">
                        Confluence: {confluenceScore}٪ {confluenceScore >= threshold ? '✅' : '⚠️'}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          {/* Tab: Timeframes */}
          {activeTab === 'timeframes' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {TIMEFRAMES.map(tf => {
                  const dec = tfDecisions[tf]
                  return (
                    <div
                      key={tf}
                      className={`bg-dark-700/30 rounded-lg p-4 border ${
                        dec.dir === 'buy' ? 'border-buy/30' :
                        dec.dir === 'sell' ? 'border-sell/30' :
                        'border-gray-600'
                      } ${tf === selectedTimeframe ? 'ring-1 ring-gold' : ''}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="text-gold font-bold">{tf}</div>
                        {tf === selectedTimeframe && (
                          <span className="text-xs bg-gold text-dark-900 px-1.5 py-0.5 rounded font-bold">مختار</span>
                        )}
                      </div>
                      <div className={`text-2xl font-bold ${
                        dec.dir === 'buy' ? 'text-buy' :
                        dec.dir === 'sell' ? 'text-sell' :
                        'text-gray-400'
                      }`}>
                        {dec.score}٪
                      </div>
                      <div className={`text-sm font-medium mt-1 ${
                        dec.dir === 'buy' ? 'text-buy' :
                        dec.dir === 'sell' ? 'text-sell' :
                        'text-gray-400'
                      }`}>
                        {dec.dir === 'buy' ? '▲ شراء' : dec.dir === 'sell' ? '▼ بيع' : '— انتظار'}
                      </div>
                      <div className="mt-2">
                        <ConfidenceBar value={dec.score} color={dec.dir} />
                      </div>
                      <div className={`mt-2 text-xs ${dec.score >= threshold ? 'text-buy' : 'text-yellow-500'}`}>
                        {dec.score >= threshold ? '✅ يمكن الدخول' : `⚠️ دون ${threshold}٪`}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Summary by TF */}
              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-3">تحليل التوافق عبر الأطر الزمنية</div>
                <div className="space-y-2 text-xs text-gray-400">
                  <div className="flex items-center gap-2">
                    <span className="text-buy">✅</span>
                    <span>الأطر المؤهلة للدخول (≥{threshold}٪):</span>
                    <span className="text-buy font-bold">
                      {TIMEFRAMES.filter(tf => tfDecisions[tf].score >= threshold).join('، ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-500">⚠️</span>
                    <span>الأطر الغير مؤهلة (&lt;{threshold}٪):</span>
                    <span className="text-yellow-500 font-bold">
                      {TIMEFRAMES.filter(tf => tfDecisions[tf].score < threshold).join('، ') || 'لا يوجد'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gold">🎯</span>
                    <span>الإطار المختار للتداول:</span>
                    <span className="text-gold font-bold">{selectedTimeframe}</span>
                    <span className={tfDecisions[selectedTimeframe]?.score >= threshold ? 'text-buy' : 'text-yellow-500'}>
                      {tfDecisions[selectedTimeframe]?.score >= threshold ? '✅ مؤهل' : '⚠️ غير مؤهل حالياً'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab: Final Lion Decision */}
          {activeTab === 'decision' && (
            <div className="space-y-4">
              {/* The big decision */}
              <div className={`rounded-xl p-6 border-2 text-center ${
                finalDirection === 'buy'
                  ? 'bg-buy/10 border-buy/50'
                  : finalDirection === 'sell'
                  ? 'bg-sell/10 border-sell/50'
                  : 'bg-dark-700/30 border-gray-600'
              }`}>
                <div className="text-4xl mb-3">
                  {finalDirection === 'buy' ? '🦁📈' : finalDirection === 'sell' ? '🦁📉' : '🦁⏸️'}
                </div>
                <div className={`text-3xl font-bold mb-2 ${
                  finalDirection === 'buy' ? 'text-buy' :
                  finalDirection === 'sell' ? 'text-sell' :
                  'text-gray-400'
                }`}>
                  {finalDirection === 'buy' ? 'قرار الأسد: شراء ▲' :
                   finalDirection === 'sell' ? 'قرار الأسد: بيع ▼' :
                   'قرار الأسد: انتظار ⏸'}
                </div>
                <div className="text-gray-400 text-sm mb-4">
                  {selectedSymbol} — الإطار: {selectedTimeframe} — Confluence Score: {confluenceScore}٪
                </div>
                <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-lg ${
                  finalDirection === 'buy' ? 'bg-buy text-white' :
                  finalDirection === 'sell' ? 'bg-sell text-white' :
                  'bg-gray-700 text-gray-300'
                }`}>
                  {finalDirection === 'buy' ? '✅ الدخول مسموح — نقطة التقاطع تجاوزت ٧٥٪' :
                   finalDirection === 'sell' ? '✅ الدخول مسموح — نقطة التقاطع تجاوزت ٧٥٪' :
                   '⏸️ لا يُنصح بالدخول — نقطة التقاطع دون ٧٥٪'}
                </div>
              </div>

              {/* Contribution breakdown */}
              <div className="space-y-2">
                <div className="text-gold font-bold text-sm mb-2">إسهام كل قسم في قرار الأسد</div>
                {sections.map(sec => (
                  <div key={sec.id} className="flex items-center gap-3">
                    <span className="text-base w-6">{sec.icon}</span>
                    <span className="text-gray-400 text-xs w-32 truncate">{sec.name}</span>
                    <div className="flex-1">
                      <div className="h-3 bg-dark-600 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${sec.direction === 'buy' ? 'bg-buy' : sec.direction === 'sell' ? 'bg-sell' : 'bg-gray-500'}`}
                          style={{ width: `${(sec.score / sec.maxWeight) * 100}%` }}
                        />
                      </div>
                    </div>
                    <span className={`text-xs font-bold w-16 text-right ${
                      sec.direction === 'buy' ? 'text-buy' : sec.direction === 'sell' ? 'text-sell' : 'text-gray-400'
                    }`}>
                      {sec.score.toFixed(1)} / {sec.maxWeight}
                    </span>
                    <span className="text-xs text-gray-500 w-8">{Math.round((sec.score / sec.maxWeight) * 100)}٪</span>
                  </div>
                ))}
              </div>

              {/* Warning / Recommendation */}
              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-2">📋 توصيات الأسد</div>
                <div className="space-y-2 text-xs text-gray-400">
                  {confluenceScore >= threshold ? (
                    <>
                      <div className="flex gap-2"><span className="text-buy">✅</span><span>نقطة التقاطع ({confluenceScore}٪) أعلى من العتبة ({threshold}٪) — الدخول مسموح</span></div>
                      <div className="flex gap-2"><span className="text-buy">✅</span><span>جميع الجداول الخمسة تشير لنفس الاتجاه — توافق عالٍ</span></div>
                      <div className="flex gap-2"><span className="text-gold">⚡</span><span>راجع جدول خطة التداول (٨) لتحديد نقطة الدخول الدقيقة و SL/TP</span></div>
                      <div className="flex gap-2"><span className="text-gold">⚡</span><span>لا تتجاوز نسبة المخاطرة المحددة في جدول خيارات المتداول</span></div>
                    </>
                  ) : (
                    <>
                      <div className="flex gap-2"><span className="text-yellow-500">⚠️</span><span>نقطة التقاطع ({confluenceScore}٪) دون العتبة ({threshold}٪) — لا يُنصح بالدخول الآن</span></div>
                      <div className="flex gap-2"><span className="text-yellow-500">⚠️</span><span>انتظر تحسن إشارات جدول الأدوات أو المدارس</span></div>
                      <div className="flex gap-2"><span className="text-gray-500">ℹ️</span><span>تابع الأطر الزمنية الأعلى للتأكيد على الاتجاه العام</span></div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
