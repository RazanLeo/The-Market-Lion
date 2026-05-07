'use client';
import { useEffect, useMemo, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';

const TIMEFRAMES = ['1M','5M','15M','30M','1H','4H','1D','1W','1Mo'] as const;
type TF = typeof TIMEFRAMES[number];

const TF_REF: Record<TF, TF> = {
  '1M':'15M','5M':'30M','15M':'1H','30M':'4H','1H':'4H','4H':'1D','1D':'1W','1W':'1Mo','1Mo':'1Mo'
};

const SYMBOLS = [
  { v:'XAUUSD', label:'XAUUSD — الذهب مقابل الدولار' },
  { v:'XAGUSD', label:'XAGUSD — الفضة مقابل الدولار' },
  { v:'EURUSD', label:'EURUSD — اليورو دولار' },
  { v:'GBPUSD', label:'GBPUSD — الباوند دولار' },
  { v:'USDJPY', label:'USDJPY — الدولار ين' },
  { v:'USDCHF', label:'USDCHF — الدولار فرنك' },
  { v:'USDCAD', label:'USDCAD — الدولار كندي' },
  { v:'AUDUSD', label:'AUDUSD — الأسترالي دولار' },
  { v:'NZDUSD', label:'NZDUSD — النيوزيلندي دولار' },
  { v:'BRENT',  label:'BRENT — نفط برنت' },
  { v:'USOIL',  label:'USOIL — النفط الأمريكي' },
  { v:'BTCUSD', label:'BTCUSD — البيتكوين' },
  { v:'ETHUSD', label:'ETHUSD — الإيثريوم' },
  { v:'NAS100', label:'NAS100 — ناسداك 100' },
  { v:'SPX500', label:'SPX500 — إس آند بي 500' },
  { v:'US30',   label:'US30 — داو جونز' },
  { v:'GER40',  label:'GER40 — داكس الألماني' },
  { v:'UK100',  label:'UK100 — فوتسي البريطاني' },
];

const TICKER_SYMBOLS = ['XAUUSD','EURUSD','GBPUSD','USDJPY','USDCHF','USDCAD','AUDUSD','BRENT','USOIL','BTCUSD','ETHUSD','NAS100'];

// 23 أداة من جدول الأدوات الأساسية
const TOOLS_LIST = [
  'مدرسة البرايس أكشن مدمجة مع التداول العاري (القمم/القيعان/Pivot Points/الشموع اليابانية)',
  'خطوط الدعم والمقاومة الأساسية',
  'خطوط الدعم والمقاومة الفرعية',
  'خطوط الاتجاه',
  'متوسط بسيط 200',
  'متوسط بسيط 60',
  'متوسط أسي 7',
  'متوسط أسي 21',
  'فراما 126',
  'القناة السعرية - الانحراف المعياري',
  'القناة السعرية - الانحدار الخطي',
  'النماذج الفنية السعرية',
  'مدرسة الأموال الذكية SMC + ICT (Order Blocks, BOS, CHoCH, FVG, Breaker, Mitigation, Inducement, Premium/Discount, Imbalance)',
  'منهجية ICT الكاملة (Killzones, Market Maker Models, OTE 61.8%, Liquidity Pools, Judas Swing, Silver Bullet, Power of 3 - AMD)',
  'مناطق العرض والطلب Supply & Demand',
  'مناطق التجميع والتصريف Accumulation/Distribution',
  'مناطق البلوك أوردر Block Orders',
  'تدفق الأوامر Order Flow',
  'حجم التداول Volume',
  'الفخاخ ونظرية وايكوف ومناطق ضرب الاستوب (BSL, SSL, Liquidity Sweep)',
  'تصحيح فيبوناتشي Fibonacci Retracement',
  'امتداد فيبوناتشي Fibonacci Extension',
  'RSI مع دايفرجنس',
  'راصد الصفقات والبوك ماب وسيولة صناع السوق',
];

// 47 مدرسة كاملة
const SCHOOLS_LIST = [
  'نظرية داو Dow Theory',
  'IPDA - خوارزمية التسليم المصرفي',
  'شوكة أندروز Andrews Pitchfork',
  'نقطة وشكل Point & Figure',
  'صندوق دارفاس Darvas Box Theory',
  'تحليل مراحل وينشتاين Weinstein Stage Analysis',
  'الفراكتل ونظرية الفوضى Fractal & Chaos - Bill Williams',
  'نظام السلحفاة Turtle Trading',
  'موجات إليوت Elliott Wave Theory',
  'طريقة وايكوف Wyckoff Method',
  'دورات هيرست Hurst Cycle Analysis',
  'سلسلة دي مارك DeMark Sequential & Combo',
  'موجة كوندراتيف Kondratieff Wave',
  'تحليل الحجم والانتشار VSA',
  'ملف السوق Market Profile',
  'VWAP',
  'نظرية مزاد السوق Auction Market Theory',
  'البصمة والدلتا Footprint Charts & Delta',
  'تداول المجمعات المظلمة Dark Pool Trading',
  'ملف الحجم الأفقي Volume Profile / TPO',
  'مروحة فيبوناتشي (Fan, Time Zones, Arcs, Circles)',
  'مقاومة مروحة فيبوناتشي Resistance Fan',
  'نظرية غان السعرية Gann Price Theory',
  'الأنماط التوافقية Harmonic Patterns',
  'الهندسة المقدسة Sacred Geometry / Golden Ratio',
  'Renko',
  'Heikin Ashi',
  'Kagi',
  'Three Line Break',
  'Range Bars',
  'Tick Charts',
  'ارتداد للمتوسط Mean Reversion',
  'التحليل بين الأسواق Intermarket Analysis',
  'تقرير COT - Commitment of Traders',
  'اتساع السوق Market Breadth',
  'الموسمية Seasonality',
  'الذكاء الاصطناعي AI & ML in TA',
  'تحليل القوة النسبية Mansfield RS',
  'CANSLIM Growth Trading',
  'مربع غان الزمني Gann Square of Time',
  'تداول الزخم Momentum Trading',
  'النجمة الزمنية لغان Gann Star',
  'مناطق الزمن الفيبوناتشية Fibonacci Time Zones',
  'الدورات الزمنية الدورية Cyclic Time Analysis',
  'التوقيت الفلكي Financial Astrology',
  'تحليل جلسات الأسواق Sessions Analysis',
  'Volume Charts',
];

// 135+ مؤشر مصنّف
const INDICATORS_LIST: { name: string; cat: string }[] = [
  { name:'SMA - Simple Moving Average', cat:'اتجاه' },
  { name:'EMA - Exponential Moving Average', cat:'اتجاه' },
  { name:'WMA - Weighted Moving Average', cat:'اتجاه' },
  { name:'DEMA - Double EMA', cat:'اتجاه' },
  { name:'TEMA - Triple EMA', cat:'اتجاه' },
  { name:'HMA - Hull MA', cat:'اتجاه' },
  { name:'FRAMA - Fractal Adaptive MA', cat:'اتجاه' },
  { name:'KAMA - Kaufman Adaptive MA', cat:'اتجاه' },
  { name:'VWMA - Volume Weighted MA', cat:'اتجاه' },
  { name:'TRIX', cat:'اتجاه' },
  { name:'ALMA - Arnaud Legoux MA', cat:'اتجاه' },
  { name:'McGinley Dynamic', cat:'اتجاه' },
  { name:'Ichimoku Kinko Hyo', cat:'اتجاه' },
  { name:'Parabolic SAR', cat:'اتجاه' },
  { name:'Supertrend', cat:'اتجاه' },
  { name:'Linear Regression', cat:'اتجاه' },
  { name:'ZigZag', cat:'اتجاه' },
  { name:'Volatility Stop', cat:'اتجاه' },
  { name:'ADX + DMI', cat:'اتجاه' },
  { name:'RSI - Relative Strength Index', cat:'زخم' },
  { name:'Stochastic Oscillator', cat:'زخم' },
  { name:'Stochastic RSI', cat:'زخم' },
  { name:'MACD', cat:'زخم' },
  { name:'CCI - Commodity Channel Index', cat:'زخم' },
  { name:'Williams %R', cat:'زخم' },
  { name:'ROC - Rate of Change', cat:'زخم' },
  { name:'Awesome Oscillator', cat:'زخم' },
  { name:'Momentum', cat:'زخم' },
  { name:'MFI - Money Flow Index', cat:'زخم' },
  { name:'Ultimate Oscillator', cat:'زخم' },
  { name:'Aroon Indicator + Oscillator', cat:'زخم' },
  { name:'Vortex Indicator (VI)', cat:'زخم' },
  { name:'Coppock Curve', cat:'زخم' },
  { name:'Chande Momentum Oscillator', cat:'زخم' },
  { name:'TSI - True Strength Index', cat:'زخم' },
  { name:'PPO - Percentage Price Oscillator', cat:'زخم' },
  { name:'Klinger Oscillator', cat:'زخم' },
  { name:'KST - Know Sure Thing', cat:'زخم' },
  { name:'Elder Ray Index', cat:'زخم' },
  { name:'Fisher Transform', cat:'زخم' },
  { name:'Schaff Trend Cycle', cat:'زخم' },
  { name:'ATR - Average True Range', cat:'تقلب' },
  { name:'Bollinger Bands', cat:'تقلب' },
  { name:'Keltner Channels', cat:'تقلب' },
  { name:'Donchian Channels', cat:'تقلب' },
  { name:'Standard Deviation', cat:'تقلب' },
  { name:'Historical Volatility', cat:'تقلب' },
  { name:'Chaikin Volatility', cat:'تقلب' },
  { name:'Mass Index', cat:'تقلب' },
  { name:'Choppiness Index', cat:'تقلب' },
  { name:'Volatility Index (VIX)', cat:'تقلب' },
  { name:'Bollinger Bandwidth', cat:'تقلب' },
  { name:'Bollinger %B', cat:'تقلب' },
  { name:'Volume', cat:'حجم' },
  { name:'OBV - On Balance Volume', cat:'حجم' },
  { name:'Volume Profile (VPVR/VPSR)', cat:'حجم' },
  { name:'Accumulation/Distribution Line', cat:'حجم' },
  { name:'Chaikin Money Flow + Oscillator', cat:'حجم' },
  { name:'Force Index', cat:'حجم' },
  { name:'Ease of Movement', cat:'حجم' },
  { name:'Volume Oscillator', cat:'حجم' },
  { name:'Negative Volume Index', cat:'حجم' },
  { name:'Positive Volume Index', cat:'حجم' },
  { name:'VWAP', cat:'حجم' },
  { name:'Anchored VWAP', cat:'حجم' },
  { name:'Volume Weighted MACD', cat:'حجم' },
  { name:'PVT - Price Volume Trend', cat:'حجم' },
  { name:'Fibonacci Retracement', cat:'دعم/مقاومة' },
  { name:'Fibonacci Extension', cat:'دعم/مقاومة' },
  { name:'Fibonacci Fan', cat:'دعم/مقاومة' },
  { name:'Fibonacci Time Zones', cat:'دعم/مقاومة' },
  { name:'Fibonacci Arcs', cat:'دعم/مقاومة' },
  { name:'Fibonacci Speed Resistance Fan', cat:'دعم/مقاومة' },
  { name:'Pivot Points - Standard', cat:'دعم/مقاومة' },
  { name:'Pivot Points - Fibonacci', cat:'دعم/مقاومة' },
  { name:'Pivot Points - Camarilla', cat:'دعم/مقاومة' },
  { name:'Pivot Points - Woodie', cat:'دعم/مقاومة' },
  { name:'Pivot Points - DeMark', cat:'دعم/مقاومة' },
  { name:'Auto Fib', cat:'دعم/مقاومة' },
  { name:'Auto Trend Lines', cat:'دعم/مقاومة' },
  { name:'Ichimoku Cloud', cat:'نظام متكامل' },
  { name:'McClellan Oscillator', cat:'نظام متكامل' },
  { name:'Arms Index (TRIN)', cat:'نظام متكامل' },
  { name:'Advance/Decline Line', cat:'نظام متكامل' },
  { name:'Bollinger %B + Bandwidth Combo', cat:'نظام متكامل' },
  { name:'Volume Profile + POC/HVN/LVN', cat:'سلوك مؤسسي' },
  { name:'Market Profile (TPO)', cat:'سلوك مؤسسي' },
  { name:'VWAP + Standard Deviation Bands', cat:'سلوك مؤسسي' },
  { name:'Cumulative Delta', cat:'سلوك مؤسسي' },
  { name:'Order Flow Imbalance', cat:'سلوك مؤسسي' },
  { name:'Footprint Delta', cat:'سلوك مؤسسي' },
  { name:'Open Interest', cat:'سلوك مؤسسي' },
  { name:'Lion ARC - Adaptive Regime Compass', cat:'Lion مخصص' },
  { name:'Lion BUMP - Bullish Up Momentum Pulse', cat:'Lion مخصص' },
  { name:'Lion DUMP - Distribution Under Major Pressure', cat:'Lion مخصص' },
  { name:'Lion ROAR - Range Of Active Reversal', cat:'Lion مخصص' },
  { name:'Lion CLAW - Composite Liquidity Absorption Wave', cat:'Lion مخصص' },
  { name:'Lion MANE - Multi-frame Adaptive Noise Estimator', cat:'Lion مخصص' },
  { name:'Lion PRIDE - Predictive Regime Index Decision Engine', cat:'Lion مخصص' },
  { name:'Lion HUNT - Higher Unit Neutral Trigger', cat:'Lion مخصص' },
  { name:'Lion FANG - Fast Adaptive Noise Gate', cat:'Lion مخصص' },
  { name:'Lion JUMP - Junior Up-Move Predictor', cat:'Lion مخصص' },
  { name:'Lion CUB - Confluence Unified Breadth', cat:'Lion مخصص' },
  { name:'Lion KING - Key Indicator Net Gauge', cat:'Lion مخصص' },
  { name:'Lion SAFARI - Session Adaptive Filter', cat:'Lion مخصص' },
  { name:'Lion EYES - Early Yield Entry Signal', cat:'Lion مخصص' },
  { name:'Lion PAW - Price Action Wave', cat:'Lion مخصص' },
  { name:'Lion TAIL - Trend Adaptive Indicator Loop', cat:'Lion مخصص' },
  { name:'Lion DEN - Decisive Entry Network', cat:'Lion مخصص' },
  { name:'Lion ROCK - Robust Oscillator with Cycle Kernel', cat:'Lion مخصص' },
  { name:'Lion SNARE - Stop-Hunt & Absorption Reversal Engine', cat:'Lion مخصص' },
  { name:'Lion HEART - Higher Edge Adaptive Real Trend', cat:'Lion مخصص' },
];

const BOOKMAP_LIST = [
  'تدفق الأوامر Order Flow Trading (Time & Sales)',
  'عمق السوق DOM (Depth of Market)',
  'الدلتا التراكمية Cumulative Delta',
  'الحجم الممتص Absorbed Volume',
  'أوامر الجبل الجليدي Iceberg Orders',
  'كتل الشراء الكبيرة BSL',
  'كتل البيع الكبيرة SSL',
  'مسح السيولة Liquidity Sweep',
];

const TRADE_PLAN_FIELDS = [
  { k:'balance', label:'رصيد المحفظة / رأس المال', def:'$25,000' },
  { k:'risk_pct', label:'نسبة المخاطرة', def:'3%' },
  { k:'risk_amt', label:'مبلغ المخاطرة', def:'$750' },
  { k:'leverage', label:'الرافعة المالية', def:'1:100' },
  { k:'lot_size', label:'حجم اللوت / العقد', def:'—' },
  { k:'margin_required', label:'الهامش المطلوب', def:'—' },
  { k:'margin_used', label:'الهامش المستخدم', def:'—' },
  { k:'margin_free', label:'الهامش المتاح', def:'$24,250' },
  { k:'margin_level', label:'مستوى الهامش', def:'—' },
  { k:'market', label:'تحديد السوق المالي', def:'فوركس / معادن' },
  { k:'asset', label:'تحديد الأصل المالي', def:'XAU/USD' },
  { k:'trade_type', label:'نوع التداول', def:'CFD' },
  { k:'tf', label:'الإطار الزمني', def:'1H' },
  { k:'side', label:'تحديد الصفقة شراء أم بيع', def:'انتظار' },
  { k:'entry', label:'نقطة الدخول (السعر)', def:'—' },
  { k:'tp1', label:'الهدف ريشيو 1 لجني الأرباح', def:'—' },
  { k:'tp2', label:'الهدف ريشيو 2 لجني الأرباح', def:'—' },
  { k:'tp3', label:'الهدف ريشيو 3 لجني الأرباح', def:'—' },
  { k:'tp_final', label:'آخر نقطة لجني الأرباح والخروج', def:'—' },
  { k:'sl', label:'وقف الخسارة والخروج (السعر)', def:'—' },
  { k:'sl_trail', label:'تعديل وقف الخسارة (تحريك بعد كل ريشيو)', def:'تلقائي' },
  { k:'reinforce', label:'تحديد منطقة التعزيز', def:'—' },
  { k:'pip_calc', label:'حساب البيب (صعود/هبوط)', def:'—' },
  { k:'profit_calc', label:'حساب الربح (بناء على البيب)', def:'—' },
  { k:'loss_calc', label:'حساب الخسارة (بناء على البيب)', def:'$750' },
  { k:'commission', label:'العمولة + السبريد + السواب', def:'$7.5 + $0.1' },
  { k:'cumulative', label:'الأرباح التراكمية', def:'—' },
  { k:'eval_daily', label:'تقييم المحفظة اليومي', def:'متوفر في تبويب الصفقات' },
  { k:'eval_weekly', label:'تقييم المحفظة الأسبوعي', def:'متوفر في تبويب الصفقات' },
  { k:'eval_monthly', label:'تقييم المحفظة الشهري', def:'متوفر في تبويب الصفقات' },
];

type Signal = 'BUY' | 'SELL' | 'NEUTRAL' | null;
type RowSignals = Partial<Record<TF, { sig: Signal; conf: number }>>;
type SectionPayload = {
  rows: { name: string; cat?: string; analysis?: string; signals: RowSignals; draw?: boolean }[];
  decision_per_tf: Partial<Record<TF, { sig: Signal; conf: number }>>;
  weight_pct: number;
  score: number;
};

const EMPTY_SECTION = (rows: { name: string; cat?: string }[], weight_pct: number): SectionPayload => ({
  rows: rows.map(r => ({ name: r.name, cat: r.cat, signals: {}, draw: false })),
  decision_per_tf: {},
  weight_pct,
  score: 0,
});

function sigBadge(s: { sig: Signal; conf: number } | undefined) {
  if (!s || !s.sig || s.sig === 'NEUTRAL') return <span className="text-zinc-500">—</span>;
  const isBuy = s.sig === 'BUY';
  return (
    <span className={`inline-flex flex-col items-center justify-center text-[10px] leading-tight px-1 py-0.5 rounded font-bold ${
      isBuy ? 'bg-emerald-700/30 text-emerald-300 border border-emerald-700/60' : 'bg-rose-700/30 text-rose-300 border border-rose-700/60'
    }`}>
      <span>{isBuy ? 'شراء' : 'بيع'}</span>
      <span className="opacity-80">{s.conf.toFixed(0)}%</span>
    </span>
  );
}

function decisionBadge(d: { sig: Signal; conf: number } | undefined) {
  if (!d || !d.sig) return <span className="text-zinc-500 text-xs">—</span>;
  if (d.sig === 'NEUTRAL')
    return <span className="text-amber-300 bg-amber-900/30 border border-amber-700/40 px-2 py-0.5 rounded text-xs">محايد ({d.conf.toFixed(1)}%)</span>;
  const isBuy = d.sig === 'BUY';
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold ${
      isBuy ? 'bg-emerald-700/40 text-emerald-200 border border-emerald-600' : 'bg-rose-700/40 text-rose-200 border border-rose-600'
    }`}>{isBuy ? 'شراء' : 'بيع'} ({d.conf.toFixed(1)}%)</span>
  );
}

function SignalTable({ title, icon, weightLabel, payload, onToggleDraw }: {
  title: string; icon: string; weightLabel: string;
  payload: SectionPayload;
  onToggleDraw: (rowIdx: number) => void;
}) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950/50 overflow-hidden mb-6">
      <header className="flex items-center justify-between px-4 py-3 bg-zinc-900/70 border-b border-zinc-800">
        <h3 className="text-gold font-bold text-sm md:text-base">
          <span className="ms-2">{icon}</span> {title}
        </h3>
        <span className="text-xs text-zinc-400">{weightLabel}</span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] md:text-xs border-collapse">
          <thead className="bg-zinc-900/80 text-zinc-300">
            <tr>
              <th className="text-start p-2 sticky right-0 bg-zinc-900 min-w-[260px]">الاسم</th>
              {TIMEFRAMES.map(tf => (
                <th key={tf} className="p-1 text-center min-w-[64px]">{tf}</th>
              ))}
              <th className="p-2 text-center">الثقة</th>
              <th className="p-2 text-center">الاتجاه</th>
              <th className="p-2 text-center">رسم</th>
            </tr>
          </thead>
          <tbody>
            {payload.rows.map((r, i) => {
              const allConfs = TIMEFRAMES.map(tf => r.signals[tf]?.conf ?? 0);
              const avgConf = allConfs.reduce((a,b)=>a+b,0) / TIMEFRAMES.length;
              const buys = TIMEFRAMES.filter(tf => r.signals[tf]?.sig === 'BUY').length;
              const sells = TIMEFRAMES.filter(tf => r.signals[tf]?.sig === 'SELL').length;
              const dir: Signal = buys === sells ? 'NEUTRAL' : (buys > sells ? 'BUY' : 'SELL');
              return (
                <tr key={i} className="border-t border-zinc-800/70 hover:bg-zinc-900/40">
                  <td className="p-2 sticky right-0 bg-zinc-950/95 text-zinc-200">
                    <div className="font-medium">{r.name}</div>
                    {r.cat && <div className="text-[10px] text-zinc-500 mt-0.5">{r.cat}</div>}
                  </td>
                  {TIMEFRAMES.map(tf => (
                    <td key={tf} className="p-1 text-center align-middle">{sigBadge(r.signals[tf])}</td>
                  ))}
                  <td className="p-2 text-center text-zinc-300">{avgConf.toFixed(0)}%</td>
                  <td className="p-2 text-center">
                    {dir === 'NEUTRAL'
                      ? <span className="text-amber-400">—</span>
                      : <span className={dir === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}>{dir === 'BUY' ? '▲' : '▼'}</span>}
                  </td>
                  <td className="p-2 text-center">
                    <button onClick={() => onToggleDraw(i)}
                      className={`text-[10px] px-2 py-1 rounded border ${
                        r.draw ? 'bg-gold/20 text-gold border-gold/60' : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                      }`}>
                      {r.draw ? '● مفعّل' : '○ إيقاف'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot className="bg-zinc-900/60 border-t-2 border-gold/40">
            <tr>
              <td className="p-2 text-gold font-bold text-xs">القرار حسب الإطار الزمني</td>
              {TIMEFRAMES.map(tf => (
                <td key={tf} className="p-1 text-center">{decisionBadge(payload.decision_per_tf[tf])}</td>
              ))}
              <td className="p-2 text-center text-gold font-bold" colSpan={3}>
                المجموع المرجح: {payload.score.toFixed(1)} / {payload.weight_pct}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const [symbol, setSymbol] = useState<string>('XAUUSD');
  const [tf, setTf] = useState<TF>('1H');
  const [balance, setBalance] = useState<number>(25000);
  const [riskPct, setRiskPct] = useState<number>(3);
  const [tradeMode, setTradeMode] = useState<'manual' | 'bot'>('manual');
  const [broker, setBroker] = useState<string>('Capital.com');
  const [tickers, setTickers] = useState<{symbol:string;price:number;change:number}[]>([]);

  const [fundamental, setFundamental] = useState<SectionPayload>(EMPTY_SECTION([{name:'(لم تُحدّث الأخبار بعد)'}], 20));
  const [tools, setTools] = useState<SectionPayload>(EMPTY_SECTION(TOOLS_LIST.map(n=>({name:n})), 30));
  const [schools, setSchools] = useState<SectionPayload>(EMPTY_SECTION(SCHOOLS_LIST.map(n=>({name:n})), 30));
  const [indicators, setIndicators] = useState<SectionPayload>(EMPTY_SECTION(INDICATORS_LIST, 10));
  const [bookmap, setBookmap] = useState<SectionPayload>(EMPTY_SECTION(BOOKMAP_LIST.map(n=>({name:n})), 10));
  const [confluence, setConfluence] = useState<{ pct:number; decision_per_tf: Partial<Record<TF, {sig:Signal;conf:number}>>; final: { sig: Signal; conf: number } } | null>(null);
  const [tradePlan, setTradePlan] = useState<Record<string,string>>({});

  const refTf = TF_REF[tf];
  const riskAmount = (balance * riskPct) / 100;

  useEffect(() => {
    let stop = false;
    const fetchTickers = async () => {
      try {
        const r = await fetch(`${API}/market/tickers?symbols=${TICKER_SYMBOLS.join(',')}`);
        if (!r.ok) return;
        const d = await r.json();
        if (!stop) setTickers(d.tickers || []);
      } catch {}
    };
    fetchTickers();
    const id = setInterval(fetchTickers, 5000);
    return () => { stop = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    let stop = false;
    const poll = async () => {
      try {
        const url = (p: string) => `${API}/analysis/${p}?symbol=${symbol}&timeframe=${tf}`;
        const [fund, tls, sch, ind, bm, conf, tp] = await Promise.all([
          fetch(url('fundamental')).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(url('tools')).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(url('schools')).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(url('indicators')).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(url('flow')).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(url('confluence')).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(url('trade-plan') + `&balance=${balance}&risk=${riskPct}`).then(r => r.ok ? r.json() : null).catch(() => null),
        ]);
        if (stop) return;
        if (fund) setFundamental(prev => mergePayload(prev, fund));
        if (tls) setTools(prev => mergePayload(prev, tls));
        if (sch) setSchools(prev => mergePayload(prev, sch));
        if (ind) setIndicators(prev => mergePayload(prev, ind));
        if (bm) setBookmap(prev => mergePayload(prev, bm));
        if (conf) setConfluence(conf);
        if (tp) setTradePlan(tp.fields || {});
      } catch {}
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => { stop = true; clearInterval(id); };
  }, [symbol, tf, balance, riskPct]);

  function mergePayload(prev: SectionPayload, incoming: any): SectionPayload {
    if (!incoming || !Array.isArray(incoming.rows)) return prev;
    const byName = new Map<string, any>(incoming.rows.map((r:any) => [r.name, r]));
    return {
      ...prev,
      rows: prev.rows.map(r => {
        const found = byName.get(r.name);
        if (!found) return r;
        return { ...r, signals: found.signals || {}, analysis: found.analysis };
      }),
      decision_per_tf: incoming.decision_per_tf || {},
      score: incoming.score ?? 0,
    };
  }

  const toggleDraw = (section: 'tools'|'schools'|'indicators'|'bookmap'|'fundamental') => (i: number) => {
    const setters = { tools: setTools, schools: setSchools, indicators: setIndicators, bookmap: setBookmap, fundamental: setFundamental } as const;
    const getters = { tools, schools, indicators, bookmap, fundamental } as const;
    const cur = getters[section];
    const next = { ...cur, rows: cur.rows.map((r, idx) => idx === i ? { ...r, draw: !r.draw } : r) };
    setters[section](next);
    fetch(`${API}/chart/draw`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ symbol, timeframe: tf, section, name: cur.rows[i].name, enabled: !cur.rows[i].draw })
    }).catch(()=>{});
  };

  const tvSrc = useMemo(() => `https://s.tradingview.com/widgetembed/?symbol=OANDA:${symbol}&interval=${tfToTvInterval(tf)}&theme=dark&style=1&locale=ar&timezone=Etc/UTC&hide_side_toolbar=0&hide_top_toolbar=0&allow_symbol_change=1&studies=BB@tv-basicstudies,RSI@tv-basicstudies,MACD@tv-basicstudies,VWAP@tv-basicstudies`, [symbol, tf]);

  return (
    <div dir="rtl" className="min-h-screen bg-[#0A0A0A] text-zinc-100 font-sans">
      <header className="sticky top-0 z-40 bg-[#0A0A0A]/95 backdrop-blur border-b border-zinc-900">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/brand/logo.webp" alt="Lion" className="w-12 h-12 rounded-lg object-cover ring-2 ring-gold/40" />
            <div>
              <h1 className="text-gold font-display text-2xl leading-tight">أسد السوق</h1>
              <p className="text-[11px] text-zinc-400">The Market Lion · AI Trading Platform</p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <a className="text-gold border-b-2 border-gold pb-1">لوحة التحكم</a>
            <a href="/trades" className="text-zinc-300 hover:text-gold">الصفقات</a>
            <a href="/portfolio" className="text-zinc-300 hover:text-gold">المحفظة</a>
            <a href="/chat" className="text-zinc-300 hover:text-gold">المحادثة</a>
            <a href="/settings" className="text-zinc-300 hover:text-gold">الإعدادات</a>
          </nav>
          <div className="flex items-center gap-2">
            <span className="text-[10px] bg-rose-600/20 text-rose-300 border border-rose-700 px-2 py-0.5 rounded animate-pulse">● LIVE</span>
            <a href="/profile" className="w-8 h-8 rounded-full bg-gold/20 border border-gold/40 grid place-items-center text-gold text-sm">R</a>
          </div>
        </div>
        <div className="bg-zinc-950 border-y border-zinc-900 overflow-hidden whitespace-nowrap">
          <div className="inline-flex animate-marquee gap-6 px-4 py-1.5 text-[11px]">
            {[...tickers, ...tickers].map((t, i) => (
              <span key={i} className="inline-flex items-center gap-1.5">
                <span className="text-zinc-400">{t.symbol}</span>
                <span className="text-zinc-100 font-mono">{t.price?.toFixed(t.symbol.includes('JPY')?2:4)}</span>
                <span className={t.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                  {t.change >= 0 ? '+' : ''}{t.change?.toFixed(2)}%
                </span>
              </span>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 py-4">
        <section className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-3 mb-6">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <select value={symbol} onChange={e => setSymbol(e.target.value)} className="bg-zinc-900 border border-zinc-700 rounded px-3 py-1.5 text-sm">
              {SYMBOLS.map(s => <option key={s.v} value={s.v}>{s.label}</option>)}
            </select>
            <div className="flex items-center gap-1 ms-auto">
              {TIMEFRAMES.map(t => (
                <button key={t} onClick={() => setTf(t)}
                  className={`text-xs px-2.5 py-1 rounded ${t === tf ? 'bg-gold text-black font-bold' : 'bg-zinc-900 text-zinc-300 hover:bg-zinc-800'}`}>
                  {t}
                </button>
              ))}
            </div>
            <span className="text-xs text-zinc-400">إطار مرجعي: <span className="text-gold">{refTf}</span></span>
          </div>
          <div className="aspect-[16/8] bg-black rounded border border-zinc-800 overflow-hidden">
            <iframe src={tvSrc} className="w-full h-full" allow="fullscreen" title="TradingView" />
          </div>
        </section>

        <section className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4 mb-6">
          <h2 className="text-gold font-bold mb-3">⚙️ ١. خيارات المتداول</h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-sm">
            <Field label="الرصيد ($)">
              <input type="number" value={balance} onChange={e => setBalance(+e.target.value)} className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1" />
            </Field>
            <Field label="نسبة المخاطرة (1-10%)">
              <input type="number" min={1} max={10} value={riskPct} onChange={e => setRiskPct(+e.target.value)} className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1" />
            </Field>
            <Field label="مبلغ المخاطرة">
              <div className="px-2 py-1 bg-zinc-900/70 rounded border border-zinc-800 text-emerald-400">${riskAmount.toFixed(2)}</div>
            </Field>
            <Field label="الإطار للمضاربة">
              <div className="px-2 py-1 bg-zinc-900/70 rounded border border-zinc-800 text-gold">{tf}</div>
            </Field>
            <Field label="الإطار المرجعي">
              <div className="px-2 py-1 bg-zinc-900/70 rounded border border-zinc-800 text-gold">{refTf}</div>
            </Field>
            <Field label="نوع التداول">
              <select value={tradeMode} onChange={e => setTradeMode(e.target.value as any)} className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1">
                <option value="manual">يدوي</option>
                <option value="bot">بوت آلي</option>
              </select>
            </Field>
            <Field label="الوسيط">
              <select value={broker} onChange={e => setBroker(e.target.value)} className="w-full bg-zinc-900 border border-zinc-700 rounded px-2 py-1">
                <option>Capital.com</option><option>IC Markets</option><option>Pepperstone</option><option>Exness</option><option>Saxo</option>
              </select>
            </Field>
          </div>
        </section>

        <SignalTable title="٢. التحليل الأساسي - الأخبار والمؤشرات الاقتصادية" icon="📰" weightLabel="الوزن: 20%" payload={fundamental} onToggleDraw={toggleDraw('fundamental')} />
        <SignalTable title="٣. الأدوات الأساسية - التحليل الفني (24 أداة)" icon="🛠️" weightLabel="الوزن: 30%" payload={tools} onToggleDraw={toggleDraw('tools')} />
        <SignalTable title="٤. مدارس التحليل الفني (47 مدرسة)" icon="🎓" weightLabel="الوزن: 30%" payload={schools} onToggleDraw={toggleDraw('schools')} />
        <SignalTable title="٥. المؤشرات الفنية (112 مؤشر)" icon="📊" weightLabel="الوزن: 10%" payload={indicators} onToggleDraw={toggleDraw('indicators')} />
        <SignalTable title="٦. تدفق الأوامر والبوك ماب (8 بنود)" icon="📚" weightLabel="الوزن: 10%" payload={bookmap} onToggleDraw={toggleDraw('bookmap')} />

        <section className="rounded-lg border-2 border-gold/60 bg-gradient-to-br from-zinc-950 to-black p-6 mb-6">
          <h2 className="text-gold font-display text-2xl text-center mb-4">🎯 نتيجة التوافق والقرار النهائي</h2>
          <div className="text-center mb-4">
            <div className="text-6xl text-gold font-display font-bold">{(confluence?.pct ?? 0).toFixed(1)}%</div>
            <div className="text-xs text-zinc-400 mt-1">نسبة التوافق الإجمالية</div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4 text-center text-xs">
            <Mini label="أساسي / 20" v={fundamental.score} />
            <Mini label="أدوات / 30" v={tools.score} />
            <Mini label="مدارس / 30" v={schools.score} />
            <Mini label="مؤشرات / 10" v={indicators.score} />
            <Mini label="تدفق / 10" v={bookmap.score} />
          </div>
          <div className="rounded border border-zinc-800 bg-zinc-950 overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-zinc-900">
                <tr>
                  <th className="text-start p-2">القسم</th>
                  {TIMEFRAMES.map(t => <th key={t} className="p-1 text-center">{t}</th>)}
                </tr>
              </thead>
              <tbody>
                <DecisionRow label="التحليل الأساسي" weight="20%" data={fundamental.decision_per_tf} />
                <DecisionRow label="الأدوات الأساسية" weight="30%" data={tools.decision_per_tf} />
                <DecisionRow label="مدارس التحليل" weight="30%" data={schools.decision_per_tf} />
                <DecisionRow label="المؤشرات الفنية" weight="10%" data={indicators.decision_per_tf} />
                <DecisionRow label="تدفق الأوامر" weight="10%" data={bookmap.decision_per_tf} />
                <tr className="bg-gold/10 border-t-2 border-gold/50">
                  <td className="p-2 text-gold font-bold">القرار النهائي للنظام</td>
                  {TIMEFRAMES.map(t => <td key={t} className="p-1 text-center">{decisionBadge(confluence?.decision_per_tf[t])}</td>)}
                </tr>
              </tbody>
            </table>
          </div>
          <div className="text-center mt-4">
            <span className="inline-block bg-gold/15 text-gold border border-gold/50 px-4 py-1 rounded">
              قرار النظام النهائي ({tf}): {confluence?.final?.sig === 'BUY' ? 'شراء' : confluence?.final?.sig === 'SELL' ? 'بيع' : 'انتظار'}
              {confluence?.final ? ` (${confluence.final.conf.toFixed(1)}%)` : ''}
            </span>
          </div>
        </section>

        <section className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4 mb-6">
          <h2 className="text-gold font-bold mb-3">📝 ٧. خطة التداول والمخاطرة وحسابات مباشرة</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {TRADE_PLAN_FIELDS.map(f => (
              <div key={f.k} className="flex justify-between gap-2 px-3 py-2 rounded bg-zinc-900/50 border border-zinc-800">
                <span className="text-zinc-400">{f.label}</span>
                <span className="text-zinc-100 font-mono">{tradePlan[f.k] ?? f.def}</span>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
            <button className="px-8 py-3 rounded-lg bg-rose-700 hover:bg-rose-600 text-white font-bold text-sm">🔴 بيع</button>
            <button className="px-8 py-3 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-sm">🟢 شراء</button>
            <button onClick={() => setTradeMode(m => m === 'bot' ? 'manual' : 'bot')}
              className={`px-8 py-3 rounded-lg font-bold text-sm border-2 ${tradeMode === 'bot' ? 'bg-gold text-black border-gold' : 'bg-zinc-900 text-gold border-gold/60'}`}>
              {tradeMode === 'bot' ? '⏹ إيقاف البوت' : '▶ تشغيل البوت'}
            </button>
          </div>
        </section>

        <footer className="border-t border-zinc-900 mt-8 pt-8 pb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="md:col-span-2 flex items-start gap-3">
              <img src="/brand/logo.webp" alt="Lion" className="w-16 h-16 rounded-lg object-cover ring-2 ring-gold/40 flex-shrink-0" />
              <div>
                <h3 className="text-gold font-display text-xl">أسد السوق</h3>
                <p className="text-[11px] text-zinc-400 mt-1">The Market Lion · AI Trading Platform</p>
                <p className="text-[11px] text-zinc-500 mt-2 leading-relaxed">منصّة تحليل وتداول ذكية تعتمد على 47 مدرسة فنية و112 مؤشراً و24 أداة و140 مصدر بيانات أساسية لإنتاج درجة Confluence وقرار تداول عبر 9 إطارات زمنية.</p>
              </div>
            </div>
            <div>
              <h4 className="text-gold text-xs font-bold mb-2">المنصّة</h4>
              <ul className="space-y-1 text-[11px] text-zinc-400">
                <li><a href="/dashboard" className="hover:text-gold">لوحة التحكم</a></li>
                <li><a href="/trades" className="hover:text-gold">الصفقات</a></li>
                <li><a href="/portfolio" className="hover:text-gold">المحفظة</a></li>
                <li><a href="/chat" className="hover:text-gold">المحادثة</a></li>
                <li><a href="/settings" className="hover:text-gold">الإعدادات</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-gold text-xs font-bold mb-2">قانوني</h4>
              <ul className="space-y-1 text-[11px] text-zinc-400">
                <li><a href="/legal/terms" className="hover:text-gold">شروط الاستخدام</a></li>
                <li><a href="/legal/privacy" className="hover:text-gold">سياسة الخصوصية</a></li>
                <li><a href="/legal/risk" className="hover:text-gold">إفصاح المخاطر</a></li>
                <li><a href="/contact" className="hover:text-gold">تواصل معنا</a></li>
              </ul>
            </div>
          </div>
          <div className="text-center text-[11px] text-zinc-500 border-t border-zinc-900 pt-4">
            <p>التداول ينطوي على مخاطر كبيرة وقد يؤدّي إلى خسارة رأس المال. الأداء التاريخي محسوب على Backtest + Walk-Forward وليس وعداً بأرباح مستقبلية.</p>
            <p className="mt-1">© 2026 The Market Lion — أسد السوق · جميع الحقوق محفوظة · المالكة والمؤسِّسة: رزان توفيق الفرّاج · المملكة العربية السعودية</p>
          </div>
        </footer>
      </main>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] text-zinc-400">{label}</span>
      {children}
    </label>
  );
}
function Mini({ label, v }: { label: string; v: number }) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded p-2">
      <div className="text-zinc-400 text-[10px]">{label}</div>
      <div className="text-gold font-bold mt-1">{v.toFixed(1)}</div>
    </div>
  );
}
function DecisionRow({ label, weight, data }: { label: string; weight: string; data: Partial<Record<TF, { sig: Signal; conf: number }>> }) {
  return (
    <tr className="border-t border-zinc-800/70">
      <td className="p-2 text-zinc-300">{label} <span className="text-zinc-500 text-[10px]">({weight})</span></td>
      {TIMEFRAMES.map(t => <td key={t} className="p-1 text-center">{decisionBadge(data[t])}</td>)}
    </tr>
  );
}
function tfToTvInterval(tf: TF): string {
  return ({ '1M':'1','5M':'5','15M':'15','30M':'30','1H':'60','4H':'240','1D':'D','1W':'W','1Mo':'M' } as const)[tf];
}
