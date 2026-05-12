'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'

const ASSETS = [
  { value: 'XAU/USD', label: 'الذهب والدولار', labelEn: 'Gold / USD (XAU/USD)' },
  { value: 'XTI/USD', label: 'النفط والدولار', labelEn: 'Oil / USD (XTI/USD)' },
  { value: 'EUR/USD', label: 'يورو / دولار', labelEn: 'EUR/USD' },
  { value: 'GBP/USD', label: 'جنيه / دولار', labelEn: 'GBP/USD' },
  { value: 'USD/JPY', label: 'دولار / ين', labelEn: 'USD/JPY' },
  { value: 'USD/CHF', label: 'دولار / فرنك', labelEn: 'USD/CHF' },
  { value: 'USD/CAD', label: 'دولار / كندي', labelEn: 'USD/CAD' },
  { value: 'AUD/USD', label: 'أسترالي / دولار', labelEn: 'AUD/USD' },
  { value: 'NZD/USD', label: 'نيوزيلندي / دولار', labelEn: 'NZD/USD' },
]

const TIMEFRAMES = [
  { value: '1M', label: '1 دقيقة', ref: '5M + 15M' },
  { value: '5M', label: '5 دقائق', ref: '15M + 30M' },
  { value: '15M', label: '15 دقيقة', ref: '30M + 1H' },
  { value: '30M', label: '30 دقيقة', ref: '1H + 4H' },
  { value: '1H', label: '1 ساعة', ref: '4H فقط' },
  { value: '4H', label: '4 ساعات', ref: '1D فقط' },
]

export default function TraderOptionsTable() {
  const { language, selectedSymbol, setSymbol, selectedTimeframe, setTimeframe } = useAppStore()
  const isRtl = language === 'ar'

  const [capital, setCapital] = useState(10000)
  const [riskPct, setRiskPct] = useState(2)
  const [tradeType, setTradeType] = useState<'auto' | 'manual'>('auto')
  const [botRunning, setBotRunning] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const riskAmount = (capital * riskPct) / 100
  const currentTF = TIMEFRAMES.find(t => t.value === selectedTimeframe) || TIMEFRAMES[2]

  const rows = [
    {
      num: 1,
      label: 'الأصل المطلوب تداوله',
      labelEn: 'Asset to Trade',
      desc: 'قائمة منسدلة: الذهب والدولار (XAU/USD) — النفط والدولار (XTI/USD) — أزواج الفوركس الرئيسية السبعة',
      value: (
        <select
          value={selectedSymbol}
          onChange={e => setSymbol(e.target.value)}
          className="bg-dark-700 border border-gold/30 rounded-lg px-3 py-2 text-gold text-sm focus:outline-none focus:border-gold min-w-[200px]"
        >
          {ASSETS.map(a => (
            <option key={a.value} value={a.value}>
              {a.value} — {a.label}
            </option>
          ))}
        </select>
      ),
    },
    {
      num: 2,
      label: 'نسبة المخاطرة',
      labelEn: 'Risk %',
      desc: 'قائمة منسدلة: من ١٪ إلى ١٠٪ من رأس المال',
      value: (
        <select
          value={riskPct}
          onChange={e => setRiskPct(Number(e.target.value))}
          className="bg-dark-700 border border-gold/30 rounded-lg px-3 py-2 text-gold text-sm focus:outline-none focus:border-gold"
        >
          {[1,2,3,4,5,6,7,8,9,10].map(n => (
            <option key={n} value={n}>{n}٪</option>
          ))}
        </select>
      ),
    },
    {
      num: 3,
      label: 'مبلغ المخاطرة',
      labelEn: 'Risk Amount',
      desc: 'يُحسب تلقائيًا عند تحديد نسبة المخاطرة ورأس المال — لا يُدخل يدويًا',
      value: (
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={capital}
            onChange={e => setCapital(Number(e.target.value))}
            className="bg-dark-700 border border-gold/30 rounded-lg px-3 py-2 text-white text-sm w-28 focus:outline-none focus:border-gold"
            placeholder="رأس المال"
          />
          <span className="text-gray-400 text-sm">→</span>
          <span className="text-buy font-bold text-sm bg-dark-700 border border-buy/30 rounded-lg px-3 py-2">
            {riskAmount.toLocaleString('ar-SA', { maximumFractionDigits: 2 })} $
          </span>
          <span className="text-gray-500 text-xs">تلقائي</span>
        </div>
      ),
    },
    {
      num: 4,
      label: 'الإطار الزمني للمضاربة',
      labelEn: 'Trading Timeframe',
      desc: 'قائمة منسدلة: 1M، 5M، 15M، 30M، 1H، 4H — هذا الإطار الذي يفتح عليه البوت الصفقات',
      value: (
        <select
          value={selectedTimeframe}
          onChange={e => setTimeframe(e.target.value)}
          className="bg-dark-700 border border-gold/30 rounded-lg px-3 py-2 text-gold text-sm focus:outline-none focus:border-gold"
        >
          {TIMEFRAMES.map(tf => (
            <option key={tf.value} value={tf.value}>{tf.value} — {tf.label}</option>
          ))}
        </select>
      ),
    },
    {
      num: 5,
      label: 'الإطار الزمني الأكبر المرجعي',
      labelEn: 'Reference Timeframe',
      desc: 'يُحدد تلقائيًا حسب إطار التداول المختار لتحديد الاتجاه العام',
      value: (
        <span className="text-gold font-bold bg-dark-700 border border-gold/30 rounded-lg px-3 py-2 text-sm">
          {currentTF.ref}
        </span>
      ),
    },
    {
      num: 6,
      label: 'نوع التداول',
      labelEn: 'Trade Type',
      desc: 'البوت الآلي (التداول الخوارزمي الكامل بالذكاء الاصطناعي) — التداول اليدوي (المستخدم يضغط دخول الصفقة بنفسه)',
      value: (
        <select
          value={tradeType}
          onChange={e => setTradeType(e.target.value as 'auto' | 'manual')}
          className="bg-dark-700 border border-gold/30 rounded-lg px-3 py-2 text-gold text-sm focus:outline-none focus:border-gold"
        >
          <option value="auto">🤖 البوت الآلي بالذكاء الاصطناعي</option>
          <option value="manual">👤 التداول اليدوي</option>
        </select>
      ),
    },
  ]

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🦁</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ١ — خيارات المتداول / المستخدم للمنصة
            </div>
            <div className="text-gray-500 text-xs">
              كل ما يحدده المتداول قبل تشغيل البوت — هذا الجدول يتفاعل مع باقي الجداول لحظيًا
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 text-xs">يتحكم بالجداول كلها</span>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4">
          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm" dir={isRtl ? 'rtl' : 'ltr'}>
              <thead>
                <tr className="border-b border-gold/20">
                  <th className="text-gold text-right pb-2 pr-2 w-8 font-medium">#</th>
                  <th className="text-gold text-right pb-2 pr-3 font-medium">الخيار</th>
                  <th className="text-gray-400 text-right pb-2 pr-3 font-medium hidden md:table-cell">الشرح</th>
                  <th className="text-gold text-right pb-2 font-medium">القيمة المختارة</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(row => (
                  <tr key={row.num} className="border-b border-dark-600 hover:bg-dark-700/30 transition-colors">
                    <td className="py-3 pr-2 text-gray-500 font-bold">{row.num}</td>
                    <td className="py-3 pr-3">
                      <div className="text-white font-medium">{row.label}</div>
                      <div className="text-gray-500 text-xs hidden lg:block">{row.labelEn}</div>
                    </td>
                    <td className="py-3 pr-3 text-gray-400 text-xs hidden md:table-cell max-w-xs">
                      {row.desc}
                    </td>
                    <td className="py-3">{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Action Buttons */}
          <div className="mt-4 pt-4 border-t border-gold/20">
            <div className="flex flex-wrap items-center gap-3">
              {/* Bot Start/Stop */}
              <button
                onClick={() => setBotRunning(!botRunning)}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 ${
                  botRunning
                    ? 'bg-red-900/80 border border-red-500 text-white hover:bg-red-800'
                    : 'text-dark-900 hover:opacity-90'
                }`}
                style={!botRunning ? { background: 'linear-gradient(135deg, #C9A227, #E8C547)' } : {}}
              >
                <img src="/logo.jpg" alt="" className="w-5 h-5 rounded-full" />
                {botRunning ? '⏹️ إيقاف البوت' : '▶️ تشغيل بوت الأسد الآلي'}
              </button>

              {/* Manual Buy */}
              <button className="flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm bg-buy hover:bg-green-700 text-white transition-colors">
                🟢 شراء يدوي
              </button>

              {/* Manual Sell */}
              <button className="flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm bg-sell hover:bg-red-800 text-white transition-colors">
                🔴 بيع يدوي
              </button>

              {botRunning && (
                <div className="flex items-center gap-2 text-xs text-green-400">
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  البوت يعمل — {selectedSymbol} — {selectedTimeframe}
                </div>
              )}
            </div>
            <p className="text-gray-500 text-xs mt-2">
              ملاحظة الأزرار: زر البوت الذهبي بشعار الأسد ▶️ Play (يتحول إلى ⏹️ Stop باللون الأحمر عند التشغيل) • الزر الأخضر للشراء اليدوي • الزر الأحمر للبيع اليدوي
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
