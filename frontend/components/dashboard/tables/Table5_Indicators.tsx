'use client';
import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';

type Tier = 'S' | 'A' | 'B' | 'C';
type Category = 'مؤشرات الاتجاه' | 'مؤشرات الزخم' | 'مؤشرات التذبذب والتقلب' | 'مؤشرات الحجم والتدفق' | 'مؤشرات السلوك المؤسسي' | 'مؤشرات الدعم والمقاومة' | 'مؤشرات الأنظمة المتكاملة';

interface IndicatorDef {
  id: number; name: string; category: Category; tier: Tier; strategy: string; code: string; defaultWeight: number;
}

const TIER_WEIGHT: Record<Tier, number> = { S: 0.00241, A: 0.001807, B: 0.001205, C: 0.000602 };
const TF_WEIGHT: Record<string, number> = { '1M': 0.05, '5M': 0.10, '15M': 0.20, '30M': 0.18, '1H': 0.22, '4H': 0.25 };
const TIMEFRAMES = ['1M', '5M', '15M', '30M', '1H', '4H'];
const CATEGORY_ORDER: Category[] = ['مؤشرات الاتجاه','مؤشرات الزخم','مؤشرات التذبذب والتقلب','مؤشرات الحجم والتدفق','مؤشرات السلوك المؤسسي','مؤشرات الدعم والمقاومة','مؤشرات الأنظمة المتكاملة'];
const CATEGORY_EN: Record<Category, string> = {
  'مؤشرات الاتجاه': 'Trend', 'مؤشرات الزخم': 'Momentum', 'مؤشرات التذبذب والتقلب': 'Volatility',
  'مؤشرات الحجم والتدفق': 'Volume & Flow', 'مؤشرات السلوك المؤسسي': 'Institutional',
  'مؤشرات الدعم والمقاومة': 'Support/Resistance', 'مؤشرات الأنظمة المتكاملة': 'Integrated Systems',
};
const TIER_COLORS: Record<Tier, string> = {
  S: 'text-yellow-400 bg-yellow-400/10', A: 'text-blue-400 bg-blue-400/10',
  B: 'text-emerald-400 bg-emerald-400/10', C: 'text-slate-400 bg-slate-400/10',
};

const INDICATORS: IndicatorDef[] = [
  // TREND (1-12)
  { id:1,  name:'Parabolic SAR',           category:'مؤشرات الاتجاه',             tier:'B', code:'parabolic_sar',           defaultWeight:0.001205, strategy:'Points above = sell, below = buy. No solo Flip in sideways — require ADX > 25 + H1 confirmation. Best as dynamic Trailing Stop after entry.' },
  { id:2,  name:'Supertrend',              category:'مؤشرات الاتجاه',             tier:'A', code:'supertrend',               defaultWeight:0.001807, strategy:'Color shift red to green below price = buy, reverse = sell. Settings: (10,3) scalping, (10,2) <15M frames. Only enter with EMA20/50 crossover + BOS.' },
  { id:3,  name:'WMA',                     category:'مؤشرات الاتجاه',             tier:'B', code:'wma',                      defaultWeight:0.001205, strategy:'Price above WMA + uptrend slope = buy, below + downtrend = sell. WMA(9)xWMA(21) crossover for scalp signals; WMA(50) as Dynamic S/R.' },
  { id:4,  name:'HMA',                     category:'مؤشرات الاتجاه',             tier:'B', code:'hma',                      defaultWeight:0.001205, strategy:'HMA(21) color red to green = buy, reverse = sell. Strongest lag reduction — ideal for scalping. Only enter in HMA(200) direction on H1 as HTF filter.' },
  { id:5,  name:'VWMA',                    category:'مؤشرات الاتجاه',             tier:'B', code:'vwma',                     defaultWeight:0.001205, strategy:'Price above VWMA + VWMA divergence up = volume-backed buy pressure. Divergence down = institutional sell. Best for detecting smart money engagement.' },
  { id:6,  name:'DEMA',                    category:'مؤشرات الاتجاه',             tier:'B', code:'dema',                     defaultWeight:0.001205, strategy:'DEMA(8) crosses above DEMA(21) = buy, below = sell. 2x faster than EMA but noise-sensitive — use only in clear trending (ADX > 30).' },
  { id:7,  name:'TEMA',                    category:'مؤشرات الاتجاه',             tier:'B', code:'tema',                     defaultWeight:0.001205, strategy:'TEMA(9)xTEMA(21) crossover = entry signal; TEMA(55) confirms trend. Ideal ultra-fast scalping (1M,5M) — fastest MA with no real lag.' },
  { id:8,  name:'KAMA',                    category:'مؤشرات الاتجاه',             tier:'B', code:'kama',                     defaultWeight:0.001205, strategy:'Price above rising KAMA = buy, below falling = sell. Slows in sideways, accelerates in trends — fewer false signals than EMA.' },
  { id:9,  name:'ALMA',                    category:'مؤشرات الاتجاه',             tier:'B', code:'alma',                     defaultWeight:0.001205, strategy:'ALMA(21) slope up + price break = strong buy. Use ALMA(9) entry, ALMA(50) trend — smoother/more precise than EMA but needs volume confirmation.' },
  { id:10, name:'McGinley Dynamic',        category:'مؤشرات الاتجاه',             tier:'B', code:'mcginley_dynamic',         defaultWeight:0.001205, strategy:'Price above + line rising = buy, below + falling = sell. No lag in rapid moves, no false signals in sideways — best MA for choppy markets.' },
  { id:11, name:'Linear Regression',       category:'مؤشرات الاتجاه',             tier:'B', code:'linear_regression',        defaultWeight:0.001205, strategy:'Price inside regression channel + rising slope = buy at lower band, falling slope = sell at upper. Use Linear Regression Slope to measure trend strength.' },
  { id:12, name:'Volatility Stop',         category:'مؤشرات الاتجاه',             tier:'B', code:'volatility_stop',          defaultWeight:0.001205, strategy:'Points below price = uptrend, above = downtrend. Like Parabolic SAR but ATR-based. Best as Trailing Stop based on actual market swing.' },
  // MOMENTUM (13-28)
  { id:13, name:'RSI',                     category:'مؤشرات الزخم',              tier:'S', code:'rsi',                      defaultWeight:0.00241,  strategy:'Oversold < 30 + Bullish Divergence + structural alignment = strong buy. Overbought > 70 + Bearish Divergence = strong sell. Never solo — always wait divergence. Line 50 divides momentum direction.' },
  { id:14, name:'MACD',                    category:'مؤشرات الزخم',              tier:'S', code:'macd',                     defaultWeight:0.00241,  strategy:'MACD line crosses above signal + green histogram above zero = buy. Below + red histogram below zero = sell. Strongest: Hidden Divergence for trend continuation; Regular Divergence for reversal.' },
  { id:15, name:'Stochastic',              category:'مؤشرات الزخم',              tier:'A', code:'stochastic',               defaultWeight:0.001807, strategy:'%K crosses above %D in zone < 20 = buy, below %D in zone > 80 = sell. Settings: (14,3,3) larger frames, (5,3,3) scalping. Hunt Hidden Divergence for trend confirmation.' },
  { id:16, name:'Stochastic RSI',          category:'مؤشرات الزخم',              tier:'B', code:'stochastic_rsi',           defaultWeight:0.001205, strategy:'Faster than regular Stochastic. Buy on exit from < 20 with upside cross. Sell on exit from > 80 with downside cross. Optimal for ultra-small frames (1M,5M).' },
  { id:17, name:'ADX + DMI',               category:'مؤشرات الزخم',              tier:'S', code:'adx_dmi',                  defaultWeight:0.00241,  strategy:'ADX > 25 = strong trend. +DI above -DI = buy, -DI above +DI = sell. ADX < 20 = sideways — avoid trading. ADX shows strength, DI shows direction.' },
  { id:18, name:'CCI',                     category:'مؤشرات الزخم',              tier:'B', code:'cci',                      defaultWeight:0.001205, strategy:'Above +100 = strong buy momentum, below -100 = strong sell momentum. Strongest in commodities/gold. Use Zero Line Cross as confirmation; divergence for reversals.' },
  { id:19, name:'Williams %R',             category:'مؤشرات الزخم',              tier:'B', code:'williams_r',               defaultWeight:0.001205, strategy:'Read < -80 + start up = buy, > -20 + start down = sell. Similar to Stochastic but faster. Use as 3rd confirmer for RSI & Stochastic.' },
  { id:20, name:'ROC',                     category:'مؤشرات الزخم',              tier:'B', code:'roc',                      defaultWeight:0.001205, strategy:'Rising positive = strong upside momentum (buy). Falling negative = strong downside momentum (sell). Zero line cross = momentum shift.' },
  { id:21, name:'Momentum',               category:'مؤشرات الزخم',              tier:'B', code:'momentum',                 defaultWeight:0.001205, strategy:'Rising positive = buy, falling negative = sell. Similar to ROC but absolute difference. Use zero cross as signal; divergence with price for reversal.' },
  { id:22, name:'Awesome Oscillator',      category:'مؤشرات الزخم',              tier:'B', code:'awesome_oscillator',       defaultWeight:0.001205, strategy:'Histogram red to green above zero = buy (Saucer). Green to red below zero = sell. Strongest: Twin Peaks — two tops above zero with 2nd lower = classic sell signal.' },
  { id:23, name:'Ultimate Oscillator',     category:'مؤشرات الزخم',              tier:'B', code:'ultimate_oscillator',      defaultWeight:0.001205, strategy:'Multi-period momentum (7,14,28). Buy: higher low + bullish divergence + break last high. Sell: lower high + bearish divergence + break last low.' },
  { id:24, name:'TRIX',                    category:'مؤشرات الزخم',              tier:'B', code:'trix',                     defaultWeight:0.001205, strategy:'Cross above zero = buy, below = sell. Triple EMA momentum kills short-term noise. Use as trend confirmation filter only, not entry.' },
  { id:25, name:'Aroon',                   category:'مؤشرات الزخم',              tier:'B', code:'aroon',                    defaultWeight:0.001205, strategy:'Aroon Up > 70 & Down < 30 = strong uptrend (buy). Reverse = downtrend (sell). Aroon Oscillator > 0 = buy, < 0 = sell.' },
  { id:26, name:'Vortex (VI)',             category:'مؤشرات الزخم',              tier:'B', code:'vortex',                   defaultWeight:0.001205, strategy:'+VI crosses above -VI = buy, below = sell. Similar to DMI but more accurate in choppy markets. Use with ADX — VI for direction, ADX for strength.' },
  { id:27, name:'Coppock Curve',           category:'مؤشرات الزخم',              tier:'C', code:'coppock',                  defaultWeight:0.000602, strategy:'Cross above zero from negative base = classic buy signal. Only for larger frames (4H+). Strongest for swing trading not scalping.' },
  { id:28, name:'Chande Momentum',         category:'مؤشرات الزخم',              tier:'B', code:'chande_momentum',          defaultWeight:0.001205, strategy:'>+50 = overbought, <-50 = oversold. Zero cross = momentum shift. Better than RSI in high-volatility markets (gold, oil). Use divergence for reversals.' },
  // VOLATILITY (29-39)
  { id:29, name:'Bollinger Bands',         category:'مؤشرات التذبذب والتقلب',    tier:'S', code:'bollinger_bands',          defaultWeight:0.00241,  strategy:'Touch lower band + reversal candle = buy, upper + reversal = sell. Golden: Bollinger Squeeze (bands converge) = breakout coming; direction set by band break.' },
  { id:30, name:'ATR',                     category:'مؤشرات التذبذب والتقلب',    tier:'A', code:'atr',                      defaultWeight:0.001807, strategy:'Not a direction indicator — measures volatility. Use for SL (1.5xATR) & TP (3xATR). Rising ATR with level break = strong move coming. Very low ATR = breakout pending.' },
  { id:31, name:'Keltner Channels',        category:'مؤشرات التذبذب والتقلب',    tier:'B', code:'keltner_channels',         defaultWeight:0.001205, strategy:'Upper channel break = strong bullish breakout. Lower break = strong bearish. Stronger than Bollinger in trends (ATR-based). Golden: Keltner inside Bollinger = real Squeeze.' },
  { id:32, name:'FRAMA',                   category:'مؤشرات التذبذب والتقلب',    tier:'B', code:'frama',                    defaultWeight:0.001205, strategy:'Rising slope + price above = strong buy, reverse = sell. Slows in choppy market (reduces false signals), accelerates in clear trend.' },
  { id:33, name:'Donchian Channels',       category:'مؤشرات التذبذب والتقلب',    tier:'B', code:'donchian_channels',        defaultWeight:0.001205, strategy:'Upper channel break (20-bar high) = classic buy (Turtle Trading). Lower break = sell. Enter at 20-period break; exit at opposite 10-period break.' },
  { id:34, name:'Standard Deviation',      category:'مؤشرات التذبذب والتقلب',    tier:'B', code:'standard_deviation',       defaultWeight:0.001205, strategy:'Rising SD with level break = potential strong move. Falling SD = calm & building = breakout prep. Not entry signal — confirms move strength & SL/TP size.' },
  { id:35, name:'Historical Volatility',   category:'مؤشرات التذبذب والتقلب',    tier:'B', code:'historical_volatility',    defaultWeight:0.001205, strategy:'HV very low (20th percentile) = breakout coming with force. When HV hits 30-day low, prepare for big move.' },
  { id:36, name:'Choppiness Index',        category:'مؤشرات التذبذب والتقلب',    tier:'A', code:'choppiness_index',         defaultWeight:0.001807, strategy:'>61.8 = sideways/choppy (avoid trading). <38.2 = strong trending. Golden context filter: do not take other indicator signals unless CI < 50.' },
  { id:37, name:'Chaikin Volatility',      category:'مؤشرات التذبذب والتقلب',    tier:'C', code:'chaikin_volatility',       defaultWeight:0.000602, strategy:'Rising acceleration = volatility expansion (imminent reversal likely). Falling = contraction (calm before storm). Confirms tops/bottoms with Bollinger Bands.' },
  { id:38, name:'Mass Index',              category:'مؤشرات التذبذب والتقلب',    tier:'C', code:'mass_index',               defaultWeight:0.000602, strategy:'Rise above 27 then drop below 26.5 = Reversal Bulge = strong reversal signal. Only larger frames (4H+) for major reversals.' },
  { id:39, name:'Volatility Index',        category:'مؤشرات التذبذب والتقلب',    tier:'C', code:'volatility_index_proxy',   defaultWeight:0.000602, strategy:'Sharp rise = market fear = likely reversal. Long calm = contentment = imminent breakout. Not entry signal — market context only.' },
  // VOLUME (40-51)
  { id:40, name:'Volume',                  category:'مؤشرات الحجم والتدفق',      tier:'A', code:'volume',                   defaultWeight:0.001807, strategy:'Price up + volume up = real buy. Price up + volume down = weak buy (reversal possible). Price down + volume up = strong sell. No move without volume = false move.' },
  { id:41, name:'OBV',                     category:'مؤشرات الحجم والتدفق',      tier:'A', code:'obv',                      defaultWeight:0.001807, strategy:'OBV rising + price rising = real buy trend. OBV falling + price rising = Bearish Divergence = imminent reversal. Best for detecting smart money accumulation/distribution.' },
  { id:42, name:'MFI',                     category:'مؤشرات الحجم والتدفق',      tier:'A', code:'mfi',                      defaultWeight:0.001807, strategy:'Like RSI but with volume. <20 + rising = strong buy, >80 + falling = strong sell. Stronger than RSI in real-volume markets.' },
  { id:43, name:'Accumulation/Distribution',category:'مؤشرات الحجم والتدفق',    tier:'B', code:'accumulation_distribution', defaultWeight:0.001205, strategy:'A/D rising + price rising = real accumulation (buy). A/D falling + price rising = hidden distribution (sell imminent). Always hunt divergence — strongest reversal signal.' },
  { id:44, name:'Chaikin Money Flow',      category:'مؤشرات الحجم والتدفق',      tier:'B', code:'chaikin_money_flow',       defaultWeight:0.001205, strategy:'>+0.20 = strong sustained buy pressure, <-0.20 = strong sell. Zero cross = money shift. Golden filter: do not buy if CMF < 0; do not sell if > 0.' },
  { id:45, name:'Chaikin Oscillator',      category:'مؤشرات الحجم والتدفق',      tier:'B', code:'ad_volume_line',           defaultWeight:0.001205, strategy:'Cross above zero with rising price = backed buy. Below zero = sell. Divergence with price = golden reversal signal.' },
  { id:46, name:'Klinger Oscillator',      category:'مؤشرات الحجم والتدفق',      tier:'B', code:'klinger_oscillator',       defaultWeight:0.001205, strategy:'Klinger line crosses above signal in negative zone = long-term buy. Below in positive zone = sell. Strongest for long-term trends.' },
  { id:47, name:'Force Index',             category:'مؤشرات الحجم والتدفق',      tier:'B', code:'force_index',              defaultWeight:0.001205, strategy:'Strong rising positive = buy pressure. Rising negative = sell pressure. Zero cross = market strength shift. Smooth with EMA(13).' },
  { id:48, name:'Ease of Movement',        category:'مؤشرات الحجم والتدفق',      tier:'B', code:'ease_of_movement',         defaultWeight:0.001205, strategy:'Large positive reads = price rises easily (buy strength). Large negative = drops easily (sell strength). Excellent trend filter.' },
  { id:49, name:'Volume Oscillator',       category:'مؤشرات الحجم والتدفق',      tier:'C', code:'volume_oscillator',        defaultWeight:0.000602, strategy:'>0 = rising volume (current move confirmation), <0 = falling volume (move weakness warning). Not entry signal — trend volume confirmation.' },
  { id:50, name:'PVI / NVI',               category:'مؤشرات الحجم والتدفق',      tier:'C', code:'positive_volume_index',    defaultWeight:0.000602, strategy:'PVI above EMA(255) = smart money buys on up-volume days = buy. NVI above EMA(255) = smart money quietly buys = strong buy.' },
  { id:51, name:'Negative Volume Index',   category:'مؤشرات الحجم والتدفق',      tier:'C', code:'negative_volume_index',    defaultWeight:0.000602, strategy:'NVI above EMA(255) = smart money quietly buys on down-volume days = strong buy. Below = institutional distribution.' },
  // INSTITUTIONAL (52-58)
  { id:52, name:'VWAP (Basic)',            category:'مؤشرات السلوك المؤسسي',     tier:'S', code:'vwap',                     defaultWeight:0.00241,  strategy:'Price above VWAP = buyers in control. Below = sellers in control. Institutions use VWAP as execution reference — bounce from VWAP in trend direction = best re-entry.' },
  { id:53, name:'Anchored VWAP',          category:'مؤشرات السلوك المؤسسي',     tier:'A', code:'anchored_vwap',            defaultWeight:0.001807, strategy:'VWAP anchored from key point (major low/high, news event). Price above = bullish strength since that point, below = bearish. Best for detecting institutional intent.' },
  { id:54, name:'Volume Profile',         category:'مؤشرات السلوك المؤسسي',     tier:'S', code:'volume_profile_vpvr',      defaultWeight:0.00241,  strategy:'POC = highest liquidity zone = price magnet. HVN = strong S/R. LVN = rapid-move zones. Enter from POC bounce in trend direction; target next HVN.' },
  { id:55, name:'VWAP + StdDev Bands',    category:'مؤشرات السلوك المؤسسي',     tier:'S', code:'bb_pct_b_plus_bw',         defaultWeight:0.00241,  strategy:'VWAP +/-1 sigma, +/-2 sigma as R/S. Buy on -2sigma bounce with reversal candle, sell on +2sigma bounce. This is true institutional VWAP.' },
  { id:56, name:'Volume Profile (POC/HVN/LVN)', category:'مؤشرات السلوك المؤسسي', tier:'S', code:'volume_profile_vpfr',  defaultWeight:0.00241,  strategy:'Deeper Volume Profile analysis. Enter on POC rejection in larger trend direction. LVN break = rapid move. Combine with Order Flow = true institutional power.' },
  { id:57, name:'Market Profile (TPO)',   category:'مؤشرات السلوك المؤسسي',     tier:'S', code:'tpo_market_profile',       defaultWeight:0.00241,  strategy:'Value Area (70% activity) = fair value zone. Price exits = strong directional move. Enter on Value Area High/Low rejection.' },
  { id:58, name:'Cumulative Delta',       category:'مؤشرات السلوك المؤسسي',     tier:'S', code:'cumulative_volume_delta',  defaultWeight:0.00241,  strategy:'Delta rising + price rising = real institutional buy. Delta falling + price rising = Absorption (institutions selling to retail) = golden reversal signal.' },
  // SUPPORT/RESISTANCE (59-66)
  { id:59, name:'Fibonacci Retracement',  category:'مؤشرات الدعم والمقاومة',    tier:'S', code:'fibonacci_retracement',   defaultWeight:0.00241,  strategy:'Bounce from 0.382, 0.500, 0.618, 0.786 in larger trend direction = classic entry. Strongest: 0.618 + Order Block + reversal candle = Golden Setup.' },
  { id:60, name:'Pivot Points',           category:'مؤشرات الدعم والمقاومة',    tier:'S', code:'pivot_points_standard',   defaultWeight:0.00241,  strategy:'All types (Standard, Fibonacci, Camarilla, Woodie, DeMark). Bounce from PP, R1, S1 = daily signals. Break R1 = target R2; break S1 = target S2. Camarilla for scalping.' },
  { id:61, name:'Fibonacci Extension',    category:'مؤشرات الدعم والمقاومة',    tier:'A', code:'fibonacci_extension',     defaultWeight:0.001807, strategy:'Target 1.272, 1.414, 1.618, 2.618 for profit-taking after trend. Draw from wave 1 low to wave 1 high, then to wave 2 low — 1.618 is optimal target for wave 3.' },
  { id:62, name:'Trend Lines',            category:'مؤشرات الدعم والمقاومة',    tier:'A', code:'auto_trend_lines_ind',    defaultWeight:0.001807, strategy:'Break uptrend line + retest from break = strong sell. Break downtrend line + retest = buy. Rule: 3 touches = valid line; 5+ = very strong line.' },
  { id:63, name:'Fibonacci Fan',          category:'مؤشرات الدعم والمقاومة',    tier:'B', code:'fibonacci_fan',           defaultWeight:0.001205, strategy:'Fans from pivot point with Fib ratios. Bounce from 0.618 line in trend direction = strong entry. Best for clearly-angled markets.' },
  { id:64, name:'Fibonacci Arcs',         category:'مؤشرات الدعم والمقاومة',    tier:'C', code:'fibonacci_arcs',          defaultWeight:0.000602, strategy:'Fib arcs measure both price & time S/R. Bounce from 0.618 arc = strong signal. Larger frames only (4H+).' },
  { id:65, name:'Fibonacci Time Zones',   category:'مؤشرات الدعم والمقاومة',    tier:'C', code:'fibonacci_time_zones_ind', defaultWeight:0.000602, strategy:'Vertical time lines with Fib ratios from start point. Each line = zone for likely price turn. Good for predicting move timing, not direction.' },
  { id:66, name:'Fibonacci Speed Resistance', category:'مؤشرات الدعم والمقاومة', tier:'C', code:'fibonacci_speed_resistance', defaultWeight:0.000602, strategy:'Fans with 1/3 & 2/3 ratios. Bounce from 2/3 = strong signal.' },
  // INTEGRATED (67-71)
  { id:67, name:'Ichimoku Cloud',         category:'مؤشرات الأنظمة المتكاملة',  tier:'S', code:'ichimoku',                defaultWeight:0.00241,  strategy:'Price above cloud + Tenkan above Kijun + Chikou above past price = complete strong buy. Below + reverse order = strong sell. 5 signals in one indicator.' },
  { id:68, name:'Bollinger %B + Bandwidth', category:'مؤشرات الأنظمة المتكاملة', tier:'A', code:'bollinger_percent_b',   defaultWeight:0.001807, strategy:'%B > 1 = above upper (overbought), < 0 = below lower (oversold). Bandwidth very low = breakout coming (Squeeze). Combine: trend from Bandwidth; signal from %B.' },
  { id:69, name:'McClellan Oscillator',   category:'مؤشرات الأنظمة المتكاملة',  tier:'C', code:'mcclellan_oscillator',   defaultWeight:0.000602, strategy:'Market breadth (stocks only). >+100 = general market buy pressure. <-100 = general sell. Use as general market context filter.' },
  { id:70, name:'Arms Index (TRIN)',      category:'مؤشرات الأنظمة المتكاملة',  tier:'C', code:'arms_index_trin',         defaultWeight:0.000602, strategy:'<1 = general buy pressure, >1 = general sell. Extreme reads (<0.5 or >2) = imminent reversal signal.' },
  { id:71, name:'Advance/Decline Line',  category:'مؤشرات الأنظمة المتكاملة',  tier:'C', code:'advance_decline_line',   defaultWeight:0.000602, strategy:'AD rising + market rising = trend health; divergence = weakness. In Forex: use on currency basket (DXY vs EUR/USD) to read dollar strength.' },
];

type Signal = 'buy' | 'sell' | 'neutral';
interface TfResult { result: Signal; confidence: number; }

export function Table5_Indicators({ symbol, tf: activeTf }: { symbol: string; tf: string }) {
  const [tfData, setTfData] = useState<Record<string, Record<string, TfResult>>>({});
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState<Record<number, boolean>>(() =>
    Object.fromEntries(INDICATORS.map(i => [i.id, true]))
  );
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [collapsedCats, setCollapsedCats] = useState<Set<Category>>(new Set());
  const [search, setSearch] = useState('');

  const fetchAll = useCallback(async () => {
    try {
      const res = await Promise.allSettled(
        TIMEFRAMES.map(tf => api.get(`/analysis/indicators?symbol=${encodeURIComponent(symbol)}&tf=${tf}`))
      );
      const nd: Record<string, Record<string, TfResult>> = {};
      res.forEach((r, i) => {
        const tf = TIMEFRAMES[i];
        nd[tf] = {};
        if (r.status === 'fulfilled') {
          (r.value.data?.indicators ?? []).forEach((row: any) => {
            nd[tf][row.code] = { result: row.result, confidence: row.confidence ?? 0 };
          });
        }
      });
      setTfData(nd);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [symbol]);

  useEffect(() => {
    setLoading(true);
    fetchAll();
    const id = setInterval(fetchAll, 15000);
    return () => clearInterval(id);
  }, [fetchAll]);

  function indResult(ind: IndicatorDef) {
    const sigs: Record<string, Signal> = {};
    let bW = 0, sW = 0, tW = 0;
    TIMEFRAMES.forEach(tf => {
      const row = tfData[tf]?.[ind.code];
      const sig: Signal = row?.result === 'buy' ? 'buy' : row?.result === 'sell' ? 'sell' : 'neutral';
      sigs[tf] = sig;
      const w = TF_WEIGHT[tf] ?? 0;
      const c = (row?.confidence ?? 0) / 100;
      if (sig === 'buy') bW += w * c;
      else if (sig === 'sell') sW += w * c;
      tW += w;
    });
    const net = tW > 0 ? (bW - sW) / tW : 0;
    const result: Signal = net > 0.05 ? 'buy' : net < -0.05 ? 'sell' : 'neutral';
    const confidence = Math.min(100, Math.round(Math.abs(net) * 200));
    return { result, confidence, sigs };
  }

  function summary() {
    let bS = 0, sS = 0;
    INDICATORS.filter(i => enabled[i.id]).forEach(ind => {
      const { result } = indResult(ind);
      if (result === 'buy') bS += ind.defaultWeight;
      else if (result === 'sell') sS += ind.defaultWeight;
    });
    const net = bS - sS;
    const conf = Math.min(100, Math.round((Math.abs(net) / 0.165) * 100));
    const decision: Signal = net > 0.001 ? 'buy' : net < -0.001 ? 'sell' : 'neutral';
    return { bS, sS, net, conf, decision };
  }

  const S = summary();
  const filtered = INDICATORS.filter(i =>
    !search || i.name.toLowerCase().includes(search.toLowerCase()) || i.code.includes(search.toLowerCase())
  );

  function sigBadge(sig: Signal, activeTf_?: string) {
    const isActive = activeTf_ === activeTf;
    return (
      <span className={`inline-block px-1 py-0.5 rounded text-[9px] font-bold transition-all ${
        sig === 'buy'  ? `bg-emerald-500/20 text-emerald-400 ${isActive ? 'ring-1 ring-emerald-400' : ''}` :
        sig === 'sell' ? `bg-red-500/20 text-red-400 ${isActive ? 'ring-1 ring-red-400' : ''}` :
        'bg-slate-500/10 text-slate-500'
      }`}>
        {sig === 'buy' ? '▲' : sig === 'sell' ? '▼' : '◆'}
      </span>
    );
  }

  function decBadge(sig: Signal, label?: { buy: string; sell: string; neutral: string }) {
    const L = label ?? { buy: 'شراء', sell: 'بيع', neutral: 'محايد' };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
        sig === 'buy'  ? 'bg-emerald-500/20 text-emerald-400' :
        sig === 'sell' ? 'bg-red-500/20 text-red-400' :
        'bg-slate-500/10 text-slate-400'
      }`}>
        {sig === 'buy' ? L.buy : sig === 'sell' ? L.sell : L.neutral}
      </span>
    );
  }

  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary">
      {/* ── Header ── */}
      <div className="flex items-center justify-between border-b border-[rgba(201,162,39,0.1)] px-4 py-3">
        <div className="flex items-center gap-3 flex-wrap">
          <h3 className="text-sm font-semibold text-gold">
            5. المؤشرات الفنية <span className="text-muted font-normal text-xs">(10%) — 71 مؤشر</span>
          </h3>
          {decBadge(S.decision, { buy: '▲ شراء', sell: '▼ بيع', neutral: '◆ محايد' })}
          <span className={`text-[11px] font-bold ${S.conf >= 80 ? 'text-yellow-300' : S.conf >= 60 ? 'text-emerald-400' : S.conf >= 30 ? 'text-blue-400' : 'text-slate-400'}`}>
            {S.conf >= 80 ? '👑' : S.conf >= 60 ? '🟢' : S.conf >= 30 ? '🟡' : '⚪'} {S.conf}%
          </span>
          {loading && <span className="text-[10px] text-muted animate-pulse">تحديث…</span>}
        </div>
        <input
          type="text" placeholder="بحث مؤشر…" value={search}
          onChange={e => setSearch(e.target.value)}
          className="text-xs bg-bg-primary border border-[rgba(201,162,39,0.15)] rounded px-2 py-1 text-[var(--text-primary)] placeholder:text-muted w-32 focus:outline-none focus:border-gold"
        />
      </div>

      {/* ── Table ── */}
      <div className="overflow-auto max-h-[72vh] scrollbar-thin">
        <table className="min-w-full text-[11px] border-collapse">
          <thead className="sticky top-0 z-10 bg-bg-secondary border-b border-[rgba(201,162,39,0.12)]">
            <tr>
              <th className="px-2 py-2 text-start text-muted font-medium">#</th>
              <th className="px-2 py-2 text-start text-muted font-medium min-w-[120px]">المؤشر</th>
              <th className="px-2 py-2 text-start text-muted font-medium">الفئة</th>
              <th className="px-2 py-2 text-start text-muted font-medium">Tier</th>
              <th className="px-2 py-2 text-start text-muted font-medium min-w-[140px]">الاستراتيجية والمنطق</th>
              {TIMEFRAMES.map(tf => (
                <th key={tf} className={`px-2 py-2 text-center text-muted font-medium ${tf === activeTf ? 'text-gold' : ''}`}>{tf}</th>
              ))}
              <th className="px-2 py-2 text-start text-muted font-medium whitespace-nowrap">الإشارات</th>
              <th className="px-2 py-2 text-start text-muted font-medium whitespace-nowrap">الوزن</th>
              <th className="px-2 py-2 text-start text-muted font-medium min-w-[80px]">الثقة</th>
              <th className="px-2 py-2 text-start text-muted font-medium">القرار</th>
              <th className="px-2 py-2 text-center text-muted font-medium">تفعيل</th>
            </tr>
          </thead>
          <tbody>
            {CATEGORY_ORDER.map(cat => {
              const catInds = filtered.filter(i => i.category === cat);
              if (catInds.length === 0) return null;
              const collapsed = collapsedCats.has(cat);
              return (
                <>
                  <tr key={`h-${cat}`}
                    className="bg-[rgba(201,162,39,0.06)] cursor-pointer hover:bg-[rgba(201,162,39,0.1)]"
                    onClick={() => setCollapsedCats(p => { const s = new Set(p); s.has(cat) ? s.delete(cat) : s.add(cat); return s; })}
                  >
                    <td colSpan={16} className="px-3 py-1.5">
                      <span className="text-gold font-semibold text-[11px]">
                        {collapsed ? '▶' : '▼'} {cat}
                        <span className="ml-2 text-[10px] text-muted font-normal">({CATEGORY_EN[cat]}) — {catInds.length} مؤشر</span>
                      </span>
                    </td>
                  </tr>
                  {!collapsed && catInds.map(ind => {
                    const { result, confidence, sigs } = indResult(ind);
                    const buys = TIMEFRAMES.filter(tf => sigs[tf] === 'buy').length;
                    const sells = TIMEFRAMES.filter(tf => sigs[tf] === 'sell').length;
                    const neutrals = 6 - buys - sells;
                    const isOn = enabled[ind.id];
                    return (
                      <tr key={ind.id}
                        className={`border-t border-[rgba(201,162,39,0.04)] hover:bg-[rgba(255,255,255,0.015)] transition-colors ${!isOn ? 'opacity-35' : ''}`}
                      >
                        <td className="px-2 py-1.5 text-muted tabular-nums">{ind.id}</td>
                        <td className="px-2 py-1.5 font-medium whitespace-nowrap">{ind.name}</td>
                        <td className="px-2 py-1.5 text-muted text-[10px] whitespace-nowrap">{CATEGORY_EN[ind.category]}</td>
                        <td className="px-2 py-1.5">
                          <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${TIER_COLORS[ind.tier]}`}>{ind.tier}</span>
                        </td>
                        <td className="px-2 py-1.5 max-w-[180px]">
                          <button
                            className="text-left w-full hover:text-gold transition-colors"
                            onClick={() => setExpandedId(expandedId === ind.id ? null : ind.id)}
                          >
                            {expandedId === ind.id
                              ? <span className="text-[10px] leading-tight whitespace-normal block">{ind.strategy}</span>
                              : <span className="text-muted truncate block text-[10px] max-w-[160px]">{ind.strategy.slice(0, 50)}…</span>
                            }
                          </button>
                        </td>
                        {TIMEFRAMES.map(tf => (
                          <td key={tf} className={`px-1 py-1.5 text-center ${tf === activeTf ? 'bg-[rgba(201,162,39,0.04)]' : ''}`}>
                            {sigBadge(sigs[tf] ?? 'neutral', tf)}
                          </td>
                        ))}
                        <td className="px-2 py-1.5 whitespace-nowrap tabular-nums text-[10px]">
                          <span className="text-emerald-400">{buys}B</span>/<span className="text-red-400">{sells}S</span>/<span className="text-slate-400">{neutrals}N</span>
                        </td>
                        <td className="px-2 py-1.5 tabular-nums text-muted text-[10px]">{ind.defaultWeight.toFixed(6)}</td>
                        <td className="px-2 py-1.5">
                          <div className="flex items-center gap-1">
                            <div className="w-10 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${result === 'buy' ? 'bg-emerald-500' : result === 'sell' ? 'bg-red-500' : 'bg-slate-600'}`}
                                style={{ width: `${confidence}%` }} />
                            </div>
                            <span className="text-muted tabular-nums text-[10px]">{confidence}%</span>
                          </div>
                        </td>
                        <td className="px-2 py-1.5">{decBadge(result)}</td>
                        <td className="px-2 py-1.5 text-center">
                          <button
                            onClick={() => setEnabled(p => ({ ...p, [ind.id]: !p[ind.id] }))}
                            className={`w-8 h-4 rounded-full transition-colors relative inline-flex items-center ${isOn ? 'bg-gold' : 'bg-slate-600'}`}
                          >
                            <span className={`absolute w-3 h-3 rounded-full bg-white shadow transition-all ${isOn ? 'right-0.5' : 'left-0.5'}`} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </>
              );
            })}

            {/* ── SUMMARY ROWS ── */}
            <tr className="border-t-2 border-[rgba(201,162,39,0.3)] bg-[rgba(201,162,39,0.04)]">
              <td colSpan={5} className="px-3 py-2 text-gold font-semibold">مجموع أوزان الشراء</td>
              {TIMEFRAMES.map(tf => <td key={tf} />)}
              <td />
              <td className="px-2 py-2 tabular-nums text-emerald-400 font-bold">{S.bS.toFixed(6)}</td>
              <td colSpan={3} />
            </tr>
            <tr className="bg-[rgba(201,162,39,0.04)]">
              <td colSpan={5} className="px-3 py-2 text-gold font-semibold">مجموع أوزان البيع</td>
              {TIMEFRAMES.map(tf => <td key={tf} />)}
              <td />
              <td className="px-2 py-2 tabular-nums text-red-400 font-bold">{S.sS.toFixed(6)}</td>
              <td colSpan={3} />
            </tr>
            <tr className="bg-[rgba(201,162,39,0.04)]">
              <td colSpan={5} className="px-3 py-2 text-gold font-semibold">الصافي (شراء − بيع)</td>
              {TIMEFRAMES.map(tf => <td key={tf} />)}
              <td />
              <td className={`px-2 py-2 tabular-nums font-bold ${S.net >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {S.net >= 0 ? '+' : ''}{S.net.toFixed(6)}
              </td>
              <td colSpan={3} />
            </tr>
            <tr className="bg-[rgba(201,162,39,0.08)] border-t border-[rgba(201,162,39,0.25)]">
              <td colSpan={5} className="px-3 py-2.5 text-gold font-bold text-[12px]">⚡ القرار النهائي</td>
              {TIMEFRAMES.map(tf => <td key={tf} />)}
              <td />
              <td className="px-2 py-2" colSpan={2}>
                {decBadge(S.decision, { buy: '▲ شراء', sell: '▼ بيع', neutral: '◆ محايد' })}
              </td>
              <td className="px-2 py-2">
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                  S.conf >= 80 ? 'bg-yellow-500/20 text-yellow-300' :
                  S.conf >= 60 ? 'bg-emerald-500/20 text-emerald-300' :
                  S.conf >= 30 ? 'bg-blue-500/20 text-blue-300' :
                  'bg-slate-500/20 text-slate-400'
                }`}>
                  {S.conf >= 80 ? '👑 Crown' : S.conf >= 60 ? '🟢 Strong' : S.conf >= 30 ? '🟡 Weak' : '⚪ No Signal'} — {S.conf}%
                </span>
              </td>
              <td />
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── Footer legend ── */}
      <div className="border-t border-[rgba(201,162,39,0.08)] px-4 py-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-muted">
        <span className="text-gold font-medium">أوزان الإطارات:</span>
        {TIMEFRAMES.map(tf => <span key={tf}><span className={tf === activeTf ? 'text-gold' : ''}>{tf}</span>={((TF_WEIGHT[tf] ?? 0) * 100).toFixed(0)}%</span>)}
        <span className="ml-2 text-gold font-medium">|</span>
        <span><span className={TIER_COLORS.S.split(' ')[0]}>Tier S</span>=مؤسسي أساسي</span>
        <span><span className={TIER_COLORS.A.split(' ')[0]}>Tier A</span>=موثوقية عالية</span>
        <span><span className={TIER_COLORS.B.split(' ')[0]}>Tier B</span>=دعم قوي</span>
        <span><span className={TIER_COLORS.C.split(' ')[0]}>Tier C</span>=مترسم مادر</span>
        <span className="ml-2 text-gold font-medium">|</span>
        <span>👑 ≥80% Crown Signal</span>
        <span>🟢 ≥60% Strong Signal</span>
        <span>🟡 ≥30% Weak Signal</span>
        <span>⚪ &lt;30% No Signal</span>
      </div>
    </section>
  );
}
