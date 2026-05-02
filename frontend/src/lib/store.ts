import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  User,
  PriceData,
  TechnicalAnalysis,
  BotStatus,
  Notification,
  Signal,
  Position,
  AccountInfo,
} from '@/types'

interface AppState {
  // Auth
  user: User | null
  token: string | null
  isAuthenticated: boolean

  // UI
  language: 'ar' | 'en'
  sidebarOpen: boolean

  // Market
  selectedSymbol: string
  selectedTimeframe: string
  prices: Record<string, PriceData>

  // Analysis
  technicalAnalysis: Record<string, TechnicalAnalysis>

  // Bot
  botStatus: BotStatus

  // Trading
  positions: Position[]
  accountInfo: AccountInfo | null

  // Notifications
  notifications: Notification[]
  unreadCount: number

  // Actions - Auth
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void

  // Actions - UI
  setLanguage: (lang: 'ar' | 'en') => void
  toggleSidebar: () => void

  // Actions - Market
  setSymbol: (symbol: string) => void
  setTimeframe: (timeframe: string) => void
  updatePrice: (symbol: string, data: PriceData) => void
  setPrices: (prices: Record<string, PriceData>) => void

  // Actions - Analysis
  setTechnical: (symbol: string, data: TechnicalAnalysis) => void

  // Actions - Bot
  setBotStatus: (status: BotStatus) => void

  // Actions - Trading
  setPositions: (positions: Position[]) => void
  setAccountInfo: (info: AccountInfo) => void

  // Actions - Notifications
  addNotification: (notification: Notification) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
}

const defaultBotStatus: BotStatus = {
  is_running: false,
  mode: 'manual',
  active_symbols: ['XAUUSD'],
  last_signal: null,
  last_trade: null,
  total_signals_today: 0,
  total_trades_today: 0,
  started_at: null,
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      language: 'ar',
      sidebarOpen: true,
      selectedSymbol: 'XAUUSD',
      selectedTimeframe: 'H1',
      prices: {},
      technicalAnalysis: {},
      botStatus: defaultBotStatus,
      positions: [],
      accountInfo: null,
      notifications: [],
      unreadCount: 0,

      // Auth actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => {
        set({ token })
        if (typeof window !== 'undefined') {
          if (token) {
            localStorage.setItem('token', token)
          } else {
            localStorage.removeItem('token')
          }
        }
      },
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          positions: [],
          accountInfo: null,
        })
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token')
        }
      },

      // UI actions
      setLanguage: (language) => set({ language }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      // Market actions
      setSymbol: (selectedSymbol) => set({ selectedSymbol }),
      setTimeframe: (selectedTimeframe) => set({ selectedTimeframe }),
      updatePrice: (symbol, data) =>
        set((state) => ({
          prices: { ...state.prices, [symbol]: data },
        })),
      setPrices: (prices) => set({ prices }),

      // Analysis actions
      setTechnical: (symbol, data) =>
        set((state) => ({
          technicalAnalysis: { ...state.technicalAnalysis, [symbol]: data },
        })),

      // Bot actions
      setBotStatus: (botStatus) => set({ botStatus }),

      // Trading actions
      setPositions: (positions) => set({ positions }),
      setAccountInfo: (accountInfo) => set({ accountInfo }),

      // Notification actions
      addNotification: (notification) =>
        set((state) => ({
          notifications: [notification, ...state.notifications].slice(0, 50),
          unreadCount: state.unreadCount + 1,
        })),
      markNotificationRead: (id) =>
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n
          ),
          unreadCount: Math.max(0, state.unreadCount - 1),
        })),
      clearNotifications: () => set({ notifications: [], unreadCount: 0 }),
    }),
    {
      name: 'market-lion-store',
      partialize: (state) => ({
        token: state.token,
        language: state.language,
        selectedSymbol: state.selectedSymbol,
        selectedTimeframe: state.selectedTimeframe,
      }),
    }
  )
)
