'use client'

import { useEffect, useState } from 'react'
import { getTechnicalAnalysis } from '@/lib/api'
import { MOCK_TECHNICAL } from '@/lib/mockData'
import { useAppStore } from '@/lib/store'
import type { TechnicalAnalysis } from '@/types'
import clsx from 'clsx'

const SignalBadge = ({ signal, lang = 'ar' }: { signal: string; lang?: string }) => {
  const labels: Record<string, Record<string, string>> = {
    ar: { buy: 'شراء', sell: 'بيع', neutral: 'محايد' },
    en: { buy: 'BUY', sell: 'SELL', neutral: 'NEUT' },
  }
  const cls = signal === 'buy' ? 'badge-buy' : signal === 'sell' ? 'badge-sell' : 'badge-neutral'
  return <span className={cls}>{labels[lang]?.[signal] || signal}</span>
}

const ConfidenceBar = ({ value, color = '#C9A227' }: { value: number; color?: string }) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 bg-dark-600 rounded-full h-1.5 overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${value}%`, background: color }}
      />
    </div>
    <span className="text-xs text-gray-400 w-8">{value}%</span>
  </div>
)

const TIMEFRAMES_ORDER = ['M15', 'H1', 'H4', 'D1', 'W1']

export default function TechnicalTable() {
  const { selectedSymbol, selectedTimeframe, language } = useAppStore()
  const [data, setData] = useState<TechnicalAnalysis>(MOCK_TECHNICAL)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'indicators' | 'schools'>('indicators')
  const isRtl = language === 'ar'

  useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true)
      try {
        const res = await getTechnicalAnalysis(selectedSymbol, selectedTimeframe)
        if (res.data) setData(res.data)
      } catch {
        setData(MOCK_TECHNICAL)
      } finally {
        setLoading(false)
      }
    }
    fetchAnalysis()
    const interval = setInterval(fetchAnalysis, 30000)
    return () => clearInterval(interval)
  }, [selectedSymbol, selectedTimeframe])

  const confluenceColor = data.confluence_score >= 75 ? '#4ADE80' :
    data.confluence_score >= 50 ? '#C9A227' : '#F87171'

  const overallLabel = () => {
    if (data.overall_signal === 'buy' && data.confidence >= 70) return isRtl ? 'شراء قوي ↑' : 'Strong BUY ↑'
    if (data.overall_signal === 'buy') return isRtl ? 'شراء ↑' : 'BUY ↑'
    if (data.overall_signal === 'sell' && data.confidence >= 70) return isRtl ? 'بيع قوي ↓' : 'Strong SELL ↓'
    if (data.overall_signal === 'sell') return isRtl ? 'بيع ↓' : 'SELL ↓'
    return isRtl ? 'انتظر →' : 'WAIT →'
  }

  return (
    <div className="card-gold h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-lg">📈</span>
          <h3 className="text-gold font-bold text-sm">
            {isRtl ? 'التحليل الفني' : 'Technical Analysis'}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {loading && <div className="w-3 h-3 border border-gold border-t-transparent rounded-full animate-spin" />}
          {/* Overall Signal */}
          <div
            className="px-3 py-1 rounded-lg text-xs font-bold"
            style={{
              background: data.overall_signal === 'buy' ? 'rgba(14,122,44,0.2)' :
                data.overall_signal === 'sell' ? 'rgba(176,20,12,0.2)' : 'rgba(160,160,160,0.1)',
              color: data.overall_signal === 'buy' ? '#4ADE80' :
                data.overall_signal === 'sell' ? '#F87171' : '#A0A0A0',
              border: `1px solid ${data.overall_signal === 'buy' ? 'rgba(14,122,44,0.4)' :
                data.overall_signal === 'sell' ? 'rgba(176,20,12,0.4)' : 'rgba(160,160,160,0.2)'}`,
            }}
          >
            {overallLabel()}
          </div>
        </div>
      </div>

      {/* Confluence Score */}
      <div className="flex items-center gap-3 mb-3 p-2 rounded-lg bg-dark-700 shrink-0">
        <span className="text-xs text-gray-400">{isRtl ? 'درجة التقاء المدارس:' : 'Confluence Score:'}</span>
        <div className="flex-1">
          <ConfidenceBar value={data.confluence_score} color={confluenceColor} />
        </div>
        <span className="text-sm font-bold" style={{ color: confluenceColor }}>
          {data.confluence_score}%
        </span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-3 shrink-0">
        <button
          onClick={() => setActiveTab('indicators')}
          className={clsx('px-3 py-1 rounded text-xs font-medium transition-colors', activeTab === 'indicators' ? 'bg-gold text-dark-900' : 'text-gray-400 hover:text-white')}
        >
          {isRtl ? 'المؤشرات' : 'Indicators'}
        </button>
        <button
          onClick={() => setActiveTab('schools')}
          className={clsx('px-3 py-1 rounded text-xs font-medium transition-colors', activeTab === 'schools' ? 'bg-gold text-dark-900' : 'text-gray-400 hover:text-white')}
        >
          {isRtl ? 'إجماع المدارس' : 'Schools'} (74+)
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'indicators' ? (
          <div>
            {/* Multi-timeframe Table */}
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-2 font-medium">
                {isRtl ? '• الإشارات على الأطر الزمنية' : '• Multi-Timeframe Signals'}
              </div>
              <table className="table-dark w-full text-xs">
                <thead>
                  <tr>
                    <th className="text-right">{isRtl ? 'الإطار' : 'TF'}</th>
                    <th className="text-center">M15</th>
                    <th className="text-center">H1</th>
                    <th className="text-center">H4</th>
                    <th className="text-center">D1</th>
                    <th className="text-center">W1</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="text-gray-300">{isRtl ? 'الإشارة' : 'Signal'}</td>
                    {TIMEFRAMES_ORDER.map(tf => (
                      <td key={tf} className="text-center">
                        <SignalBadge signal={data.timeframes?.[tf]?.signal || 'neutral'} lang={language} />
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="text-gray-300">{isRtl ? 'الثقة' : 'Conf.'}</td>
                    {TIMEFRAMES_ORDER.map(tf => (
                      <td key={tf} className="text-center text-gold text-xs">
                        {data.timeframes?.[tf]?.confidence || 0}%
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Indicators */}
            <div>
              <div className="text-xs text-gray-400 mb-2 font-medium">
                {isRtl ? '• المؤشرات الفنية' : '• Technical Indicators'}
              </div>
              <table className="table-dark w-full text-xs">
                <thead>
                  <tr>
                    <th className="text-right">{isRtl ? 'المؤشر' : 'Indicator'}</th>
                    <th className="text-center">{isRtl ? 'القيمة' : 'Value'}</th>
                    <th className="text-center">{isRtl ? 'الإشارة' : 'Signal'}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.indicators?.map((ind, i) => (
                    <tr key={i}>
                      <td className="text-gray-200 font-medium">{ind.name}</td>
                      <td className="text-center text-gray-400">
                        {typeof ind.value === 'number' ? ind.value.toFixed(2) : ind.value}
                      </td>
                      <td className="text-center">
                        <SignalBadge signal={ind.signal} lang={language} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {data.schools?.map((school, i) => (
              <div key={i} className="flex items-center gap-2 py-1.5">
                <div className="w-32 shrink-0">
                  <div className="text-gray-200 text-xs font-medium leading-tight">
                    {isRtl ? school.name_ar : school.name}
                  </div>
                </div>
                <div className="flex-1">
                  <ConfidenceBar
                    value={school.confidence}
                    color={school.signal === 'buy' ? '#4ADE80' : school.signal === 'sell' ? '#F87171' : '#C9A227'}
                  />
                </div>
                <SignalBadge signal={school.signal} lang={language} />
              </div>
            ))}
            <div className="text-center text-gray-500 text-xs pt-2 border-t border-dark-600">
              {isRtl ? '+ 64 مدرسة أخرى في الخطة المتقدمة' : '+ 64 more schools in advanced plan'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
