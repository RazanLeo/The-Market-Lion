'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAppStore } from '@/lib/store'
import clsx from 'clsx'

const navItems = [
  { href: '/dashboard', icon: '📊', label: 'لوحة التحكم', labelEn: 'Dashboard' },
  { href: '/dashboard/technical', icon: '📈', label: 'التحليل الفني', labelEn: 'Technical' },
  { href: '/dashboard/fundamental', icon: '📰', label: 'التحليل الأساسي', labelEn: 'Fundamental' },
  { href: '/dashboard/bot', icon: '🤖', label: 'روبوت التداول', labelEn: 'Trading Bot' },
  { href: '/dashboard/trades', icon: '💹', label: 'الصفقات', labelEn: 'Trades' },
  { href: '/dashboard/subscription', icon: '⭐', label: 'الاشتراك', labelEn: 'Subscription' },
  { href: '/dashboard/settings', icon: '⚙️', label: 'الإعدادات', labelEn: 'Settings' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, botStatus, language, user } = useAppStore()
  const isRtl = language === 'ar'

  if (!sidebarOpen) return null

  const planColors: Record<string, string> = {
    free: 'text-gray-400',
    pro: 'text-gold',
    vip: 'text-purple-400',
  }

  const planLabels: Record<string, { ar: string; en: string }> = {
    free: { ar: 'مجاني', en: 'Free' },
    pro: { ar: 'برو', en: 'Pro' },
    vip: { ar: 'VIP', en: 'VIP' },
  }

  const plan = user?.subscription?.plan || 'free'

  return (
    <aside className="fixed top-14 bottom-0 right-0 w-56 bg-dark-800 border-l border-dark-700 z-30 flex flex-col overflow-y-auto">
      {/* Navigation */}
      <nav className="p-3 flex-1">
        <div className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== '/dashboard' && pathname?.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm',
                  isActive
                    ? 'bg-gold/10 text-gold border border-gold/20'
                    : 'text-gray-400 hover:text-white hover:bg-dark-700'
                )}
              >
                <span className="text-base">{item.icon}</span>
                <span className="font-medium">{isRtl ? item.label : item.labelEn}</span>
                {isActive && (
                  <span className="mr-auto w-1.5 h-1.5 rounded-full bg-gold" />
                )}
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Bot Status Card */}
      <div className="p-3 border-t border-dark-700">
        <div className={clsx(
          'rounded-xl p-4',
          botStatus.is_running
            ? 'bg-green-500/5 border border-green-500/20'
            : 'bg-dark-700 border border-dark-600'
        )}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">{isRtl ? 'البوت' : 'Bot'}</span>
            <div className="flex items-center gap-1.5">
              <div className={clsx(
                'w-2 h-2 rounded-full',
                botStatus.is_running ? 'bg-green-400 pulse-green' : 'bg-gray-600'
              )} />
              <span className={clsx(
                'text-xs font-bold',
                botStatus.is_running ? 'text-green-400' : 'text-gray-500'
              )}>
                {isRtl
                  ? (botStatus.is_running ? 'يعمل' : 'متوقف')
                  : (botStatus.is_running ? 'Running' : 'Stopped')}
              </span>
            </div>
          </div>

          {botStatus.is_running && (
            <>
              <div className="text-xs text-gray-400 mb-1">
                {isRtl ? 'الوضع:' : 'Mode:'}{' '}
                <span className="text-gold">
                  {botStatus.mode === 'auto' ? (isRtl ? 'تلقائي' : 'Auto') :
                   botStatus.mode === 'semi-auto' ? (isRtl ? 'شبه تلقائي' : 'Semi') :
                   (isRtl ? 'يدوي' : 'Manual')}
                </span>
              </div>
              <div className="text-xs text-gray-400">
                {isRtl ? 'إشارات اليوم:' : 'Today:'}{' '}
                <span className="text-white">{botStatus.total_signals_today}</span>
              </div>
              {botStatus.last_signal && (
                <div className="mt-2 pt-2 border-t border-dark-600">
                  <div className="text-xs text-gray-400 mb-1">{isRtl ? 'آخر إشارة:' : 'Last Signal:'}</div>
                  <div className={clsx(
                    'text-xs font-bold px-2 py-1 rounded text-center',
                    botStatus.last_signal.direction === 'buy' ? 'badge-buy' : 'badge-sell'
                  )}>
                    {botStatus.last_signal.direction === 'buy'
                      ? (isRtl ? 'شراء' : 'BUY')
                      : (isRtl ? 'بيع' : 'SELL')}{' '}
                    {botStatus.last_signal.symbol}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Subscription Badge */}
      <div className="p-3 border-t border-dark-700">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs text-gray-500">{isRtl ? 'اشتراكك' : 'Plan'}</span>
          <span className={clsx('text-xs font-bold px-2 py-0.5 rounded border', {
            'text-gray-400 border-gray-600': plan === 'free',
            'text-gold border-gold': plan === 'pro',
            'text-purple-400 border-purple-500': plan === 'vip',
          })}>
            {isRtl ? planLabels[plan]?.ar : planLabels[plan]?.en}
          </span>
        </div>
        {plan === 'free' && (
          <Link href="/dashboard/subscription"
            className="btn-gold w-full text-xs py-2 text-center block mt-2">
            {isRtl ? 'ترقية الاشتراك ⬆️' : 'Upgrade ⬆️'}
          </Link>
        )}
      </div>
    </aside>
  )
}
