'use client'
import { useEffect, useRef, useState } from 'react'

interface ChartPanelProps {
  symbol: string
  timeframe: string
  signal: any
}

export function ChartPanel({ symbol, timeframe, signal }: ChartPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<any>(null)
  const candleSeriesRef = useRef<any>(null)
  const [chartReady, setChartReady] = useState(false)
  const [showIndicators, setShowIndicators] = useState({
    ema7: true, ema25: true, sma200: true, orderBlocks: true,
    fibonacci: true, signals: true, vwap: true,
  })

  useEffect(() => {
    let chart: any = null
    let resizeObs: ResizeObserver | null = null

    const initChart = async () => {
      if (!containerRef.current) return
      const LWC = await import('lightweight-charts')

      chart = LWC.createChart(containerRef.current, {
        layout: {
          background: { color: '#0A0A0A' },
          textColor: '#9ca3af',
          fontFamily: 'JetBrains Mono, monospace',
        },
        grid: {
          vertLines: { color: 'rgba(255,255,255,0.03)' },
          horzLines: { color: 'rgba(255,255,255,0.03)' },
        },
        crosshair: {
          mode: LWC.CrosshairMode.Normal,
          vertLine: { color: '#C9A227', labelBackgroundColor: '#C9A227' },
          horzLine: { color: '#C9A227', labelBackgroundColor: '#C9A227' },
        },
        rightPriceScale: {
          borderColor: '#1f1f1f',
          textColor: '#9ca3af',
          scaleMargins: { top: 0.1, bottom: 0.2 },
        },
        timeScale: {
          borderColor: '#1f1f1f',
          textColor: '#9ca3af',
          timeVisible: true,
          secondsVisible: false,
        },
        handleScroll: true,
        handleScale: true,
      })

      const candleSeries = chart.addCandlestickSeries({
        upColor: '#0E7A2C',
        downColor: '#B0140C',
        borderUpColor: '#0E7A2C',
        borderDownColor: '#B0140C',
        wickUpColor: '#0E7A2C',
        wickDownColor: '#B0140C',
      })

      // Generate synthetic candles
      const candles = generateCandles(symbol, 200)
      candleSeries.setData(candles)
      candleSeriesRef.current = candleSeries

      // Add EMA 7
      if (showIndicators.ema7) {
        const ema7 = chart.addLineSeries({ color: '#C9A227', lineWidth: 1, priceLineVisible: false })
        ema7.setData(calcEMA(candles, 7))
      }

      // Add EMA 25
      if (showIndicators.ema25) {
        const ema25 = chart.addLineSeries({ color: '#f0c040', lineWidth: 1.5, priceLineVisible: false })
        ema25.setData(calcEMA(candles, 25))
      }

      // Add SMA 200
      if (showIndicators.sma200) {
        const sma200 = chart.addLineSeries({ color: '#6b7280', lineWidth: 1, priceLineVisible: false })
        sma200.setData(calcSMA(candles, 200))
      }

      // Add VWAP
      if (showIndicators.vwap) {
        const vwapSeries = chart.addLineSeries({ color: '#818cf8', lineWidth: 1.5, lineStyle: 2, priceLineVisible: false })
        vwapSeries.setData(calcVWAP(candles))
      }

      // Add signal markers
      if (signal && showIndicators.signals) {
        const markers = [{
          time: candles[candles.length - 1].time,
          position: signal.side === 'BUY' ? 'belowBar' : 'aboveBar',
          color: signal.side === 'BUY' ? '#0E7A2C' : '#B0140C',
          shape: signal.side === 'BUY' ? 'arrowUp' : 'arrowDown',
          text: `🦁 ${signal.side} ${signal.confluenceScore?.toFixed(0)}%`,
          size: 2,
        }]
        candleSeries.setMarkers(markers)
      }

      chartRef.current = chart
      setChartReady(true)

      // Responsive resize
      resizeObs = new ResizeObserver(() => {
        if (containerRef.current && chart) {
          chart.applyOptions({
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight,
          })
        }
      })
      resizeObs.observe(containerRef.current)
    }

    initChart()

    return () => {
      resizeObs?.disconnect()
      chart?.remove()
    }
  }, [symbol, timeframe])

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      {/* Chart toolbar */}
      <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-200 border-b border-dark-50 text-xs">
        <span className="text-gold-500 font-bold">{symbol}</span>
        <span className="text-gray-600">{timeframe}</span>
        <div className="w-px h-4 bg-dark-50 mx-1" />
        {Object.entries(showIndicators).map(([key, val]) => (
          <button
            key={key}
            onClick={() => setShowIndicators(p => ({ ...p, [key]: !p[key as keyof typeof p] }))}
            className={`px-2 py-0.5 rounded text-xs ${val ? 'text-gold-500' : 'text-gray-700'}`}
          >
            {key.toUpperCase()}
          </button>
        ))}
        <div className="flex-1" />
        {/* Signal overlay info */}
        {signal && (
          <div className="flex items-center gap-3">
            <span className="text-gray-500">دخول: <span className="text-gold-500 font-mono">{signal.entry?.toFixed(2)}</span></span>
            <span className="text-gray-500">SL: <span className="price-down font-mono">{signal.sl?.toFixed(2)}</span></span>
            <span className="text-gray-500">TP3: <span className="price-up font-mono">{signal.tp3?.toFixed(2)}</span></span>
          </div>
        )}
      </div>

      {/* Chart container */}
      <div ref={containerRef} className="flex-1" />

      {/* Confluence Score overlay */}
      {signal && (
        <div className="absolute top-12 right-3 bg-dark-100/90 border border-dark-50 rounded-xl p-3 text-xs backdrop-blur-sm">
          <div className="text-gold-500 font-bold text-sm mb-2 text-center">Confluence Score</div>
          <div className="confluence-bar w-32 mb-1">
            <div
              className={`confluence-fill ${signal.side.toLowerCase()}`}
              style={{ width: `${signal.confluenceScore}%` }}
            />
          </div>
          <div className={`text-center font-mono font-bold ${
            signal.confluenceScore >= 75 ? 'price-up' : signal.confluenceScore >= 60 ? 'text-gold-500' : 'price-down'
          }`}>
            {signal.confluenceScore?.toFixed(1)}%
          </div>
          <div className={`text-center mt-1 font-bold ${
            signal.side === 'BUY' ? 'price-up' : signal.side === 'SELL' ? 'price-down' : 'text-gray-500'
          }`}>
            {signal.side === 'BUY' ? '🟢 شراء' : signal.side === 'SELL' ? '🔴 بيع' : '⚪ محايد'}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Helper functions ──────────────────────────────────────────────────────────

function generateCandles(symbol: string, count: number) {
  const basePrices: Record<string, number> = {
    XAUUSD: 2350, USOIL: 78.5, EURUSD: 1.0852, GBPUSD: 1.2654,
    USDJPY: 149.45, BTCUSD: 67000,
  }
  const base = basePrices[symbol] || 1.0
  const now = Math.floor(Date.now() / 1000)
  const intervalSec = 3600
  const candles = []
  let price = base

  for (let i = count; i >= 0; i--) {
    const change = (Math.random() - 0.485) * base * 0.003
    price += change
    const open = price
    const close = price + (Math.random() - 0.5) * base * 0.001
    const high = Math.max(open, close) + Math.random() * base * 0.001
    const low = Math.min(open, close) - Math.random() * base * 0.001
    candles.push({
      time: now - i * intervalSec,
      open: parseFloat(open.toFixed(5)),
      high: parseFloat(high.toFixed(5)),
      low: parseFloat(low.toFixed(5)),
      close: parseFloat(close.toFixed(5)),
    })
    price = close
  }
  return candles
}

function calcEMA(candles: any[], period: number) {
  const result = []
  const k = 2 / (period + 1)
  let ema = candles[0]?.close || 0
  for (let i = 0; i < candles.length; i++) {
    if (i < period) { ema = candles[i].close; continue }
    ema = candles[i].close * k + ema * (1 - k)
    result.push({ time: candles[i].time, value: parseFloat(ema.toFixed(5)) })
  }
  return result
}

function calcSMA(candles: any[], period: number) {
  const result = []
  for (let i = period - 1; i < candles.length; i++) {
    const avg = candles.slice(i - period + 1, i + 1).reduce((s, c) => s + c.close, 0) / period
    result.push({ time: candles[i].time, value: parseFloat(avg.toFixed(5)) })
  }
  return result
}

function calcVWAP(candles: any[]) {
  let cumTPV = 0, cumV = 0
  return candles.map(c => {
    const tp = (c.high + c.low + c.close) / 3
    const vol = Math.random() * 1000 + 100
    cumTPV += tp * vol
    cumV += vol
    return { time: c.time, value: parseFloat((cumTPV / cumV).toFixed(5)) }
  })
}
