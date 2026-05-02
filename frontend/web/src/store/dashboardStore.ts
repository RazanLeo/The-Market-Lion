import { create } from 'zustand'

interface DashboardStore {
  selectedSymbol: string
  selectedTimeframe: string
  activeMode: 'auto' | 'semi-auto' | 'manual'
  riskPercent: number
  capital: number
  broker: string
  language: string

  setSelectedSymbol: (symbol: string) => void
  setSelectedTimeframe: (tf: string) => void
  setActiveMode: (mode: 'auto' | 'semi-auto' | 'manual') => void
  setRiskPercent: (pct: number) => void
  setCapital: (capital: number) => void
  setBroker: (broker: string) => void
  setLanguage: (lang: string) => void
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  selectedSymbol: 'XAUUSD',
  selectedTimeframe: 'H1',
  activeMode: 'manual',
  riskPercent: 2,
  capital: 10000,
  broker: 'demo',
  language: 'ar',

  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  setSelectedTimeframe: (tf) => set({ selectedTimeframe: tf }),
  setActiveMode: (mode) => set({ activeMode: mode }),
  setRiskPercent: (pct) => set({ riskPercent: pct }),
  setCapital: (capital) => set({ capital }),
  setBroker: (broker) => set({ broker }),
  setLanguage: (lang) => set({ language: lang }),
}))
