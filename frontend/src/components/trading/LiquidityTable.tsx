'use client'

import { useEffect, useState } from 'react'
import { getLiquidityData } from '@/lib/api'
import { MOCK_LIQUIDITY } from '@/lib/mockData'
import { useAppStore } from '@/lib/store'
import type { LiquidityData } from '@/types'
import clsx from 'clsx'
import { format } from 'date-fns'

const StrengthBar = ({ value }: { value: number }) => (
  <div className="w-16 bg-dark-600 rounded-full h-1.5 overflow-hidden">
    <div
      className="h-full rounded-full"
      style={{
        width: `${value}%`,
        background: value >= 80 ? '#C9A227' : value >= 60 ? '#E8C547' : '#A0A0A0',
      }}
    />
  </div>
)

export default function LiquidityTable() {
  const { selectedSymbol, language } = useAppStore()
  const [data, setData] = useState<LiquidityData>(MOCK_LIQUIDITY)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'ob' | 'fvg' | 'whale'>('ob')
  const isRtl = language === 'ar'

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await getLiquidityData(selectedSymbol)
        if (res.data) setData(res.data)
      } catch {
        setData(MOCK_LIQUIDITY)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [selectedSymbol])

  const biasColor = data.smart_money_bias === 'bullish' ? '#4ADE80' :
    data.smart_money_bias === 'bearish' ? '#F87171' : '#A0A0A0'

  return (
    <div className="card-gold h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-lg">💧</span>
          <h3 className="text-gold font-bold text-sm">
            {isRtl ? 'السيولة وتدفق الأموال' : 'Liquidity & Order Flow'}
          </h3>
        </div>
        {loading && <div className="w-3 h-3 border border-gold border-t-transparent rounded-full animate-spin" />}
      </div>

      {/* Smart Money Bias + Killzone */}
      <div className="grid grid-cols-2 gap-2 mb-3 shrink-0">
        <div className="bg-dark-700 rounded-lg p-2 text-center">
          <div className="text-xs text-gray-400 mb-1">
            {isRtl ? 'الأموال الذكية' : 'Smart Money'}
          </div>
          <div className="text-sm font-bold" style={{ color: biasColor }}>
            {data.smart_money_bias === 'bullish' ? (isRtl ? '↑ صعودي' : '↑ Bullish') :
             data.smart_money_bias === 'bearish' ? (isRtl ? '↓ هبوطي' : '↓ Bearish') :
             (isRtl ? '→ محايد' : '→ Neutral')}
          </div>
        </div>
        <div className={clsx(
          'rounded-lg p-2 text-center',
          data.killzone?.active ? 'bg-green-500/10 border border-green-500/30' : 'bg-dark-700'
        )}>
          <div className="text-xs text-gray-400 mb-1">
            {isRtl ? 'منطقة التداول' : 'Killzone'}
          </div>
          <div className={clsx('text-xs font-semibold', data.killzone?.active ? 'text-green-400' : 'text-gray-500')}>
            {isRtl ? data.killzone?.name_ar : data.killzone?.name}
          </div>
          {data.killzone?.active && (
            <div className="text-xs text-green-400/70">
              {data.killzone.start} - {data.killzone.end}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-3 shrink-0">
        {[
          { key: 'ob', label: 'Order Blocks', labelAr: 'بلوكات الطلبات' },
          { key: 'fvg', label: 'FVG', labelAr: 'فجوات FVG' },
          { key: 'whale', label: 'Whales', labelAr: 'الحيتان' },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as any)}
            className={clsx('px-2 py-1 rounded text-xs font-medium transition-colors', tab === t.key ? 'bg-gold text-dark-900' : 'text-gray-400 hover:text-white')}
          >
            {isRtl ? t.labelAr : t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'ob' && (
          <table className="table-dark w-full text-xs">
            <thead>
              <tr>
                <th className="text-right">{isRtl ? 'المستوى' : 'Level'}</th>
                <th className="text-center">{isRtl ? 'الاتجاه' : 'Dir.'}</th>
                <th className="text-center">{isRtl ? 'الإطار' : 'TF'}</th>
                <th className="text-right">{isRtl ? 'القوة' : 'Strength'}</th>
              </tr>
            </thead>
            <tbody>
              {data.order_blocks.map((ob) => (
                <tr key={ob.id}>
                  <td className="text-white font-bold">{ob.level.toFixed(2)}</td>
                  <td className="text-center">
                    <span className={ob.direction === 'bullish' ? 'badge-buy' : 'badge-sell'}>
                      {ob.direction === 'bullish' ? (isRtl ? '↑ شراء' : '↑ Bull') : (isRtl ? '↓ بيع' : '↓ Bear')}
                    </span>
                  </td>
                  <td className="text-center text-gray-400">{ob.timeframe}</td>
                  <td><StrengthBar value={ob.strength} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === 'fvg' && (
          <table className="table-dark w-full text-xs">
            <thead>
              <tr>
                <th className="text-right">{isRtl ? 'القمة' : 'Top'}</th>
                <th className="text-right">{isRtl ? 'القاع' : 'Bottom'}</th>
                <th className="text-center">{isRtl ? 'الاتجاه' : 'Dir.'}</th>
                <th className="text-center">{isRtl ? 'الإطار' : 'TF'}</th>
                <th className="text-center">{isRtl ? 'مملوء' : 'Filled'}</th>
              </tr>
            </thead>
            <tbody>
              {data.fv_gaps.map((gap) => (
                <tr key={gap.id} className={gap.filled ? 'opacity-50' : ''}>
                  <td className="text-white">{gap.top.toFixed(2)}</td>
                  <td className="text-white">{gap.bottom.toFixed(2)}</td>
                  <td className="text-center">
                    <span className={gap.direction === 'bullish' ? 'badge-buy' : 'badge-sell'}>
                      {gap.direction === 'bullish' ? '↑' : '↓'}
                    </span>
                  </td>
                  <td className="text-center text-gray-400">{gap.timeframe}</td>
                  <td className="text-center">
                    {gap.filled ?
                      <span className="text-gray-500">✓</span> :
                      <span className="text-gold">○</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === 'whale' && (
          <div className="space-y-2">
            {data.whale_alerts.map((alert) => (
              <div key={alert.id} className={clsx(
                'flex items-center justify-between p-2 rounded-lg text-xs',
                alert.side === 'buy' ? 'bg-green-500/5 border border-green-500/20' : 'bg-red-500/5 border border-red-500/20'
              )}>
                <div className="flex items-center gap-2">
                  <span className="text-base">{alert.side === 'buy' ? '🐋' : '🦈'}</span>
                  <div>
                    <div className="font-bold" style={{ color: alert.side === 'buy' ? '#4ADE80' : '#F87171' }}>
                      {alert.side === 'buy' ? (isRtl ? '↑ شراء ضخم' : '↑ Big BUY') : (isRtl ? '↓ بيع ضخم' : '↓ Big SELL')}
                    </div>
                    <div className="text-gray-400">{alert.symbol} @ {alert.price.toFixed(2)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-gold font-bold">{alert.volume.toFixed(1)} lots</div>
                  <div className="text-gray-500">
                    {(() => {
                      try {
                        const mins = Math.floor((Date.now() - new Date(alert.timestamp).getTime()) / 60000)
                        return `${mins}${isRtl ? 'د' : 'm'}`
                      } catch { return '' }
                    })()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
