'use client'
import { useState, useEffect } from 'react'

interface LiquidityTableProps { symbol: string }

export function LiquidityTable({ symbol }: LiquidityTableProps) {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    // Generate demo liquidity data
    const generate = () => setData({
      orderBlocks: [
        { type: 'bullish', high: 2358.5, low: 2353.2, fresh: true, volume: 2840000 },
        { type: 'bearish', high: 2375.0, low: 2370.8, fresh: true, volume: 1920000 },
        { type: 'bullish', high: 2340.0, low: 2335.5, fresh: false, volume: 980000 },
      ],
      fvgs: [
        { type: 'bullish', top: 2362.0, bottom: 2358.5 },
        { type: 'bearish', top: 2380.5, bottom: 2376.0 },
      ],
      killzone: 'LONDON_OPEN',
      killzone_active: true,
      bsl: 2378.5,
      ssl: 2332.0,
      cumDelta: 1240000,
      deltaBias: 'BUY',
      vwap: 2351.2,
    })
    generate()
    const interval = setInterval(generate, 5000)
    return () => clearInterval(interval)
  }, [symbol])

  if (!data) return <div className="p-3 text-gray-600 text-xs text-center">جاري تحليل السيولة...</div>

  return (
    <div className="text-xs">
      {/* Killzone */}
      <div className={`flex items-center justify-between p-2 border-b border-dark-50 ${data.killzone_active ? 'bg-gold-500/10' : 'bg-dark-300'}`}>
        <span className="text-gray-500">Killzone النشط:</span>
        <span className={`font-bold ${data.killzone_active ? 'text-gold-500' : 'text-gray-600'}`}>
          {data.killzone_active ? '⚡ ' : ''}{data.killzone?.replace('_', ' ') || 'بدون'}
        </span>
      </div>

      {/* BSL/SSL */}
      <div className="grid grid-cols-2 gap-1 p-2 border-b border-dark-50">
        <div className="bg-dark-300 rounded p-1.5 text-center">
          <div className="text-gray-600">BSL (وقف البائعين)</div>
          <div className="font-mono font-bold price-up">{data.bsl?.toFixed(2)}</div>
        </div>
        <div className="bg-dark-300 rounded p-1.5 text-center">
          <div className="text-gray-600">SSL (وقف المشترين)</div>
          <div className="font-mono font-bold price-down">{data.ssl?.toFixed(2)}</div>
        </div>
      </div>

      {/* Cumulative Delta */}
      <div className="flex items-center justify-between p-2 border-b border-dark-50">
        <span className="text-gray-500">Cumulative Delta:</span>
        <span className={`font-mono font-bold ${data.deltaBias === 'BUY' ? 'price-up' : 'price-down'}`}>
          {data.deltaBias === 'BUY' ? '+' : ''}{(data.cumDelta / 1000000).toFixed(2)}M
        </span>
      </div>

      {/* Order Blocks */}
      <div className="p-2 border-b border-dark-50">
        <div className="text-gray-600 mb-1 font-bold">Order Blocks النشطة:</div>
        {data.orderBlocks.map((ob: any, i: number) => (
          <div key={i} className="flex items-center justify-between mb-1">
            <span className={`w-2 h-2 rounded-full ${ob.type === 'bullish' ? 'bg-bull' : 'bg-bear'}`} />
            <span className="text-gray-500">{ob.type === 'bullish' ? 'دعم' : 'مقاومة'}</span>
            <span className="font-mono">{ob.low?.toFixed(2)}–{ob.high?.toFixed(2)}</span>
            <span className={`${ob.fresh ? 'text-gold-500' : 'text-gray-600'}`}>{ob.fresh ? 'طازج' : 'مُختبَر'}</span>
            <span className="text-gray-600">${(ob.volume / 1000000).toFixed(1)}M</span>
          </div>
        ))}
      </div>

      {/* FVGs */}
      <div className="p-2">
        <div className="text-gray-600 mb-1 font-bold">Fair Value Gaps:</div>
        {data.fvgs.map((fvg: any, i: number) => (
          <div key={i} className="flex items-center justify-between mb-1">
            <span className={fvg.type === 'bullish' ? 'price-up' : 'price-down'}>
              {fvg.type === 'bullish' ? '▲' : '▼'} FVG
            </span>
            <span className="font-mono text-gray-400">{fvg.bottom?.toFixed(2)}–{fvg.top?.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
