'use client'

import { useEffect, useState } from 'react'
import { getTechnicalAnalysis } from '@/lib/api'
import { useAppStore } from '@/lib/store'
import clsx from 'clsx'

const SignalBadge = ({ signal, lang = 'ar' }: { signal: string; lang?: string }) => {
  const ar: Record<string, string> = { buy: 'شراء', sell: 'بيع', neutral: 'محايد', wait: 'انتظر' }
  const en: Record<string, string> = { buy: 'BUY', sell: 'SELL', neutral: 'WAIT', wait: 'WAIT' }
  const cls = signal === 'buy' ? 'badge-buy' : signal === 'sell' ? 'badge-sell' : 'badge-neutral'
  return <span className={cls}>{lang === 'ar' ? (ar[signal] || signal) : (en[signal] || signal)}</span>
}

const Bar = ({ value, color = '#C9A227' }: { value: number; color?: string }) => (
  <div className="flex items-center gap-1.5 flex-1">
    <div className="flex-1 bg-dark-600 rounded-full h-1.5 overflow-hidden">
      <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(value, 100)}%`, background: color }} />
    </div>
    <span className="text-xs text-gray-400 w-7 shrink-0">{Math.round(value)}%</span>
  </div>
)

const signalColor = (s: string) => s === 'buy' ? '#4ADE80' : s === 'sell' ? '#F87171' : '#9CA3AF'

interface AnalysisData {
  signal?: string
  confluence_score?: number
  buy_votes?: number
  sell_votes?: number
  neutral_votes?: number
  total_schools?: number
  should_trade?: boolean
  rejection_reasons?: string[]
  top_factors?: Array<{ school: string; vote: string; strength: number; confidence: number; weight: number }>
  schools?: Record<string, { name: string; signal: string; confidence: number; strength: number; weight: number }>
  indicators?: Record<string, any>
  trend?: string
}

const INDICATOR_LABELS: Record<string, { ar: string; en: string }> = {
  rsi: { ar: 'RSI (14)', en: 'RSI (14)' },
  macd: { ar: 'MACD', en: 'MACD' },
  ema_20: { ar: 'EMA 20', en: 'EMA 20' },
  ema_50: { ar: 'EMA 50', en: 'EMA 50' },
  ema_200: { ar: 'EMA 200', en: 'EMA 200' },
  bollinger: { ar: 'بولنجر باند', en: 'Bollinger Bands' },
  stochastic: { ar: 'ستوكاستك', en: 'Stochastic' },
  adx: { ar: 'ADX', en: 'ADX' },
  atr: { ar: 'ATR', en: 'ATR' },
}

export default function TechnicalTable() {
  const { selectedSymbol, selectedTimeframe, language } = useAppStore()
  const [data, setData] = useState<AnalysisData>({})
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'vote' | 'schools' | 'indicators'>('vote')
  const isRtl = language === 'ar'

  useEffect(() => {
    const fetch = async () => {
      setLoading(true)
      try {
        const res = await getTechnicalAnalysis(selectedSymbol, selectedTimeframe)
        if (res.data && !res.data.error) setData(res.data)
      } catch {}
      setLoading(false)
    }
    fetch()
    const t = setInterval(fetch, 30000)
    return () => clearInterval(t)
  }, [selectedSymbol, selectedTimeframe])

  const sig = data.signal || 'wait'
  const confScore = data.confluence_score || 0
  const confColor = confScore >= 75 ? '#4ADE80' : confScore >= 50 ? '#C9A227' : '#F87171'
  const buyV = data.buy_votes || 0
  const sellV = data.sell_votes || 0
  const neutV = data.neutral_votes || 0
  const total = data.total_schools || 0

  const schoolsList = Object.values(data.schools || {})
  const indicatorsList = Object.entries(data.indicators || {}).filter(([k]) => INDICATOR_LABELS[k])

  return (
    <div className="card-gold h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 shrink-0">
        <div className="flex items-center gap-2">
          <span>📈</span>
          <h3 className="text-gold font-bold text-sm">{isRtl ? 'التحليل الفني — 74 مدرسة' : 'Technical Analysis — 74 Schools'}</h3>
        </div>
        <div className="flex items-center gap-2">
          {loading && <div className="w-3 h-3 border border-gold border-t-transparent rounded-full animate-spin" />}
          <SignalBadge signal={sig} lang={language} />
        </div>
      </div>

      {/* Vote Summary Bar */}
      <div className="grid grid-cols-3 gap-2 mb-2 shrink-0">
        <div className="rounded-lg bg-green-900/20 border border-green-800/30 p-2 text-center">
          <div className="text-green-400 font-black text-xl">{buyV}</div>
          <div className="text-green-600 text-xs">{isRtl ? 'شراء' : 'BUY'}</div>
        </div>
        <div className="rounded-lg bg-red-900/20 border border-red-800/30 p-2 text-center">
          <div className="text-red-400 font-black text-xl">{sellV}</div>
          <div className="text-red-600 text-xs">{isRtl ? 'بيع' : 'SELL'}</div>
        </div>
        <div className="rounded-lg bg-dark-700 border border-dark-600 p-2 text-center">
          <div className="text-gray-400 font-black text-xl">{neutV}</div>
          <div className="text-gray-500 text-xs">{isRtl ? 'محايد' : 'WAIT'}</div>
        </div>
      </div>

      {/* Confluence Score */}
      <div className="flex items-center gap-2 mb-2 p-2 rounded-lg bg-dark-700 shrink-0">
        <span className="text-xs text-gray-400 shrink-0">{isRtl ? 'التقاء المدارس:' : 'Confluence:'}</span>
        <Bar value={confScore} color={confColor} />
        <span className="text-sm font-black shrink-0" style={{ color: confColor }}>{confScore.toFixed(1)}%</span>
      </div>

      {/* Should Trade */}
      {total > 0 && (
        <div className={clsx(
          'mb-2 p-2 rounded-lg text-center text-xs font-bold shrink-0',
          data.should_trade ? 'bg-green-900/20 text-green-400 border border-green-800/40' : 'bg-dark-700 text-gray-500 border border-dark-600'
        )}>
          {data.should_trade
            ? (isRtl ? '✅ شروط الدخول مكتملة' : '✅ Entry Conditions Met')
            : (isRtl ? `⏳ انتظر — ${data.rejection_reasons?.[0] || 'تقاطع غير كافٍ'}` : `⏳ Wait — ${data.rejection_reasons?.[0] || 'Low confluence'}`)}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-2 shrink-0">
        {(['vote', 'schools', 'indicators'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={clsx('px-2 py-1 rounded text-xs font-medium transition-colors flex-1', tab === t ? 'bg-gold text-dark-900' : 'text-gray-400 hover:text-white bg-dark-700')}>
            {t === 'vote' ? (isRtl ? 'الأقوى' : 'Top Factors') : t === 'schools' ? (isRtl ? `المدارس (${total})` : `Schools (${total})`) : (isRtl ? 'المؤشرات' : 'Indicators')}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'vote' && (
          <div className="space-y-1">
            <div className="text-xs text-gray-500 mb-2">{isRtl ? 'أقوى 5 عوامل في القرار:' : 'Top 5 decision factors:'}</div>
            {(data.top_factors || []).map((f, i) => (
              <div key={i} className="flex items-center gap-2 p-1.5 rounded-lg bg-dark-700">
                <span className="text-gold text-xs font-black w-4">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-200 truncate">{f.school}</div>
                  <Bar value={f.strength * 100} color={signalColor(f.vote?.toLowerCase())} />
                </div>
                <SignalBadge signal={f.vote?.toLowerCase()} lang={language} />
              </div>
            ))}
            {(!data.top_factors || data.top_factors.length === 0) && (
              <div className="text-center text-gray-600 text-xs py-8">{isRtl ? 'جاري التحليل...' : 'Analyzing...'}</div>
            )}
          </div>
        )}

        {tab === 'schools' && (
          <div className="space-y-0.5">
            {schoolsList.length === 0 && (
              <div className="text-center text-gray-600 text-xs py-8">{isRtl ? 'جاري تحميل 74 مدرسة...' : 'Loading 74 schools...'}</div>
            )}
            {schoolsList.map((school, i) => (
              <div key={i} className="flex items-center gap-2 py-1 border-b border-dark-700/50">
                <div className="w-28 shrink-0">
                  <div className="text-gray-300 text-xs leading-tight truncate">{school.name}</div>
                </div>
                <Bar value={school.confidence || 0} color={signalColor(school.signal)} />
                <SignalBadge signal={school.signal} lang={language} />
              </div>
            ))}
          </div>
        )}

        {tab === 'indicators' && (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 border-b border-dark-700">
                <th className="text-right pb-1">{isRtl ? 'المؤشر' : 'Indicator'}</th>
                <th className="text-center pb-1">{isRtl ? 'القيمة' : 'Value'}</th>
                <th className="text-center pb-1">{isRtl ? 'الإشارة' : 'Signal'}</th>
              </tr>
            </thead>
            <tbody>
              {indicatorsList.map(([key, val]) => {
                const label = INDICATOR_LABELS[key]
                const value = val?.value ?? val?.macd ?? val?.k ?? '—'
                const sig = val?.signal || val?.signal_type || 'neutral'
                return (
                  <tr key={key} className="border-b border-dark-700/30">
                    <td className="py-1 text-gray-300">{isRtl ? label.ar : label.en}</td>
                    <td className="py-1 text-center text-gray-400">
                      {typeof value === 'number' ? value.toFixed(2) : String(value).slice(0, 8)}
                    </td>
                    <td className="py-1 text-center"><SignalBadge signal={sig} lang={language} /></td>
                  </tr>
                )
              })}
              {indicatorsList.length === 0 && (
                <tr><td colSpan={3} className="text-center text-gray-600 py-4">{isRtl ? 'جاري التحميل...' : 'Loading...'}</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
