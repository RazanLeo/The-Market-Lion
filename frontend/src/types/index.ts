export interface User {
  id: string
  email: string
  full_name: string
  language: 'ar' | 'en'
  role: 'user' | 'admin'
  subscription: Subscription | null
  created_at: string
  is_active: boolean
}

export interface Subscription {
  plan: 'free' | 'pro' | 'vip'
  status: 'active' | 'expired' | 'cancelled'
  expires_at: string | null
  features: string[]
}

export interface PriceData {
  symbol: string
  price: number
  bid: number
  ask: number
  change: number
  change_pct: number
  high: number
  low: number
  volume?: number
  timestamp: string
}

export interface Candle {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

export interface TechnicalIndicator {
  name: string
  value: number | string
  signal: 'buy' | 'sell' | 'neutral'
  strength?: number
}

export interface TimeframeAnalysis {
  timeframe: string
  signal: 'buy' | 'sell' | 'neutral'
  confidence: number
  indicators: TechnicalIndicator[]
}

export interface AnalysisSchool {
  name: string
  name_ar: string
  signal: 'buy' | 'sell' | 'neutral'
  confidence: number
  description?: string
}

export interface TechnicalAnalysis {
  symbol: string
  timeframe: string
  overall_signal: 'buy' | 'sell' | 'neutral'
  confidence: number
  confluence_score: number
  timeframes: Record<string, TimeframeAnalysis>
  indicators: TechnicalIndicator[]
  schools: AnalysisSchool[]
  entry_price?: number
  stop_loss?: number
  targets?: number[]
  timestamp: string
}

export interface EconomicEvent {
  id: string
  title: string
  title_ar?: string
  country: string
  currency: string
  impact: 'high' | 'medium' | 'low'
  datetime: string
  actual?: string | null
  forecast?: string | null
  previous?: string | null
  gold_impact?: 'bullish' | 'bearish' | 'neutral'
}

export interface NewsItem {
  id: string
  title: string
  title_ar?: string
  summary?: string
  source: string
  url: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  published_at: string
}

export interface FundamentalAnalysis {
  symbol: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  events: EconomicEvent[]
  news: NewsItem[]
  timestamp: string
}

export interface OrderBlock {
  id: string
  level: number
  direction: 'bullish' | 'bearish'
  strength: number
  timeframe: string
  created_at: string
  is_active: boolean
}

export interface FVGap {
  id: string
  top: number
  bottom: number
  direction: 'bullish' | 'bearish'
  timeframe: string
  filled: boolean
}

export interface LiquidityData {
  symbol: string
  order_blocks: OrderBlock[]
  fv_gaps: FVGap[]
  killzone: {
    name: string
    name_ar: string
    active: boolean
    start: string
    end: string
  }
  smart_money_bias: 'bullish' | 'bearish' | 'neutral'
  whale_alerts: WhaleAlert[]
}

export interface WhaleAlert {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  volume: number
  price: number
  timestamp: string
}

export interface Signal {
  id: string
  symbol: string
  direction: 'buy' | 'sell'
  timeframe: string
  entry_price: number
  stop_loss: number
  targets: number[]
  confidence: number
  status: 'active' | 'hit' | 'stopped' | 'expired'
  created_at: string
}

export interface Trade {
  id: string
  symbol: string
  direction: 'buy' | 'sell'
  open_price: number
  close_price?: number
  volume: number
  profit?: number
  profit_pct?: number
  status: 'open' | 'closed'
  opened_at: string
  closed_at?: string
}

export interface Position {
  id: string
  symbol: string
  direction: 'buy' | 'sell'
  volume: number
  open_price: number
  current_price: number
  profit: number
  profit_pct: number
  opened_at: string
}

export interface AccountInfo {
  balance: number
  equity: number
  margin: number
  free_margin: number
  margin_level: number
  daily_pnl: number
  daily_pnl_pct: number
  win_rate: number
  total_trades: number
  active_positions: number
}

export interface BotStatus {
  is_running: boolean
  mode: 'auto' | 'semi-auto' | 'manual'
  active_symbols: string[]
  last_signal?: Signal | null
  last_trade?: Trade | null
  total_signals_today: number
  total_trades_today: number
  started_at?: string | null
}

export interface Notification {
  id: string
  type: 'signal' | 'trade' | 'alert' | 'system'
  message: string
  message_ar?: string
  read: boolean
  created_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface SubscriptionPlan {
  id: string
  name: string
  name_ar: string
  price: number
  currency: string
  period: 'monthly' | 'yearly'
  features: string[]
  features_ar: string[]
  is_popular?: boolean
}

export interface AdminStats {
  total_users: number
  active_subscriptions: number
  total_revenue: number
  active_bots: number
  total_trades_today: number
  win_rate: number
  new_users_today: number
}
