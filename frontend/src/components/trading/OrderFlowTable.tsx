'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'

const INSTITUTIONS = [
  { id: 'central_banks', name: 'البنوك المركزية', nameEn: 'Central Banks', icon: '🏦', tier: 'S', examples: 'Fed, ECB, BoE, BoJ, SNB, PBoC, SAMA' },
  { id: 'investment_banks', name: 'البنوك الاستثمارية', nameEn: 'Investment Banks', icon: '🏢', tier: 'S', examples: 'Goldman Sachs, JPMorgan, Morgan Stanley, Citi, BoA, Deutsche, HSBC, BNP' },
  { id: 'hedge_funds', name: 'صناديق التحوط', nameEn: 'Hedge Funds', icon: '📈', tier: 'A', examples: 'Bridgewater, Renaissance, Two Sigma, Citadel, Man Group, AQR, Millennium' },
  { id: 'asset_managers', name: 'مدراء الأصول', nameEn: 'Asset Managers', icon: '💼', tier: 'A', examples: 'BlackRock, Vanguard, Fidelity, State Street, PIMCO, T.Rowe Price, Franklin' },
  { id: 'sovereign_wealth', name: 'صناديق الثروة السيادية', nameEn: 'Sovereign Wealth Funds', icon: '👑', tier: 'S', examples: 'PIF (السعودية), ADIA (أبوظبي), GIC (سنغافورة), Norges Bank, CIC (الصين), KWIA (الكويت)' },
  { id: 'gold_companies', name: 'شركات الذهب والتعدين', nameEn: 'Gold & Mining Companies', icon: '🥇', tier: 'A', examples: 'Barrick Gold, Newmont, AngloGold, Gold Fields, Kinross, Agnico Eagle, Wheaton' },
  { id: 'oil_companies', name: 'شركات النفط والطاقة', nameEn: 'Oil & Energy Companies', icon: '🛢️', tier: 'A', examples: 'Aramco, ExxonMobil, Shell, BP, TotalEnergies, Chevron, ConocoPhillips, Eni' },
  { id: 'forex_makers', name: 'صانعو سوق الفوركس', nameEn: 'Forex Market Makers', icon: '🔄', tier: 'A', examples: 'Citi FX, Deutsche FX, Barclays FX, UBS FX, HSBC FX, BNP FX, JPMorgan FX' },
  { id: 'insurance', name: 'شركات التأمين الكبرى', nameEn: 'Major Insurance Companies', icon: '🛡️', tier: 'B', examples: 'AIG, Allianz, AXA, Munich Re, Swiss Re, Berkshire Hathaway, Zurich, Prudential' },
  { id: 'pension_funds', name: 'صناديق التقاعد', nameEn: 'Pension Funds', icon: '📋', tier: 'B', examples: 'CalPERS, CPPIB, APG, OTPP, GEPF, ATP, ABP, USS' },
  { id: 'etfs', name: 'صناديق ETF المؤثرة', nameEn: 'Major ETFs', icon: '📊', tier: 'B', examples: 'GLD, IAU, SLV, USO, UNG, SPY, QQQ, GDX, GDXJ, DBO' },
  { id: 'hft', name: 'خوارزميات HFT عالية التردد', nameEn: 'HFT Algorithms', icon: '⚡', tier: 'B', examples: 'Virtu Financial, Citadel Securities, Jump Trading, DRW, XTX Markets, Tower Research' },
  { id: 'prop_trading', name: 'شركات التداول الخاص', nameEn: 'Prop Trading Firms', icon: '🎯', tier: 'C', examples: 'Jane Street, IMC, Flow Traders, Optiver, SIG, Wolverine Trading, Getco' },
]

const SIGNALS_TF = ['1M', '5M', '15M', '30M', '1H', '4H']

function randomSignal(): 'buy' | 'sell' | 'neutral' {
  const r = Math.random()
  if (r < 0.4) return 'buy'
  if (r < 0.7) return 'sell'
  return 'neutral'
}

function SignalBadge({ signal }: { signal: 'buy' | 'sell' | 'neutral' }) {
  if (signal === 'buy') return <span className="text-xs px-1.5 py-0.5 rounded bg-buy/20 text-buy font-bold">▲</span>
  if (signal === 'sell') return <span className="text-xs px-1.5 py-0.5 rounded bg-sell/20 text-sell font-bold">▼</span>
  return <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400 font-bold">—</span>
}

function TierBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    S: 'bg-yellow-400/20 text-yellow-300 border-yellow-400/40',
    A: 'bg-gold/20 text-gold border-gold/40',
    B: 'bg-blue-400/20 text-blue-300 border-blue-400/40',
    C: 'bg-gray-400/20 text-gray-400 border-gray-500/40',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-bold ${colors[tier] || colors.C}`}>
      {tier}
    </span>
  )
}

interface InstitutionRow {
  id: string
  buyVolume: number
  sellVolume: number
  netFlow: number
  signals: ('buy' | 'sell' | 'neutral')[]
  signal: 'buy' | 'sell' | 'neutral'
  dominance: number
  activity: 'نشط جداً' | 'نشط' | 'محايد' | 'هادئ'
  chartOn: boolean
}

export default function OrderFlowTable() {
  const { language, selectedSymbol, selectedTimeframe } = useAppStore()
  const isRtl = language === 'ar'
  const [collapsed, setCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<'dom' | 'institutions' | 'signals'>('dom')
  const [rows, setRows] = useState<InstitutionRow[]>([])

  const [domData, setDomData] = useState({
    bid: 1983.45,
    ask: 1983.67,
    spread: 0.22,
    cumulativeDeltaBuy: 2847,
    cumulativeDeltaSell: 1923,
    cumulativeDeltaNet: 924,
    bidVolume: 1245,
    askVolume: 987,
    imbalance: 26.1,
    lastTick: '▲ 0.12',
    footprintBull: 68,
    footprintBear: 32,
    bookmapLiq: 'كثيفة عند 1985.00 و 1979.00',
    arcBreakout: 'فوق 1985.20 → استمرار صعود',
    pumpSignal: false,
    dumpSignal: false,
  })

  useEffect(() => {
    const generated: InstitutionRow[] = INSTITUTIONS.map(inst => {
      const buyVol = Math.floor(Math.random() * 5000) + 500
      const sellVol = Math.floor(Math.random() * 5000) + 500
      const net = buyVol - sellVol
      const signals = SIGNALS_TF.map(() => randomSignal()) as ('buy' | 'sell' | 'neutral')[]
      const buys = signals.filter(s => s === 'buy').length
      const sells = signals.filter(s => s === 'sell').length
      return {
        id: inst.id,
        buyVolume: buyVol,
        sellVolume: sellVol,
        netFlow: net,
        signals,
        signal: buys > sells ? 'buy' : sells > buys ? 'sell' : 'neutral',
        dominance: Math.floor(Math.random() * 40) + 5,
        activity: (['نشط جداً', 'نشط', 'محايد', 'هادئ'] as const)[Math.floor(Math.random() * 4)],
        chartOn: false,
      }
    })
    setRows(generated)
  }, [selectedSymbol, selectedTimeframe])

  const totalBuy = rows.reduce((a, r) => a + r.buyVolume, 0)
  const totalSell = rows.reduce((a, r) => a + r.sellVolume, 0)
  const netTotal = totalBuy - totalSell

  const buyCubCount = Math.floor(Math.random() * 300) + 50
  const sellCubCount = Math.floor(Math.random() * 300) + 50
  const buyLionCount = rows.filter(r => r.signal === 'buy').length
  const sellLionCount = rows.filter(r => r.signal === 'sell').length
  const lionSignal = buyLionCount > sellLionCount ? 'buy' : sellLionCount > buyLionCount ? 'sell' : 'neutral'

  const weightedScore = netTotal > 0 ? Math.min(((netTotal / (totalBuy + totalSell)) * 100 * 1.5), 15) : Math.max(((-netTotal / (totalBuy + totalSell)) * 100 * 1.5) * -1, -15)
  const contributionTo15 = Math.abs(weightedScore).toFixed(1)

  function toggleChart(id: string) {
    setRows(prev => prev.map(r => r.id === id ? { ...r, chartOn: !r.chartOn } : r))
  }

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">📊</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٦ — تدفق الأوامر والبوك ماب (Order Flow & BookMap)
            </div>
            <div className="text-gray-500 text-xs">
              الوزن: ١٥٪ من قرار الدخول • مراقبة السيولة المؤسسية والحقيقية
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-buy font-bold">شراء أسد: {buyLionCount}</span>
            <span className="text-gray-500">/</span>
            <span className="text-sell font-bold">بيع أسد: {sellLionCount}</span>
          </div>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4">
          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b border-gold/20 pb-2">
            {[
              { key: 'dom', label: '📋 DOM وتدفق الأوامر' },
              { key: 'institutions', label: '🏛️ المؤسسات الكبرى' },
              { key: 'signals', label: '🎯 إشارات الأسد والشبل' },
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

          {/* Tab: DOM */}
          {activeTab === 'dom' && (
            <div className="space-y-4">
              {/* Live DOM */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-dark-700/50 rounded-lg p-3 border border-buy/20">
                  <div className="text-gray-500 text-xs mb-1">Bid (طلب شراء)</div>
                  <div className="text-buy font-bold text-lg">{domData.bid.toFixed(2)}</div>
                  <div className="text-gray-500 text-xs">حجم: {domData.bidVolume} عقد</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3 border border-sell/20">
                  <div className="text-gray-500 text-xs mb-1">Ask (عرض بيع)</div>
                  <div className="text-sell font-bold text-lg">{domData.ask.toFixed(2)}</div>
                  <div className="text-gray-500 text-xs">حجم: {domData.askVolume} عقد</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3 border border-gold/20">
                  <div className="text-gray-500 text-xs mb-1">السبريد (Spread)</div>
                  <div className="text-gold font-bold text-lg">{domData.spread.toFixed(2)}</div>
                  <div className="text-gray-500 text-xs">نقطة / pips</div>
                </div>
                <div className="bg-dark-700/50 rounded-lg p-3 border border-purple-500/20">
                  <div className="text-gray-500 text-xs mb-1">آخر حركة</div>
                  <div className="text-purple-300 font-bold text-lg">{domData.lastTick}</div>
                  <div className="text-gray-500 text-xs">تيك حي</div>
                </div>
              </div>

              {/* Cumulative Delta */}
              <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                <div className="text-gold font-bold text-sm mb-3">Delta التراكمي (Cumulative Delta)</div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-buy font-bold text-xl">{domData.cumulativeDeltaBuy.toLocaleString()}</div>
                    <div className="text-gray-500 text-xs">Delta شراء</div>
                  </div>
                  <div className="text-center">
                    <div className={`font-bold text-xl ${domData.cumulativeDeltaNet > 0 ? 'text-buy' : 'text-sell'}`}>
                      {domData.cumulativeDeltaNet > 0 ? '+' : ''}{domData.cumulativeDeltaNet.toLocaleString()}
                    </div>
                    <div className="text-gray-500 text-xs">صافي Delta</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sell font-bold text-xl">{domData.cumulativeDeltaSell.toLocaleString()}</div>
                    <div className="text-gray-500 text-xs">Delta بيع</div>
                  </div>
                </div>
                <div className="mt-3 h-3 bg-dark-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-buy to-green-400 rounded-full"
                    style={{ width: `${(domData.cumulativeDeltaBuy / (domData.cumulativeDeltaBuy + domData.cumulativeDeltaSell)) * 100}%` }}
                  />
                </div>
              </div>

              {/* Footprint & Imbalance */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                  <div className="text-gold font-bold text-sm mb-3">Footprint Chart — طبعة القدم</div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-buy">ثيران ({domData.footprintBull}٪)</span>
                        <span className="text-sell">دببة ({domData.footprintBear}٪)</span>
                      </div>
                      <div className="h-4 bg-sell/30 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-buy rounded-full"
                          style={{ width: `${domData.footprintBull}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-gray-400">
                    اختلال في الأحجام (Imbalance): <span className="text-gold font-bold">{domData.imbalance}٪</span>
                  </div>
                </div>
                <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/10">
                  <div className="text-gold font-bold text-sm mb-3">BookMap — خريطة السيولة</div>
                  <div className="space-y-2 text-xs">
                    <div className="flex gap-2">
                      <span className="text-gray-500">مناطق السيولة الكثيفة:</span>
                      <span className="text-white font-medium">{domData.bookmapLiq}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-gray-500">منطقة ARC كسر:</span>
                      <span className="text-buy font-medium">{domData.arcBreakout}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-gray-500">إشارة Pump:</span>
                      <span className={domData.pumpSignal ? 'text-buy font-bold' : 'text-gray-500'}>
                        {domData.pumpSignal ? '🚀 PUMP نشط' : '— لا توجد'}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-gray-500">إشارة Dump:</span>
                      <span className={domData.dumpSignal ? 'text-sell font-bold' : 'text-gray-500'}>
                        {domData.dumpSignal ? '💥 DUMP نشط' : '— لا توجد'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab: Institutions */}
          {activeTab === 'institutions' && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
                <thead>
                  <tr className="border-b border-gold/20">
                    <th className="text-gold text-right pb-2 pr-2 font-medium">#</th>
                    <th className="text-gold text-right pb-2 pr-3 font-medium">المؤسسة</th>
                    <th className="text-gold text-right pb-2 pr-2 font-medium">Tier</th>
                    <th className="text-gold text-right pb-2 pr-2 font-medium">أمثلة</th>
                    {SIGNALS_TF.map(tf => (
                      <th key={tf} className="text-gold text-center pb-2 px-1 font-medium w-10">{tf}</th>
                    ))}
                    <th className="text-gold text-center pb-2 px-2 font-medium">الإشارة</th>
                    <th className="text-gold text-right pb-2 px-2 font-medium">حجم شراء</th>
                    <th className="text-gold text-right pb-2 px-2 font-medium">حجم بيع</th>
                    <th className="text-gold text-right pb-2 px-2 font-medium">صافي</th>
                    <th className="text-gold text-center pb-2 px-2 font-medium">النشاط</th>
                    <th className="text-gold text-center pb-2 px-2 font-medium">Chart</th>
                  </tr>
                </thead>
                <tbody>
                  {INSTITUTIONS.map((inst, idx) => {
                    const row = rows[idx]
                    if (!row) return null
                    return (
                      <tr key={inst.id} className="border-b border-dark-600 hover:bg-dark-700/30 transition-colors">
                        <td className="py-2.5 pr-2 text-gray-500 font-bold">{idx + 1}</td>
                        <td className="py-2.5 pr-3">
                          <div className="flex items-center gap-2">
                            <span>{inst.icon}</span>
                            <div>
                              <div className="text-white font-medium">{inst.name}</div>
                              <div className="text-gray-500 text-xs">{inst.nameEn}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-2.5 pr-2"><TierBadge tier={inst.tier} /></td>
                        <td className="py-2.5 pr-2 text-gray-500 max-w-[120px] truncate" title={inst.examples}>
                          {inst.examples.split(',')[0]}...
                        </td>
                        {row.signals.map((sig, si) => (
                          <td key={si} className="py-2.5 px-1 text-center">
                            <SignalBadge signal={sig} />
                          </td>
                        ))}
                        <td className="py-2.5 px-2 text-center">
                          {row.signal === 'buy' ? (
                            <span className="text-buy font-bold text-xs">🟢 شراء</span>
                          ) : row.signal === 'sell' ? (
                            <span className="text-sell font-bold text-xs">🔴 بيع</span>
                          ) : (
                            <span className="text-gray-400 text-xs">— محايد</span>
                          )}
                        </td>
                        <td className="py-2.5 px-2 text-buy font-medium">{row.buyVolume.toLocaleString()}</td>
                        <td className="py-2.5 px-2 text-sell font-medium">{row.sellVolume.toLocaleString()}</td>
                        <td className={`py-2.5 px-2 font-bold ${row.netFlow > 0 ? 'text-buy' : 'text-sell'}`}>
                          {row.netFlow > 0 ? '+' : ''}{row.netFlow.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-2 text-center">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            row.activity === 'نشط جداً' ? 'bg-buy/20 text-buy' :
                            row.activity === 'نشط' ? 'bg-green-700/20 text-green-400' :
                            row.activity === 'محايد' ? 'bg-yellow-700/20 text-yellow-400' :
                            'bg-gray-700/20 text-gray-500'
                          }`}>
                            {row.activity}
                          </span>
                        </td>
                        <td className="py-2.5 px-2 text-center">
                          <button
                            onClick={() => toggleChart(inst.id)}
                            className={`text-xs px-2 py-1 rounded transition-colors ${
                              row.chartOn ? 'bg-gold text-dark-900 font-bold' : 'bg-dark-700 text-gray-400 hover:text-gold'
                            }`}
                          >
                            {row.chartOn ? 'ON' : 'OFF'}
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
                <tfoot>
                  <tr className="border-t border-gold/30 bg-dark-700/30">
                    <td colSpan={4} className="py-3 pr-2 text-gold font-bold text-xs">المجموع الكلي</td>
                    {SIGNALS_TF.map(tf => <td key={tf} />)}
                    <td className="py-3 px-2 text-center">
                      {netTotal > 0
                        ? <span className="text-buy font-bold text-xs">🟢 شراء مؤسسي</span>
                        : <span className="text-sell font-bold text-xs">🔴 بيع مؤسسي</span>
                      }
                    </td>
                    <td className="py-3 px-2 text-buy font-bold">{totalBuy.toLocaleString()}</td>
                    <td className="py-3 px-2 text-sell font-bold">{totalSell.toLocaleString()}</td>
                    <td className={`py-3 px-2 font-bold ${netTotal > 0 ? 'text-buy' : 'text-sell'}`}>
                      {netTotal > 0 ? '+' : ''}{netTotal.toLocaleString()}
                    </td>
                    <td colSpan={2} />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          {/* Tab: Lion & Cub Signals */}
          {activeTab === 'signals' && (
            <div className="space-y-4">
              {/* Cub Signals */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-dark-700/30 rounded-lg p-4 border border-green-500/20">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">🐻</span>
                    <div>
                      <div className="text-buy font-bold text-sm">إشارة شراء الشبل (Buy Cub)</div>
                      <div className="text-gray-500 text-xs">متداولون صغار &lt; 5,000$ • تأكيد جزئي</div>
                    </div>
                  </div>
                  <div className="text-buy text-3xl font-bold">{buyCubCount}</div>
                  <div className="text-gray-500 text-xs mt-1">صفقة شراء نشطة من الأفراد الصغار</div>
                  <div className="mt-2 text-xs text-gray-400">
                    هذه الإشارة تُستخدم كمؤشر سطحي فقط — لا تتخذ قرارات بها منفردة
                  </div>
                </div>
                <div className="bg-dark-700/30 rounded-lg p-4 border border-sell/20">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">🐻</span>
                    <div>
                      <div className="text-sell font-bold text-sm">إشارة بيع الشبل (Sell Cub)</div>
                      <div className="text-gray-500 text-xs">متداولون صغار &lt; 5,000$ • تأكيد جزئي</div>
                    </div>
                  </div>
                  <div className="text-sell text-3xl font-bold">{sellCubCount}</div>
                  <div className="text-gray-500 text-xs mt-1">صفقة بيع نشطة من الأفراد الصغار</div>
                  <div className="mt-2 text-xs text-gray-400">
                    ملاحظة: كثرة إشارات الأفراد الصغار في اتجاه قد تعني عكسه من قبل المؤسسات
                  </div>
                </div>
              </div>

              {/* Lion Signals */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-dark-700/30 rounded-lg p-4 border border-gold/30">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">🦁</span>
                    <div>
                      <div className="text-gold font-bold text-sm">إشارة شراء الأسد (Buy Lion)</div>
                      <div className="text-gray-500 text-xs">مؤسسات كبرى مؤكدة • وزن عالي جداً</div>
                    </div>
                  </div>
                  <div className="text-buy text-3xl font-bold">{buyLionCount}</div>
                  <div className="text-gray-500 text-xs mt-1">مؤسسة من أصل {INSTITUTIONS.length} تشتري بقوة</div>
                  <div className="mt-3">
                    <div className="flex flex-wrap gap-1">
                      {INSTITUTIONS.slice(0, buyLionCount).map(inst => (
                        <span key={inst.id} className="text-xs bg-buy/20 text-buy px-1.5 py-0.5 rounded">
                          {inst.icon} {inst.name.split(' ')[0]}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="bg-dark-700/30 rounded-lg p-4 border border-sell/30">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">🦁</span>
                    <div>
                      <div className="text-sell font-bold text-sm">إشارة بيع الأسد (Sell Lion)</div>
                      <div className="text-gray-500 text-xs">مؤسسات كبرى مؤكدة • وزن عالي جداً</div>
                    </div>
                  </div>
                  <div className="text-sell text-3xl font-bold">{sellLionCount}</div>
                  <div className="text-gray-500 text-xs mt-1">مؤسسة من أصل {INSTITUTIONS.length} تبيع بقوة</div>
                  <div className="mt-3">
                    <div className="flex flex-wrap gap-1">
                      {INSTITUTIONS.slice(0, sellLionCount).map(inst => (
                        <span key={inst.id} className="text-xs bg-sell/20 text-sell px-1.5 py-0.5 rounded">
                          {inst.icon} {inst.name.split(' ')[0]}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* PUMP / DUMP / BOMP / ARC */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'PUMP 🚀', desc: 'ضخ صعودي مؤسسي', active: domData.pumpSignal, color: 'buy' },
                  { label: 'BOMP 💥', desc: 'كسر صعودي بحجم', active: netTotal > 2000, color: 'buy' },
                  { label: 'DUMP 🔻', desc: 'بيع حاد مؤسسي', active: domData.dumpSignal, color: 'sell' },
                  { label: 'ARC 🎯', desc: 'كسر قوس مقاومة', active: true, color: 'gold' },
                ].map(sig => (
                  <div
                    key={sig.label}
                    className={`rounded-lg p-3 border text-center ${
                      sig.active
                        ? sig.color === 'buy' ? 'bg-buy/20 border-buy/40' :
                          sig.color === 'sell' ? 'bg-sell/20 border-sell/40' :
                          'bg-gold/20 border-gold/40'
                        : 'bg-dark-700/30 border-dark-600'
                    }`}
                  >
                    <div className={`font-bold text-sm ${
                      sig.active
                        ? sig.color === 'buy' ? 'text-buy' :
                          sig.color === 'sell' ? 'text-sell' :
                          'text-gold'
                        : 'text-gray-600'
                    }`}>
                      {sig.label}
                    </div>
                    <div className="text-gray-500 text-xs mt-1">{sig.desc}</div>
                    <div className={`text-xs font-bold mt-1 ${sig.active ? 'text-white' : 'text-gray-600'}`}>
                      {sig.active ? '● نشط' : '○ غير نشط'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary Row */}
          <div className="mt-4 pt-4 border-t border-gold/20">
            <div className="bg-dark-700/30 rounded-lg p-3 border border-gold/10">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-4">
                  <div className="text-gold font-bold text-sm">ملخص تدفق الأوامر — {selectedSymbol}</div>
                  <div className={`flex items-center gap-1 text-sm font-bold ${
                    lionSignal === 'buy' ? 'text-buy' : lionSignal === 'sell' ? 'text-sell' : 'text-gray-400'
                  }`}>
                    {lionSignal === 'buy' ? '🟢 تدفق شراء مؤسسي' : lionSignal === 'sell' ? '🔴 تدفق بيع مؤسسي' : '⚪ محايد'}
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="text-gray-500">
                    إسهام في القرار:
                    <span className="text-gold font-bold mr-1">{contributionTo15}٪</span>
                    من أصل ١٥٪
                  </div>
                  <div className={`px-3 py-1 rounded-lg font-bold text-xs ${
                    lionSignal === 'buy' ? 'bg-buy/20 text-buy border border-buy/30' :
                    lionSignal === 'sell' ? 'bg-sell/20 text-sell border border-sell/30' :
                    'bg-gray-700/30 text-gray-400 border border-gray-600'
                  }`}>
                    {lionSignal === 'buy' ? '▲ شراء أسد مؤسسي' : lionSignal === 'sell' ? '▼ بيع أسد مؤسسي' : '— محايد'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
