'use client'

import { useEffect, useState } from 'react'
import { getCalendar, getNews } from '@/lib/api'
import { MOCK_FUNDAMENTAL } from '@/lib/mockData'
import { useAppStore } from '@/lib/store'
import type { EconomicEvent, NewsItem } from '@/types'
import clsx from 'clsx'
import { format } from 'date-fns'

const ImpactIcon = ({ impact }: { impact: string }) => {
  if (impact === 'high') return <span className="text-red-400">🔴</span>
  if (impact === 'medium') return <span className="text-yellow-400">🟡</span>
  return <span className="text-green-400">🟢</span>
}

const GoldImpact = ({ impact }: { impact?: string }) => {
  if (impact === 'bullish') return <span className="badge-buy">صعود</span>
  if (impact === 'bearish') return <span className="badge-sell">هبوط</span>
  return <span className="badge-neutral">محايد</span>
}

const SentimentBadge = ({ sentiment }: { sentiment: string }) => {
  if (sentiment === 'bullish') return <span className="badge-buy">↑ صعودي</span>
  if (sentiment === 'bearish') return <span className="badge-sell">↓ هبوطي</span>
  return <span className="badge-neutral">→ محايد</span>
}

export default function FundamentalTable() {
  const { language } = useAppStore()
  const [events, setEvents] = useState<EconomicEvent[]>(MOCK_FUNDAMENTAL.events)
  const [news, setNews] = useState<NewsItem[]>(MOCK_FUNDAMENTAL.news)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'calendar' | 'news'>('calendar')
  const isRtl = language === 'ar'

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [calRes, newsRes] = await Promise.all([getCalendar(), getNews()])
        if (calRes.data?.events) setEvents(calRes.data.events)
        if (newsRes.data?.news) setNews(newsRes.data.news)
      } catch {
        // Use mock data
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const formatTime = (datetime: string) => {
    try {
      return format(new Date(datetime), 'HH:mm')
    } catch {
      return '--:--'
    }
  }

  return (
    <div className="card-gold h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-lg">📰</span>
          <h3 className="text-gold font-bold text-sm">
            {isRtl ? 'التحليل الأساسي' : 'Fundamental Analysis'}
          </h3>
        </div>
        {loading && (
          <div className="w-4 h-4 border border-gold border-t-transparent rounded-full animate-spin" />
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-3 shrink-0">
        <button
          onClick={() => setTab('calendar')}
          className={clsx('px-3 py-1 rounded text-xs font-medium transition-colors', tab === 'calendar' ? 'bg-gold text-dark-900' : 'text-gray-400 hover:text-white')}
        >
          {isRtl ? '📅 الأحداث' : '📅 Events'}
        </button>
        <button
          onClick={() => setTab('news')}
          className={clsx('px-3 py-1 rounded text-xs font-medium transition-colors', tab === 'news' ? 'bg-gold text-dark-900' : 'text-gray-400 hover:text-white')}
        >
          {isRtl ? '📄 الأخبار' : '📄 News'}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'calendar' ? (
          <table className="table-dark w-full">
            <thead>
              <tr>
                <th className="text-right w-8">{isRtl ? 'تأثير' : 'Impact'}</th>
                <th className="text-right">{isRtl ? 'الحدث' : 'Event'}</th>
                <th className="text-center">{isRtl ? 'الوقت' : 'Time'}</th>
                <th className="text-center">{isRtl ? 'متوقع' : 'Fore.'}</th>
                <th className="text-center">{isRtl ? 'سابق' : 'Prev.'}</th>
                <th className="text-center">{isRtl ? 'الذهب' : 'Gold'}</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td className="text-center"><ImpactIcon impact={event.impact} /></td>
                  <td>
                    <div className="text-white text-xs leading-tight">
                      {isRtl ? (event.title_ar || event.title) : event.title}
                    </div>
                    <div className="text-gray-500 text-xs">{event.currency}</div>
                  </td>
                  <td className="text-center text-gray-300 text-xs">{formatTime(event.datetime)}</td>
                  <td className="text-center text-gray-300 text-xs">{event.forecast || '–'}</td>
                  <td className="text-center text-gray-400 text-xs">{event.previous || '–'}</td>
                  <td className="text-center"><GoldImpact impact={event.gold_impact} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="space-y-2">
            {news.map((item) => (
              <div key={item.id} className="p-3 rounded-lg bg-dark-700 hover:bg-dark-600 transition-colors cursor-pointer">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="text-white text-xs font-medium leading-tight flex-1">
                    {isRtl ? (item.title_ar || item.title) : item.title}
                  </h4>
                  <SentimentBadge sentiment={item.sentiment} />
                </div>
                <div className="flex items-center gap-2 text-gray-500 text-xs">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>
                    {(() => {
                      try {
                        const mins = Math.floor((Date.now() - new Date(item.published_at).getTime()) / 60000)
                        if (mins < 60) return `${mins}د`
                        return `${Math.floor(mins / 60)}س`
                      } catch { return '' }
                    })()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
