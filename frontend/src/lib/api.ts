import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Market data
export const getPrice = (symbol: string) => api.get(`/market/price/${symbol}`)
export const getAllPrices = () => api.get('/market/prices/all')
export const getCandles = (symbol: string, timeframe: string) =>
  api.get(`/market/candles/${symbol}?timeframe=${timeframe}`)

// Technical Analysis
export const getTechnicalAnalysis = (symbol: string, timeframe: string) =>
  api.get(`/technical/analysis/${symbol}?timeframe=${timeframe}`)
export const getAllTimeframesAnalysis = (symbol: string) =>
  api.get(`/technical/analysis/${symbol}/all`)

// Fundamental Analysis
export const getFundamentalAnalysis = (symbol: string) =>
  api.get(`/fundamental/analysis/${symbol}`)
export const getNews = () => api.get('/fundamental/news')
export const getCalendar = () => api.get('/fundamental/calendar')

// Liquidity
export const getLiquidityData = (symbol: string) =>
  api.get(`/liquidity/analysis/${symbol}`)

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/login', { email, password })
export const register = (data: {
  email: string
  password: string
  full_name: string
  language: string
}) => api.post('/auth/register', data)
export const getMe = () => api.get('/auth/me')
export const logout = () => api.post('/auth/logout')

// Bot
export const getBotStatus = () => api.get('/bot/status')
export const startBot = (config: {
  mode: string
  symbols: string[]
}) => api.post('/bot/start', config)
export const stopBot = () => api.post('/bot/stop')
export const getSignals = () => api.get('/bot/signals')
export const getSignalHistory = () => api.get('/bot/signals/history')

// Broker
export const connectBroker = (data: {
  broker: string
  account_id: string
  password: string
  server: string
}) => api.post('/broker/connect', data)
export const disconnectBroker = () => api.post('/broker/disconnect')
export const getPositions = () => api.get('/broker/positions')
export const getAccountInfo = () => api.get('/broker/account')
export const getAccount = () => api.get('/broker/account')
export const placeOrder = (order: {
  symbol: string
  direction: string
  volume: number
  price?: number
  stop_loss?: number
  take_profit?: number
}) => api.post('/broker/order', order)
export const closePosition = (positionId: string) =>
  api.delete(`/broker/positions/${positionId}`)

// Trades
export const getTrades = (params?: {
  status?: string
  limit?: number
  offset?: number
}) => api.get('/trades', { params })

// Subscription
export const getPlans = () => api.get('/subscription/plans')
export const subscribe = (data: {
  plan_id: string
  payment_method: string
}) => api.post('/subscription/subscribe', data)
export const cancelSubscription = () => api.delete('/subscription/cancel')

// AI Chat
export const chatWithAI = (message: string, history: Array<{
  role: string
  content: string
}>) => api.post('/ai/chat', { message, history })

// Admin
export const getAdminStats = () => api.get('/admin/stats')
export const getAdminUsers = (params?: {
  page?: number
  limit?: number
  search?: string
}) => api.get('/admin/users', { params })
export const updateUserSubscription = (userId: string, data: {
  plan: string
  expires_at?: string
}) => api.put(`/admin/users/${userId}/subscription`, data)

export default api
