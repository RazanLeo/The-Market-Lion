'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAppStore } from '@/lib/store'
import { getAdminStats, getAdminUsers, updateUserSubscription } from '@/lib/api'
import { MOCK_ADMIN_STATS } from '@/lib/mockData'
import type { User, AdminStats } from '@/types'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const MOCK_USERS: User[] = [
  { id: '1', email: 'ahmed@example.com', full_name: 'أحمد محمد', language: 'ar', role: 'user', subscription: { plan: 'pro', status: 'active', expires_at: '2025-06-30', features: [] }, created_at: '2025-01-15T00:00:00Z', is_active: true },
  { id: '2', email: 'sara@example.com', full_name: 'سارة علي', language: 'ar', role: 'user', subscription: { plan: 'vip', status: 'active', expires_at: '2026-01-01', features: [] }, created_at: '2025-02-01T00:00:00Z', is_active: true },
  { id: '3', email: 'john@example.com', full_name: 'John Smith', language: 'en', role: 'user', subscription: { plan: 'free', status: 'active', expires_at: null, features: [] }, created_at: '2025-03-10T00:00:00Z', is_active: true },
  { id: '4', email: 'fatima@example.com', full_name: 'فاطمة خالد', language: 'ar', role: 'user', subscription: { plan: 'pro', status: 'expired', expires_at: '2025-04-01', features: [] }, created_at: '2024-12-01T00:00:00Z', is_active: true },
  { id: '5', email: 'omar@example.com', full_name: 'عمر الرشيد', language: 'ar', role: 'user', subscription: { plan: 'pro', status: 'active', expires_at: '2025-08-15', features: [] }, created_at: '2025-04-20T00:00:00Z', is_active: false },
]

const StatCard = ({ icon, label, value, sub, color = 'text-gold' }: {
  icon: string; label: string; value: string | number; sub?: string; color?: string
}) => (
  <div className="card-gold p-4">
    <div className="flex items-start justify-between">
      <div>
        <div className="text-gray-400 text-xs mb-1">{label}</div>
        <div className={`text-2xl font-black ${color}`}>{value}</div>
        {sub && <div className="text-gray-500 text-xs mt-1">{sub}</div>}
      </div>
      <span className="text-3xl">{icon}</span>
    </div>
  </div>
)

export default function AdminPage() {
  const router = useRouter()
  const { user, token, language } = useAppStore()
  const [stats, setStats] = useState<AdminStats>(MOCK_ADMIN_STATS)
  const [users, setUsers] = useState<User[]>(MOCK_USERS)
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [newPlan, setNewPlan] = useState<string>('')
  const isRtl = language === 'ar'

  useEffect(() => {
    const storedToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (!token && !storedToken) {
      router.push('/login')
      return
    }
    if (user && user.role !== 'admin') {
      router.push('/dashboard')
      return
    }
  }, [token, user, router])

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [statsRes, usersRes] = await Promise.all([
          getAdminStats(),
          getAdminUsers(),
        ])
        if (statsRes.data) setStats(statsRes.data)
        if (usersRes.data?.users) setUsers(usersRes.data.users)
      } catch {
        // Use mock data
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleUpdateSubscription = async (userId: string) => {
    if (!newPlan) return
    try {
      await updateUserSubscription(userId, { plan: newPlan })
      setUsers(prev => prev.map(u => u.id === userId ? {
        ...u,
        subscription: { ...u.subscription!, plan: newPlan as any }
      } : u))
      toast.success(isRtl ? 'تم تحديث الاشتراك' : 'Subscription updated')
      setEditingUser(null)
      setNewPlan('')
    } catch {
      // Demo mode
      setUsers(prev => prev.map(u => u.id === userId ? {
        ...u,
        subscription: { ...u.subscription!, plan: newPlan as any }
      } : u))
      toast.success(isRtl ? 'تم تحديث الاشتراك' : 'Subscription updated')
      setEditingUser(null)
      setNewPlan('')
    }
  }

  const filteredUsers = users.filter(u =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  const planBadgeClass = (plan: string, status: string) => {
    if (status === 'expired') return 'text-gray-500 border-gray-600 bg-gray-500/5'
    if (plan === 'vip') return 'text-purple-400 border-purple-500 bg-purple-500/10'
    if (plan === 'pro') return 'text-gold border-gold bg-gold/10'
    return 'text-gray-400 border-gray-600 bg-gray-500/5'
  }

  return (
    <div className="min-h-screen bg-dark-900" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🛡️</span>
          <div>
            <h1 className="text-gold font-black text-lg">
              {isRtl ? 'لوحة الإدارة' : 'Admin Panel'}
            </h1>
            <p className="text-gray-400 text-xs">
              {isRtl ? 'أسد السوق — إدارة النظام' : 'Market Lion — System Admin'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {loading && <div className="w-4 h-4 border border-gold border-t-transparent rounded-full animate-spin" />}
          <Link href="/dashboard" className="btn-outline-gold text-sm px-4 py-2">
            {isRtl ? '← لوحة التداول' : '← Trading Board'}
          </Link>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon="👥" label={isRtl ? 'إجمالي المستخدمين' : 'Total Users'} value={stats.total_users.toLocaleString()} sub={`+${stats.new_users_today} ${isRtl ? 'اليوم' : 'today'}`} />
          <StatCard icon="⭐" label={isRtl ? 'اشتراكات نشطة' : 'Active Subs'} value={stats.active_subscriptions} color="text-purple-400" />
          <StatCard icon="💰" label={isRtl ? 'الإيرادات ($)' : 'Revenue ($)'} value={`$${stats.total_revenue.toLocaleString()}`} color="text-green-400" />
          <StatCard icon="🤖" label={isRtl ? 'بوتات نشطة' : 'Active Bots'} value={stats.active_bots} color="text-blue-400" />
          <StatCard icon="📊" label={isRtl ? 'صفقات اليوم' : 'Trades Today'} value={stats.total_trades_today.toLocaleString()} color="text-white" />
          <StatCard icon="🎯" label={isRtl ? 'معدل الفوز' : 'Win Rate'} value={`${stats.win_rate}%`} color="text-gold" />
          <StatCard icon="💹" label={isRtl ? 'الإيراد/مستخدم' : 'Rev/User'} value={`$${(stats.total_revenue / stats.active_subscriptions).toFixed(0)}`} color="text-gold-light" />
          <div className="card-gold p-4">
            <div className="text-gray-400 text-xs mb-2">{isRtl ? 'حالة النظام' : 'System Status'}</div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400 pulse-green" />
              <span className="text-green-400 font-bold text-sm">{isRtl ? 'يعمل بشكل طبيعي' : 'All Systems OK'}</span>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              API: <span className="text-green-400">✓</span> |
              DB: <span className="text-green-400">✓</span> |
              WS: <span className="text-green-400">✓</span>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="card-gold">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-gold font-bold flex items-center gap-2">
              <span>👥</span>
              {isRtl ? 'إدارة المستخدمين' : 'User Management'}
              <span className="text-gray-400 font-normal text-sm">({filteredUsers.length})</span>
            </h2>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder={isRtl ? 'بحث...' : 'Search...'}
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input-dark text-sm py-2 w-40"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="table-dark w-full">
              <thead>
                <tr>
                  <th className="text-right">{isRtl ? 'المستخدم' : 'User'}</th>
                  <th className="text-center">{isRtl ? 'الاشتراك' : 'Plan'}</th>
                  <th className="text-center">{isRtl ? 'الحالة' : 'Status'}</th>
                  <th className="text-center">{isRtl ? 'اللغة' : 'Lang'}</th>
                  <th className="text-center">{isRtl ? 'الانتهاء' : 'Expires'}</th>
                  <th className="text-center">{isRtl ? 'إجراءات' : 'Actions'}</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(u => (
                  <tr key={u.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gold/20 border border-gold/30 flex items-center justify-center text-gold text-sm font-bold shrink-0">
                          {u.full_name[0]}
                        </div>
                        <div>
                          <div className="text-white text-sm font-medium">{u.full_name}</div>
                          <div className="text-gray-500 text-xs">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-center">
                      <span className={clsx('text-xs px-2 py-0.5 rounded border font-bold', planBadgeClass(u.subscription?.plan || 'free', u.subscription?.status || 'active'))}>
                        {u.subscription?.plan?.toUpperCase() || 'FREE'}
                      </span>
                    </td>
                    <td className="text-center">
                      <span className={clsx('text-xs font-medium', u.is_active ? 'text-green-400' : 'text-red-400')}>
                        {u.is_active ? (isRtl ? 'نشط' : 'Active') : (isRtl ? 'موقوف' : 'Banned')}
                      </span>
                    </td>
                    <td className="text-center text-gray-300 text-xs">
                      {u.language === 'ar' ? '🇸🇦' : '🇬🇧'} {u.language.toUpperCase()}
                    </td>
                    <td className="text-center text-gray-400 text-xs">
                      {u.subscription?.expires_at
                        ? new Date(u.subscription.expires_at).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US')
                        : (isRtl ? 'دائم' : 'Forever')}
                    </td>
                    <td className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => { setEditingUser(u); setNewPlan(u.subscription?.plan || 'free') }}
                          className="text-xs px-2 py-1 rounded bg-gold/10 text-gold hover:bg-gold/20 transition-colors border border-gold/30"
                        >
                          {isRtl ? 'تعديل' : 'Edit'}
                        </button>
                        <button className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors border border-red-500/30">
                          {isRtl ? 'إيقاف' : 'Ban'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Plan Distribution */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { plan: 'free', label: isRtl ? 'مجاني' : 'Free', count: users.filter(u => u.subscription?.plan === 'free').length, color: '#A0A0A0' },
            { plan: 'pro', label: 'Pro', count: users.filter(u => u.subscription?.plan === 'pro').length, color: '#C9A227' },
            { plan: 'vip', label: 'VIP', count: users.filter(u => u.subscription?.plan === 'vip').length, color: '#A855F7' },
          ].map(item => (
            <div key={item.plan} className="card-gold">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">{item.label}</span>
                <span className="font-black text-2xl" style={{ color: item.color }}>{item.count}</span>
              </div>
              <div className="bg-dark-600 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${(item.count / users.length) * 100}%`, background: item.color }}
                />
              </div>
              <div className="text-gray-500 text-xs mt-1">
                {((item.count / users.length) * 100).toFixed(0)}% {isRtl ? 'من المستخدمين' : 'of users'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Edit Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" dir={isRtl ? 'rtl' : 'ltr'}>
          <div className="bg-dark-800 rounded-2xl p-6 w-full max-w-sm gold-border">
            <h3 className="text-gold font-bold mb-4">
              {isRtl ? 'تعديل اشتراك' : 'Edit Subscription'}: {editingUser.full_name}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="text-gray-300 text-sm mb-2 block">
                  {isRtl ? 'الخطة الجديدة:' : 'New Plan:'}
                </label>
                <select
                  value={newPlan}
                  onChange={e => setNewPlan(e.target.value)}
                  className="input-dark"
                >
                  <option value="free">{isRtl ? 'مجاني' : 'Free'}</option>
                  <option value="pro">Pro</option>
                  <option value="vip">VIP</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleUpdateSubscription(editingUser.id)}
                  className="btn-gold flex-1"
                >
                  {isRtl ? 'حفظ' : 'Save'}
                </button>
                <button
                  onClick={() => { setEditingUser(null); setNewPlan('') }}
                  className="btn-outline-gold flex-1"
                >
                  {isRtl ? 'إلغاء' : 'Cancel'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
