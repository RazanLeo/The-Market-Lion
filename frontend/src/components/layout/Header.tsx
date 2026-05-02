'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAppStore } from '@/lib/store'
import { SYMBOLS } from '@/lib/mockData'
import clsx from 'clsx'

const LionLogo = () => (
  <img
    src="/logo.jpg"
    alt="أسد السوق"
    width={36}
    height={36}
    style={{ borderRadius: '50%', objectFit: 'cover', width: 36, height: 36 }}
  />
)

export default function Header() {
  const router = useRouter()
  const { user, selectedSymbol, setSymbol, prices, language, setLanguage, botStatus, logout, toggleSidebar } = useAppStore()
  const [symbolOpen, setSymbolOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const symbolRef = useRef<HTMLDivElement>(null)
  const userRef = useRef<HTMLDivElement>(null)

  const currentPrice = prices[selectedSymbol]
  const currentSymbol = SYMBOLS.find(s => s.value === selectedSymbol)
  const isRtl = language === 'ar'

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (symbolRef.current && !symbolRef.current.contains(e.target as Node)) setSymbolOpen(false)
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const priceChange = currentPrice ? currentPrice.change_pct : 0
  const isPositive = priceChange >= 0

  const subscriptionColors: Record<string, string> = {
    free: 'text-gray-400 border-gray-600',
    pro: 'text-gold border-gold',
    vip: 'text-purple-400 border-purple-500',
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-dark-800/95 backdrop-blur-sm border-b-2 border-gold/30">
      <div className="flex items-center h-14 px-4 gap-3">
        {/* Sidebar Toggle */}
        <button
          onClick={toggleSidebar}
          className="text-gray-400 hover:text-gold transition-colors p-1 rounded"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2 shrink-0">
          <LionLogo />
          <div className="hidden sm:block">
            <div className="text-gold font-black text-sm leading-none" style={{ fontFamily: 'Cairo' }}>
              {isRtl ? 'أسد السوق' : 'Market Lion'}
            </div>
            <div className="text-gray-500 text-xs">AI Trading Bot</div>
          </div>
        </Link>

        {/* Symbol Selector */}
        <div ref={symbolRef} className="relative">
          <button
            onClick={() => setSymbolOpen(!symbolOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-700 border border-dark-600 hover:border-gold/40 transition-colors"
          >
            <span className="text-white font-bold text-sm">
              {isRtl ? currentSymbol?.labelAr : currentSymbol?.label}
            </span>
            <svg className={`w-3 h-3 text-gray-400 transition-transform ${symbolOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {symbolOpen && (
            <div className="absolute top-full mt-1 right-0 bg-dark-700 border border-dark-600 rounded-lg shadow-xl z-50 min-w-[160px]">
              {SYMBOLS.map(sym => (
                <button
                  key={sym.value}
                  onClick={() => { setSymbol(sym.value); setSymbolOpen(false) }}
                  className={clsx(
                    'w-full text-right px-4 py-2 text-sm hover:bg-dark-600 transition-colors flex items-center justify-between',
                    selectedSymbol === sym.value ? 'text-gold' : 'text-gray-300'
                  )}
                >
                  <span>{isRtl ? sym.labelAr : sym.label}</span>
                  {selectedSymbol === sym.value && <span className="text-gold text-xs">✓</span>}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Price Display */}
        {currentPrice ? (
          <div className="flex items-center gap-3">
            <span className="text-white font-bold text-lg">
              {currentPrice.price.toFixed(selectedSymbol === 'EURUSD' || selectedSymbol === 'GBPUSD' ? 4 : 2)}
            </span>
            <span className={clsx(
              'text-sm font-semibold px-2 py-0.5 rounded',
              isPositive ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'
            )}>
              {isPositive ? '+' : ''}{currentPrice.change_pct.toFixed(2)}%
            </span>
          </div>
        ) : (
          <div className="skeleton h-6 w-24 rounded" />
        )}

        {/* Bot Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-700 border border-dark-600">
          <div className={clsx(
            'w-2 h-2 rounded-full',
            botStatus.is_running ? 'bg-green-400 pulse-green' : 'bg-gray-600'
          )} />
          <span className="text-xs text-gray-300">
            {isRtl
              ? (botStatus.is_running ? 'البوت يعمل' : 'البوت متوقف')
              : (botStatus.is_running ? 'Bot Running' : 'Bot Stopped')}
          </span>
          {botStatus.is_running && (
            <span className="text-xs text-gray-500">
              {botStatus.mode === 'auto' ? (isRtl ? 'تلقائي' : 'Auto') :
               botStatus.mode === 'semi-auto' ? (isRtl ? 'شبه تلقائي' : 'Semi-Auto') :
               (isRtl ? 'يدوي' : 'Manual')}
            </span>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Language Toggle */}
        <button
          onClick={() => setLanguage(language === 'ar' ? 'en' : 'ar')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-700 border border-dark-600 hover:border-gold/40 transition-colors text-sm"
        >
          <span>{language === 'ar' ? '🇸🇦' : '🇬🇧'}</span>
          <span className="text-gray-300">{language === 'ar' ? 'AR' : 'EN'}</span>
        </button>

        {/* User Menu */}
        <div ref={userRef} className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-dark-700 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-gold/20 border border-gold/30 flex items-center justify-center text-gold font-bold text-sm">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-white text-xs font-semibold leading-none">{user?.full_name || 'User'}</div>
              <div className={clsx('text-xs mt-0.5 border rounded px-1 text-center', subscriptionColors[user?.subscription?.plan || 'free'])}>
                {user?.subscription?.plan?.toUpperCase() || 'FREE'}
              </div>
            </div>
            <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {userMenuOpen && (
            <div className="absolute top-full mt-1 left-0 bg-dark-700 border border-dark-600 rounded-xl shadow-xl z-50 min-w-[180px] py-2">
              <div className="px-4 py-2 border-b border-dark-600">
                <div className="text-white text-sm font-semibold">{user?.full_name}</div>
                <div className="text-gray-400 text-xs">{user?.email}</div>
              </div>
              <Link href="/dashboard" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-gold hover:bg-dark-600 transition-colors" onClick={() => setUserMenuOpen(false)}>
                <span>📊</span> {isRtl ? 'لوحة التحكم' : 'Dashboard'}
              </Link>
              <Link href="/dashboard/settings" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-gold hover:bg-dark-600 transition-colors" onClick={() => setUserMenuOpen(false)}>
                <span>⚙️</span> {isRtl ? 'الإعدادات' : 'Settings'}
              </Link>
              {user?.role === 'admin' && (
                <Link href="/admin" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-gold hover:bg-dark-600 transition-colors" onClick={() => setUserMenuOpen(false)}>
                  <span>🛡️</span> {isRtl ? 'إدارة النظام' : 'Admin'}
                </Link>
              )}
              <div className="border-t border-dark-600 mt-1 pt-1">
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-400 hover:bg-dark-600 transition-colors"
                >
                  <span>🚪</span> {isRtl ? 'تسجيل الخروج' : 'Logout'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
