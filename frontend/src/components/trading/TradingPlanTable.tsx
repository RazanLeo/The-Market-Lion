'use client'
import { useEffect, useState } from 'react'
import { getTechnicalAnalysis, getAccount } from '@/lib/api'
import { useAppStore } from '@/lib/store'

interface TradePlan {
  signal: string
  entry: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  confluence_score: number
  atr: number
}

export default function TradingPlanTable({ symbol = 'XAU/USD' }: { symbol?: string }) {
  const [plan, setPlan] = useState<TradePlan | null>(null)
  const [balance, setBalance] = useState(10000)
  const [riskPct, setRiskPct] = useState(1)
  const language = useAppStore((s) => s.language)
  const ar = language === 'ar'

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getTechnicalAnalysis(symbol, 'H1')
        const d = res.data
        setPlan({
          signal: d.signal,
          entry: d.entry || d.price,
          stop_loss: d.stop_loss || d.price * 0.99,
          take_profit_1: d.take_profit_1 || d.price * 1.006,
          take_profit_2: d.take_profit_2 || d.price * 1.013,
          take_profit_3: d.take_profit_3 || d.price * 1.021,
          confluence_score: d.confluence_score,
          atr: d.indicators?.atr?.value || 15,
        })
      } catch {
        setPlan({
          signal: 'buy',
          entry: 2345.50,
          stop_loss: 2330.00,
          take_profit_1: 2360.00,
          take_profit_2: 2375.00,
          take_profit_3: 2395.00,
          confluence_score: 0.72,
          atr: 15.2,
        })
      }
    }
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [symbol])

  if (!plan) return (
    <div className="bg-dark-800 border border-gold/10 rounded-xl p-4 animate-pulse">
      {[...Array(6)].map((_, i) => <div key={i} className="h-4 bg-dark-700 rounded mb-2" />)}
    </div>
  )

  const isBuy = plan.signal === 'buy'
  const slPips = Math.abs(plan.entry - plan.stop_loss)
  const tp1Pips = Math.abs(plan.take_profit_1 - plan.entry)
  const riskDollar = balance * (riskPct / 100)
  const lotSize = slPips > 0 ? (riskDollar / (slPips * 100)) : 0.01
  const rr1 = slPips > 0 ? (tp1Pips / slPips).toFixed(2) : '—'
  const rr2 = slPips > 0 ? (Math.abs(plan.take_profit_2 - plan.entry) / slPips).toFixed(2) : '—'
  const rr3 = slPips > 0 ? (Math.abs(plan.take_profit_3 - plan.entry) / slPips).toFixed(2) : '—'

  const signalColor = isBuy ? 'text-green-400 border-green-500/30 bg-green-500/5' : plan.signal === 'sell' ? 'text-red-400 border-red-500/30 bg-red-500/5' : 'text-yellow-400 border-yellow-500/30 bg-yellow-500/5'
  const signalLabel = isBuy ? (ar ? '🟢 شراء — BUY' : '🟢 BUY') : plan.signal === 'sell' ? (ar ? '🔴 بيع — SELL' : '🔴 SELL') : (ar ? '🟡 انتظار' : '🟡 WAIT')

  const Row = ({ label, value, color = '' }: { label: string; value: string; color?: string }) => (
    <div className="flex items-center justify-between py-1.5 border-b border-dark-700 last:border-0">
      <span className="text-gray-400 text-xs">{label}</span>
      <span className={`font-bold text-sm ${color || 'text-white'}`}>{value}</span>
    </div>
  )

  return (
    <div className="bg-dark-800 border border-gold/10 rounded-xl overflow-hidden" dir={ar ? 'rtl' : 'ltr'}>
      <div className="px-4 py-3 border-b border-gold/10 bg-gradient-to-r from-gold/5 to-transparent">
        <h3 className="text-gold font-bold text-sm">📋 {ar ? 'الجدول 4: خطة التداول وإدارة المخاطر' : 'Table 4: Trade Plan & Risk'}</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Signal Box */}
        <div className={`border rounded-xl p-4 ${signalColor}`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-lg font-black">{signalLabel}</span>
            <div className="text-right">
              <p className="text-xs text-gray-400">{symbol}</p>
              <p className="text-xs text-gray-500">H1 | Confluence: {Math.round(plan.confluence_score * 100)}%</p>
            </div>
          </div>
          <div className="space-y-1">
            <Row label={ar ? 'نقطة الدخول' : 'Entry'} value={plan.entry.toFixed(2)} color="text-gold" />
            <Row label={ar ? 'وقف الخسارة' : 'Stop Loss'} value={`${plan.stop_loss.toFixed(2)} (${isBuy ? '-' : '+'}${slPips.toFixed(1)})`} color="text-red-400" />
            <Row label={ar ? 'هدف 1 (RR 1:' + rr1 + ')' : `TP1 (RR 1:${rr1})`} value={plan.take_profit_1.toFixed(2)} color="text-green-400" />
            <Row label={ar ? 'هدف 2 (RR 1:' + rr2 + ')' : `TP2 (RR 1:${rr2})`} value={plan.take_profit_2.toFixed(2)} color="text-green-400" />
            <Row label={ar ? 'هدف 3 (RR 1:' + rr3 + ')' : `TP3 (RR 1:${rr3})`} value={plan.take_profit_3.toFixed(2)} color="text-green-500" />
          </div>
        </div>

        {/* Risk Calculator */}
        <div className="bg-dark-900 rounded-xl p-3">
          <p className="text-xs text-gray-400 font-bold mb-3">{ar ? 'حاسبة المخاطرة' : 'Risk Calculator'}</p>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400 w-24">{ar ? 'الرصيد ($)' : 'Balance ($)'}</label>
              <input
                type="number"
                value={balance}
                onChange={(e) => setBalance(Number(e.target.value))}
                className="flex-1 bg-dark-800 border border-gold/20 rounded-lg px-3 py-1.5 text-sm text-white focus:border-gold outline-none"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-400 w-24">{ar ? 'نسبة المخاطرة' : 'Risk %'}</label>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.5"
                value={riskPct}
                onChange={(e) => setRiskPct(Number(e.target.value))}
                className="flex-1 accent-gold"
              />
              <span className="text-gold text-xs font-bold w-8">{riskPct}%</span>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="bg-dark-800 rounded-lg p-2 text-center">
              <p className="text-gold font-black text-sm">{lotSize.toFixed(3)}</p>
              <p className="text-gray-500 text-xs">{ar ? 'لوت مقترح' : 'Lot Size'}</p>
            </div>
            <div className="bg-dark-800 rounded-lg p-2 text-center">
              <p className="text-red-400 font-black text-sm">${riskDollar.toFixed(0)}</p>
              <p className="text-gray-500 text-xs">{ar ? 'مخاطرة بالدولار' : 'Dollar Risk'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
