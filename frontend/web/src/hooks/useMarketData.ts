'use client'
import { useState, useEffect, useCallback, useRef } from 'react'

interface Signal {
  side: 'BUY' | 'SELL' | 'NEUTRAL'
  confluenceScore: number
  entry: number
  sl: number
  tp1: number
  tp2: number
  tp3: number
  lotSize: number
  riskPct: number
  rr1: number
  rr2: number
  rr3: number
  fundamentalScore: number
  technicalScore: number
  schoolBreakdown: Array<{ school: string; vote: string; strength: number; weight: number }>
  topFactors: string[]
  shouldTrade: boolean
  rejectionReasons: string[]
  generatedAt: string
}

interface TechnicalResult {
  school: string
  vote: 'BUY' | 'SELL' | 'NEUTRAL'
  strength: number
  details: Record<string, any>
  timeframes: { M15?: string; M30?: string; H1?: string; H4?: string; D1?: string }
}

export function useMarketData(symbol: string, timeframe: string) {
  const [signal, setSignal] = useState<Signal | null>(null)
  const [prices, setPrices] = useState<Record<string, any>>({})
  const [fundamentalReport, setFundamentalReport] = useState<any>(null)
  const [technicalResults, setTechnicalResults] = useState<TechnicalResult[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // Demo data generator for frontend testing
  const generateDemoSignal = useCallback((): Signal => {
    const sides = ['BUY', 'SELL', 'NEUTRAL'] as const
    const side = sides[Math.floor(Math.random() * 2)]
    const base = symbol === 'XAUUSD' ? 2350 : symbol === 'USOIL' ? 78 : 1.085
    const entry = base + (Math.random() - 0.5) * base * 0.002
    const atr = base * 0.008
    const sl = side === 'BUY' ? entry - atr * 1.5 : entry + atr * 1.5
    const risk = Math.abs(entry - sl)
    const tp1 = side === 'BUY' ? entry + risk : entry - risk
    const tp2 = side === 'BUY' ? entry + risk * 2 : entry - risk * 2
    const tp3 = side === 'BUY' ? entry + risk * 3 : entry - risk * 3
    const score = 72 + Math.random() * 20

    const schools = [
      'Smart Money Concepts', 'Fibonacci', 'Price Action', 'RSI Pro', 'MACD',
      'Ichimoku Cloud', 'Bollinger Bands', 'Moving Averages', 'Wyckoff Method',
      'Volume Spread Analysis', 'Elliott Wave', 'Harmonic Patterns',
    ]

    return {
      side,
      confluenceScore: parseFloat(score.toFixed(1)),
      entry: parseFloat(entry.toFixed(5)),
      sl: parseFloat(sl.toFixed(5)),
      tp1: parseFloat(tp1.toFixed(5)),
      tp2: parseFloat(tp2.toFixed(5)),
      tp3: parseFloat(tp3.toFixed(5)),
      lotSize: 0.1,
      riskPct: 2.0,
      rr1: 1.0,
      rr2: 2.0,
      rr3: 3.0,
      fundamentalScore: 60 + Math.random() * 30,
      technicalScore: 65 + Math.random() * 25,
      schoolBreakdown: schools.map(s => ({
        school: s,
        vote: Math.random() > 0.4 ? side : 'NEUTRAL',
        strength: parseFloat((0.5 + Math.random() * 0.5).toFixed(2)),
        weight: parseFloat((0.01 + Math.random() * 0.08).toFixed(3)),
      })),
      topFactors: ['Smart Money Order Block', 'Fibonacci 61.8% Zone', 'RSI Divergence', 'Killzone Active'],
      shouldTrade: score >= 75,
      rejectionReasons: score < 75 ? ['MTF_NOT_ALIGNED'] : [],
      generatedAt: new Date().toISOString(),
    }
  }, [symbol])

  const generateDemoPrices = useCallback(() => {
    const basePrices: Record<string, number> = {
      XAUUSD: 2350, USOIL: 78.5, EURUSD: 1.0852, GBPUSD: 1.2654,
      USDJPY: 149.45, BTCUSD: 67000, DXY: 104.2, XBRUSD: 82.3,
    }
    const updated: Record<string, any> = {}
    Object.entries(basePrices).forEach(([sym, base]) => {
      const change = (Math.random() - 0.5) * 0.002
      const price = base * (1 + change)
      updated[sym] = {
        symbol: sym,
        price: parseFloat(price.toFixed(sym === 'USDJPY' ? 3 : sym === 'XAUUSD' ? 2 : 5)),
        change_pct: parseFloat((change * 100).toFixed(3)),
        bid: parseFloat((price * 0.9999).toFixed(5)),
        ask: parseFloat((price * 1.0001).toFixed(5)),
        timestamp: new Date().toISOString(),
      }
    })
    return updated
  }, [])

  const generateDemoTechnical = useCallback((): TechnicalResult[] => {
    const schools = [
      { school: 'Moving Averages', weight: 0.03 },
      { school: 'RSI Pro', weight: 0.02 },
      { school: 'MACD', weight: 0.012 },
      { school: 'Stochastic', weight: 0.012 },
      { school: 'Bollinger Bands', weight: 0.012 },
      { school: 'Ichimoku Cloud', weight: 0.014 },
      { school: 'Smart Money Concepts', weight: 0.07 },
      { school: 'Fibonacci', weight: 0.05 },
      { school: 'Price Action', weight: 0.05 },
      { school: 'VWAP', weight: 0.015 },
      { school: 'ATR', weight: 0.01 },
      { school: 'ADX+DMI', weight: 0.012 },
      { school: 'CCI', weight: 0.01 },
      { school: 'Wyckoff Method', weight: 0.013 },
      { school: 'Volume Spread Analysis', weight: 0.015 },
      { school: 'Elliott Wave', weight: 0.012 },
      { school: 'Harmonic Patterns', weight: 0.01 },
      { school: 'Parabolic SAR', weight: 0.01 },
      { school: 'Williams %R', weight: 0.01 },
      { school: 'OBV', weight: 0.01 },
    ]
    const votes = ['BUY', 'BUY', 'BUY', 'SELL', 'NEUTRAL'] as const
    return schools.map(({ school, weight }) => ({
      school,
      vote: votes[Math.floor(Math.random() * votes.length)],
      strength: parseFloat((0.5 + Math.random() * 0.5).toFixed(2)),
      details: { value: (Math.random() * 100).toFixed(2) },
      timeframes: {
        M15: votes[Math.floor(Math.random() * votes.length)],
        M30: votes[Math.floor(Math.random() * votes.length)],
        H1: votes[Math.floor(Math.random() * votes.length)],
        H4: votes[Math.floor(Math.random() * votes.length)],
        D1: votes[Math.floor(Math.random() * votes.length)],
      },
    }))
  }, [])

  // Try WebSocket, fallback to polling demo data
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    let ws: WebSocket | null = null

    const connectWS = () => {
      try {
        ws = new WebSocket(`ws://localhost:8000/ws/${symbol}/${timeframe}`)
        ws.onopen = () => setIsConnected(true)
        ws.onmessage = (e) => {
          const data = JSON.parse(e.data)
          if (data.signal) setSignal(data.signal)
          if (data.prices) setPrices(data.prices)
          if (data.technical) setTechnicalResults(data.technical)
          if (data.fundamental) setFundamentalReport(data.fundamental)
        }
        ws.onclose = () => { setIsConnected(false); startDemoMode() }
        ws.onerror = () => { ws?.close(); startDemoMode() }
        wsRef.current = ws
      } catch {
        startDemoMode()
      }
    }

    const startDemoMode = () => {
      setIsConnected(false)
      pollRef.current = setInterval(() => {
        setPrices(generateDemoPrices())
        setSignal(generateDemoSignal())
        setTechnicalResults(generateDemoTechnical())
        setFundamentalReport({
          asset: symbol,
          overall_score: 60 + Math.random() * 30,
          direction: Math.random() > 0.5 ? 'BULL' : 'BEAR',
          market_regime: 'RISK_ON',
          news_shield_active: false,
          events_today: [
            { title: 'NFP Non-Farm Payrolls', impact: 'HIGH', actual: 256, forecast: 220, previous: 303, sentiment_score: 45, bias: 'BULL' },
            { title: 'CPI m/m', impact: 'HIGH', actual: 0.3, forecast: 0.3, previous: 0.4, sentiment_score: 0, bias: 'NEUTRAL' },
            { title: 'FOMC Meeting Minutes', impact: 'MEDIUM', actual: null, forecast: null, previous: null, sentiment_score: -10, bias: 'BEAR' },
          ],
          top_drivers: ['NFP Beat', 'CPI Inline', 'Fed Hawkish'],
          generated_at: new Date().toISOString(),
        })
      }, 3000)
    }

    // Initial load
    setPrices(generateDemoPrices())
    setSignal(generateDemoSignal())
    setTechnicalResults(generateDemoTechnical())

    connectWS()

    return () => {
      ws?.close()
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [symbol, timeframe, generateDemoSignal, generateDemoPrices, generateDemoTechnical])

  return { signal, prices, fundamentalReport, technicalResults, isConnected }
}
