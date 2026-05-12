'use client'

import { useEffect, useState } from 'react'
import { useAppStore } from '@/lib/store'

const SIGNAL_COLORS: Record<string, string> = {
  buy: '#0E7A2C', sell: '#B0140C', neutral: '#6B7280',
  bullish: '#0E7A2C', bearish: '#B0140C',
}

const SignalBadge = ({ s }: { s: string }) => {
  const labels: Record<string, string> = {
    buy: 'شراء', sell: 'بيع', neutral: 'محايد',
    bullish: 'صعود', bearish: 'هبوط', positive: 'إيجابي', negative: 'سلبي',
  }
  const bg = SIGNAL_COLORS[s] || '#6B7280'
  return (
    <span className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
      style={{ background: bg }}>
      {labels[s] || s}
    </span>
  )
}

const TFCell = ({ tf }: { tf: string }) => (
  <SignalBadge s={tf || 'neutral'} />
)

const ECONOMIC_INDICATORS = [
  { id: 1, asset: 'USD', indicator: 'قرار الفائدة الفيدرالية (FOMC Rate Decision)', utc: '18:00 UTC', local: '21:00 KSA', importance: 'عالي جداً' },
  { id: 2, asset: 'USD', indicator: 'Dot Plot — توقعات أعضاء الفيدرالي', utc: 'حسب الجدولة', local: 'حسب الجدولة', importance: 'عالي جداً' },
  { id: 3, asset: 'USD', indicator: 'FOMC Minutes — محاضر اجتماعات الفيدرالي', utc: 'شهري', local: 'شهري', importance: 'عالي' },
  { id: 4, asset: 'EUR', indicator: 'ECB — قرار الفائدة الأوروبي', utc: '12:15 UTC', local: '15:15 KSA', importance: 'عالي جداً' },
  { id: 5, asset: 'GBP', indicator: 'BOE — بنك إنجلترا (قرار الفائدة)', utc: '11:00 UTC', local: '14:00 KSA', importance: 'عالي' },
  { id: 6, asset: 'JPY', indicator: 'BOJ — بنك اليابان (قرار الفائدة + YCC)', utc: '03:00 UTC', local: '06:00 KSA', importance: 'عالي' },
  { id: 7, asset: 'CHF', indicator: 'SNB — البنك السويسري', utc: '07:30 UTC', local: '10:30 KSA', importance: 'متوسط' },
  { id: 8, asset: 'AUD', indicator: 'RBA — البنك المركزي الأسترالي', utc: '03:30 UTC', local: '06:30 KSA', importance: 'متوسط' },
  { id: 9, asset: 'CAD', indicator: 'BOC — بنك كندا (مهم للنفط)', utc: '14:00 UTC', local: '17:00 KSA', importance: 'متوسط' },
  { id: 10, asset: 'USD', indicator: 'DXY — مؤشر الدولار الأمريكي', utc: 'لحظي', local: 'لحظي', importance: 'عالي جداً' },
  { id: 11, asset: 'USD', indicator: 'CPI — مؤشر أسعار المستهلكين (Headline)', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي جداً' },
  { id: 12, asset: 'USD', indicator: 'Core CPI — مؤشر أسعار المستهلكين الأساسي', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي جداً' },
  { id: 13, asset: 'USD', indicator: 'PPI — مؤشر أسعار المنتجين', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي' },
  { id: 14, asset: 'USD', indicator: 'PCE — نفقات الاستهلاك الشخصي (المفضل للفيد)', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي جداً' },
  { id: 15, asset: 'USD', indicator: 'Core PCE — PCE الأساسي بدون الغذاء والطاقة', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي جداً' },
  { id: 16, asset: 'USD', indicator: 'GDP — الناتج المحلي الإجمالي (Advance/Final)', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي جداً' },
  { id: 17, asset: 'USD', indicator: 'GDPNow — توقع الفيدرالي أتلانتا اللحظي', utc: 'لحظي', local: 'لحظي', importance: 'عالي' },
  { id: 18, asset: 'USD', indicator: 'Industrial Production — الإنتاج الصناعي', utc: '13:15 UTC', local: '16:15 KSA', importance: 'متوسط' },
  { id: 19, asset: 'USD', indicator: 'NFP — الوظائف غير الزراعية (أهم تقرير شهري)', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي جداً' },
  { id: 20, asset: 'USD', indicator: 'Unemployment Rate — معدل البطالة', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي' },
  { id: 21, asset: 'USD', indicator: 'Initial Jobless Claims — طلبات إعانة البطالة الأسبوعية', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي' },
  { id: 22, asset: 'USD', indicator: 'JOLTS — فرص العمل + معدل الاستقالات', utc: '14:00 UTC', local: '17:00 KSA', importance: 'متوسط' },
  { id: 23, asset: 'USD', indicator: 'ADP Employment — تقرير التوظيف الخاص', utc: '12:15 UTC', local: '15:15 KSA', importance: 'متوسط' },
  { id: 24, asset: 'USD', indicator: 'Average Hourly Earnings — متوسط الأجور الساعية', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي' },
  { id: 25, asset: 'USD', indicator: 'Retail Sales — مبيعات التجزئة (Headline + Core)', utc: '12:30 UTC', local: '15:30 KSA', importance: 'عالي' },
  { id: 26, asset: 'USD', indicator: 'Consumer Confidence — ثقة المستهلك (CB)', utc: '14:00 UTC', local: '17:00 KSA', importance: 'متوسط' },
  { id: 27, asset: 'USD', indicator: 'UoM Consumer Sentiment — ثقة المستهلك ميشيغان', utc: '14:00 UTC', local: '17:00 KSA', importance: 'متوسط' },
  { id: 28, asset: 'USD', indicator: 'ISM Manufacturing PMI — مديري المشتريات الصناعي', utc: '14:00 UTC', local: '17:00 KSA', importance: 'عالي' },
  { id: 29, asset: 'USD', indicator: 'ISM Services PMI — مديري المشتريات الخدمي', utc: '14:00 UTC', local: '17:00 KSA', importance: 'عالي' },
  { id: 30, asset: 'USD', indicator: 'S&P Global PMI — المؤشر العالمي', utc: '13:45 UTC', local: '16:45 KSA', importance: 'متوسط' },
  { id: 31, asset: 'CNY', indicator: 'Caixin PMI الصيني (مهم للسلع والنفط)', utc: '01:45 UTC', local: '04:45 KSA', importance: 'متوسط' },
  { id: 32, asset: 'USD', indicator: 'Durable Goods Orders — طلبيات السلع المعمرة', utc: '12:30 UTC', local: '15:30 KSA', importance: 'متوسط' },
  { id: 33, asset: 'USD', indicator: 'Housing Starts & Building Permits', utc: '12:30 UTC', local: '15:30 KSA', importance: 'منخفض' },
  { id: 34, asset: 'USD', indicator: 'Case-Shiller Home Price Index', utc: '13:00 UTC', local: '16:00 KSA', importance: 'منخفض' },
  { id: 35, asset: 'USD', indicator: 'US Treasury Yields — عوائد السندات (2Y, 10Y, 30Y)', utc: 'لحظي', local: 'لحظي', importance: 'عالي جداً' },
  { id: 36, asset: 'XAU', indicator: 'Real Yields TIPS 10Y — العائد الحقيقي (الأهم للذهب)', utc: 'لحظي', local: 'لحظي', importance: 'عالي جداً' },
  { id: 37, asset: 'XTI', indicator: 'EIA Crude Oil Inventories — مخزونات النفط الأسبوعية', utc: '14:30 UTC', local: '17:30 KSA', importance: 'عالي جداً' },
  { id: 38, asset: 'XTI', indicator: 'API Crude Oil Inventories — تقرير API', utc: '20:30 UTC', local: '23:30 KSA', importance: 'عالي' },
  { id: 39, asset: 'XTI', indicator: 'Baker Hughes Rig Count — عدد منصات الحفر', utc: 'الجمعة 17:00', local: 'الجمعة 20:00', importance: 'متوسط' },
  { id: 40, asset: 'XAU', indicator: 'COMEX Gold Positioning — مراكز المضاربين', utc: 'الجمعة 19:30', local: 'الجمعة 22:30', importance: 'عالي' },
]

const NEWS_REPORTS = [
  { id: 1, asset: 'XAU', news: 'تقرير مجلس الذهب العالمي (WGC) ربعي', date: 'ربعي', source: 'World Gold Council', importance: 'عالي' },
  { id: 2, asset: 'USD', news: 'تقرير صندوق النقد الدولي (IMF)', date: 'دوري', source: 'IMF', importance: 'عالي' },
  { id: 3, asset: 'USD', news: 'تقرير الخزانة الأمريكية الفصلي', date: 'ربعي', source: 'US Treasury', importance: 'عالي' },
  { id: 4, asset: 'XTI', news: 'تقرير OPEC الشهري (MOMR)', date: 'شهري', source: 'OPEC', importance: 'عالي جداً' },
  { id: 5, asset: 'XTI', news: 'تقرير وكالة الطاقة الدولية (IEA) الشهري', date: 'شهري', source: 'IEA', importance: 'عالي' },
  { id: 6, asset: 'XTI', news: 'EIA Short-Term Energy Outlook (STEO)', date: 'شهري', source: 'EIA', importance: 'عالي' },
  { id: 7, asset: 'USD', news: 'الأخبار الجيوسياسية المؤثرة (حروب/عقوبات)', date: 'لحظي', source: 'Reuters/Bloomberg', importance: 'متغير' },
  { id: 8, asset: 'USD', news: 'COT Report — تقرير صفقات المضاربين', date: 'أسبوعي', source: 'CFTC', importance: 'عالي' },
  { id: 9, asset: 'USD', news: 'تقارير CPI/PPI الأوروبية والآسيوية', date: 'شهري', source: 'البنوك المركزية', importance: 'عالي' },
  { id: 10, asset: 'XAU', news: 'تقارير LBMA Gold Price (London Fix)', date: 'يومي', source: 'LBMA', importance: 'متوسط' },
  { id: 11, asset: 'XAU', news: 'Gold ETF Flows (GLD, IAU, SPDR)', date: 'يومي', source: 'WGC/ETF Providers', importance: 'متوسط' },
  { id: 12, asset: 'USD', news: 'Mining Stocks Performance (GDX, GDXJ)', date: 'لحظي', source: 'NYSE', importance: 'منخفض' },
]

const SPEECHES_TWEETS = [
  { id: 1, asset: 'USD', speech: 'خطاب رئيس الفيدرالي + Press Conference', speaker: 'Jerome Powell', platform: 'Federal Reserve', importance: 'عالي جداً' },
  { id: 2, asset: 'EUR', speech: 'خطاب رئيس البنك المركزي الأوروبي + Press Conference', speaker: 'Christine Lagarde', platform: 'ECB', importance: 'عالي جداً' },
  { id: 3, asset: 'GBP', speech: 'خطاب محافظ بنك إنجلترا', speaker: 'BoE Governor', platform: 'Bank of England', importance: 'عالي' },
  { id: 4, asset: 'JPY', speech: 'خطاب محافظ بنك اليابان', speaker: 'BoJ Governor', platform: 'Bank of Japan', importance: 'عالي' },
  { id: 5, asset: 'USD', speech: 'خطابات الرئيس الأمريكي + تغريداته', speaker: 'Donald Trump', platform: 'Twitter/X (@realDonaldTrump)', importance: 'عالي جداً' },
  { id: 6, asset: 'XAU', speech: 'تصريحات ولي العهد السعودي', speaker: 'محمد بن سلمان', platform: 'الحساب الرسمي للقيادة السعودية', importance: 'عالي جداً' },
  { id: 7, asset: 'USD', speech: 'تغريدات وزير الخزانة الأمريكي', speaker: 'US Treasury Secretary', platform: 'Twitter/X', importance: 'عالي' },
  { id: 8, asset: 'XTI', speech: 'تصريحات وزراء طاقة OPEC+ (السعودية، الإمارات، روسيا، إيران)', speaker: 'OPEC+ Energy Ministers', platform: 'بيانات رسمية + Twitter', importance: 'عالي جداً' },
  { id: 9, asset: 'USD', speech: 'تغريدات Macro Analysts المؤثرين', speaker: 'El-Erian, Roubini, Lyn Alden, Raoul Pal', platform: 'Twitter/X', importance: 'متوسط' },
  { id: 10, asset: 'USD', speech: 'تصريحات CEOs الكبار (Larry Fink, Jamie Dimon)', speaker: 'BlackRock / JPMorgan CEOs', platform: 'CNBC + Bloomberg + Twitter', importance: 'عالي' },
  { id: 11, asset: 'USD', speech: 'خطابات أعضاء FOMC الأفراد (Hawkish/Dovish)', speaker: 'FOMC Members', platform: 'Federal Reserve', importance: 'عالي' },
  { id: 12, asset: 'CNY', speech: 'تصريحات البنك المركزي الصيني (PBOC)', speaker: 'PBOC Governor', platform: 'China Central Bank', importance: 'عالي' },
]

const TIMEFRAME_LABELS = ['1M', '5M', '15M', '30M', '1H', '4H']

function randomSignal() {
  const s = ['buy', 'sell', 'neutral']
  return s[Math.floor(Math.random() * s.length)]
}

function generateRow() {
  return {
    prev: (Math.random() * 5).toFixed(2),
    expected: (Math.random() * 5).toFixed(2),
    actual: (Math.random() * 5).toFixed(2),
    result: Math.random() > 0.5 ? 'إيجابي' : 'سلبي',
    signals: TIMEFRAME_LABELS.map(() => randomSignal()),
    score: (Math.random() * 10).toFixed(1),
    pct: (Math.random() * 2).toFixed(2),
  }
}

const impColor = (imp: string) => {
  if (imp === 'عالي جداً') return 'text-red-400'
  if (imp === 'عالي') return 'text-yellow-400'
  if (imp === 'متوسط') return 'text-blue-400'
  return 'text-gray-400'
}

export default function FundamentalTable() {
  const { language, selectedSymbol } = useAppStore()
  const isRtl = language === 'ar'
  const [tab, setTab] = useState<'indicators' | 'news' | 'speeches'>('indicators')
  const [collapsed, setCollapsed] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [rows] = useState(() => ({
    indicators: ECONOMIC_INDICATORS.map(r => ({ ...r, ...generateRow() })),
    news: NEWS_REPORTS.map(r => ({ ...r, ...generateRow() })),
    speeches: SPEECHES_TWEETS.map(r => ({ ...r, ...generateRow() })),
  }))

  useEffect(() => {
    const t = setInterval(() => setLastUpdate(new Date()), 60000)
    return () => clearInterval(t)
  }, [])

  const summarySignal = randomSignal()
  const confidence = (55 + Math.random() * 40).toFixed(1)

  const tabs = [
    { key: 'indicators', label: '🏛️ المؤشرات الاقتصادية', count: 40 },
    { key: 'news', label: '📰 الأخبار والتقارير', count: 12 },
    { key: 'speeches', label: '🎤 الخطابات والتغريدات', count: 12 },
  ] as const

  return (
    <div className="bg-dark-800 border border-gold/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-dark-700/50 border-b border-gold/20 cursor-pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">📰</span>
          <div>
            <div className="text-gold font-bold text-sm">
              جدول ٢ — التحليل الأساسي والتقويم الاقتصادي — الوزن <span className="text-white">20٪</span> من التحليل الكامل
            </div>
            <div className="text-gray-500 text-xs">
              ثلاثة أقسام: المؤشرات الاقتصادية (40+) + الأخبار والتقارير (12+) + الخطابات والتصريحات والتغريدات (12+)
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-gray-500 text-xs">آخر تحديث: {lastUpdate.toLocaleTimeString('ar-SA')}</span>
          <span className="text-gold text-lg">{collapsed ? '▼' : '▲'}</span>
        </div>
      </div>

      {!collapsed && (
        <div>
          {/* Tabs */}
          <div className="flex border-b border-gold/20 px-4 pt-3 gap-1">
            {tabs.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-3 py-2 text-xs rounded-t-lg font-medium transition-colors ${
                  tab === t.key
                    ? 'bg-gold text-dark-900 font-bold'
                    : 'text-gray-400 hover:text-gold'
                }`}
              >
                {t.label} ({t.count}+)
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            {/* SECTION 1: Economic Indicators */}
            {tab === 'indicators' && (
              <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
                <thead className="bg-dark-700/50">
                  <tr>
                    {['#', 'الأصل', 'المؤشر الاقتصادي', 'UTC', 'KSA', 'السابق', 'المتوقع', 'الفعلي', 'التحليل', 'النتيجة', ...TIMEFRAME_LABELS, 'الدرجة', '% 20٪'].map((h, i) => (
                      <th key={i} className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.indicators.map((row: any) => (
                    <tr key={row.id} className="border-b border-dark-600 hover:bg-dark-700/30">
                      <td className="px-2 py-2 text-gray-500">{row.id}</td>
                      <td className="px-2 py-2 text-blue-400 font-bold">{row.asset}</td>
                      <td className="px-2 py-2 text-white min-w-[200px]">{row.indicator}</td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap">{row.utc}</td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap">{row.local}</td>
                      <td className="px-2 py-2 text-gray-300">{row.prev}%</td>
                      <td className="px-2 py-2 text-gray-300">{row.expected}%</td>
                      <td className="px-2 py-2 text-white font-medium">{row.actual}%</td>
                      <td className="px-2 py-2 text-gray-400 min-w-[120px] text-xs">
                        <span className="text-gray-500">تحليل ذكاء اصطناعي لحظي...</span>
                      </td>
                      <td className="px-2 py-2">
                        <SignalBadge s={row.result === 'إيجابي' ? 'buy' : 'sell'} />
                      </td>
                      {row.signals.map((sig: string, i: number) => (
                        <td key={i} className="px-1 py-2"><TFCell tf={sig} /></td>
                      ))}
                      <td className="px-2 py-2 text-gold font-bold">{row.score}</td>
                      <td className="px-2 py-2 text-gray-400">{row.pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* SECTION 2: News & Reports */}
            {tab === 'news' && (
              <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
                <thead className="bg-dark-700/50">
                  <tr>
                    {['#', 'الأصل', 'الخبر / التقرير', 'التاريخ', 'المصدر', 'الأهمية', 'التحليل', 'النتيجة', ...TIMEFRAME_LABELS, 'الدرجة', '% 20٪'].map((h, i) => (
                      <th key={i} className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.news.map((row: any) => (
                    <tr key={row.id} className="border-b border-dark-600 hover:bg-dark-700/30">
                      <td className="px-2 py-2 text-gray-500">{row.id}</td>
                      <td className="px-2 py-2 text-blue-400 font-bold">{row.asset}</td>
                      <td className="px-2 py-2 text-white min-w-[200px]">{row.news}</td>
                      <td className="px-2 py-2 text-gray-400">{row.date}</td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap">{row.source}</td>
                      <td className={`px-2 py-2 font-medium whitespace-nowrap ${impColor(row.importance)}`}>{row.importance}</td>
                      <td className="px-2 py-2 text-gray-400 min-w-[120px]">
                        <span className="text-gray-500">تحليل ذكاء اصطناعي لحظي...</span>
                      </td>
                      <td className="px-2 py-2">
                        <SignalBadge s={row.result === 'إيجابي' ? 'buy' : 'sell'} />
                      </td>
                      {row.signals.map((sig: string, i: number) => (
                        <td key={i} className="px-1 py-2"><TFCell tf={sig} /></td>
                      ))}
                      <td className="px-2 py-2 text-gold font-bold">{row.score}</td>
                      <td className="px-2 py-2 text-gray-400">{row.pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* SECTION 3: Speeches & Tweets */}
            {tab === 'speeches' && (
              <table className="w-full text-xs" dir={isRtl ? 'rtl' : 'ltr'}>
                <thead className="bg-dark-700/50">
                  <tr>
                    {['#', 'الأصل', 'الخطاب / التصريح / التغريدة', 'المتحدث', 'المنصة', 'الأهمية', 'التحليل', 'النتيجة', ...TIMEFRAME_LABELS, 'الدرجة', '% 20٪'].map((h, i) => (
                      <th key={i} className="px-2 py-2 text-gold text-right font-medium border-b border-gold/20 whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.speeches.map((row: any) => (
                    <tr key={row.id} className="border-b border-dark-600 hover:bg-dark-700/30">
                      <td className="px-2 py-2 text-gray-500">{row.id}</td>
                      <td className="px-2 py-2 text-blue-400 font-bold">{row.asset}</td>
                      <td className="px-2 py-2 text-white min-w-[180px]">{row.speech}</td>
                      <td className="px-2 py-2 text-gray-300 whitespace-nowrap">{row.speaker}</td>
                      <td className="px-2 py-2 text-gray-400 whitespace-nowrap">{row.platform}</td>
                      <td className={`px-2 py-2 font-medium whitespace-nowrap ${impColor(row.importance)}`}>{row.importance}</td>
                      <td className="px-2 py-2 text-gray-400 min-w-[120px]">
                        <span className="text-gray-500">تحليل ذكاء اصطناعي لحظي...</span>
                      </td>
                      <td className="px-2 py-2">
                        <SignalBadge s={row.result === 'إيجابي' ? 'buy' : 'sell'} />
                      </td>
                      {row.signals.map((sig: string, i: number) => (
                        <td key={i} className="px-1 py-2"><TFCell tf={sig} /></td>
                      ))}
                      <td className="px-2 py-2 text-gold font-bold">{row.score}</td>
                      <td className="px-2 py-2 text-gray-400">{row.pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Summary Box */}
          <div className="p-4 border-t border-gold/20 bg-dark-700/30">
            <div className="text-gold font-bold text-xs mb-3">🎯 الاتجاه العام والقرار النهائي اللحظي للتحليل الأساسي</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-dark-800 rounded-lg p-3">
                <div className="text-gray-400 text-xs mb-1">الأصل المختار</div>
                <div className="text-gold font-bold">{selectedSymbol}</div>
              </div>
              <div className="bg-dark-800 rounded-lg p-3">
                <div className="text-gray-400 text-xs mb-1">الاتجاه العام (1D)</div>
                <SignalBadge s={summarySignal} />
              </div>
              <div className="bg-dark-800 rounded-lg p-3">
                <div className="text-gray-400 text-xs mb-1">درجة الثقة</div>
                <div className="text-white font-bold">{confidence}%</div>
              </div>
              <div className="bg-dark-800 rounded-lg p-3">
                <div className="text-gray-400 text-xs mb-1">مساهمة التحليل الأساسي</div>
                <div className="text-gold font-bold">20٪ من 100٪</div>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-6 gap-2">
              {TIMEFRAME_LABELS.map((tf, i) => (
                <div key={i} className="bg-dark-800 rounded-lg p-2 text-center">
                  <div className="text-gray-500 text-xs mb-1">{tf}</div>
                  <SignalBadge s={randomSignal()} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
