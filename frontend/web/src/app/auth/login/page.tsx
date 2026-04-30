'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { LionLogo } from '@/components/ui/LionLogo'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [requires2FA, setRequires2FA] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const apiUrl = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8001'
      const resp = await fetch(`${apiUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, totp_code: totpCode || undefined }),
      })
      const data = await resp.json()

      if (resp.status === 200 && data.requires_2fa) {
        setRequires2FA(true)
        setLoading(false)
        return
      }

      if (!resp.ok) {
        setError(data.detail || 'خطأ في تسجيل الدخول')
        setLoading(false)
        return
      }

      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      router.push('/dashboard')
    } catch {
      setError('خطأ في الاتصال بالخادم')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-3">
            <LionLogo size={64} />
          </div>
          <h1 className="text-2xl font-bold text-gold-500">أسد السوق</h1>
          <p className="text-gray-500 text-sm mt-1">نظام التداول بالذكاء الاصطناعي</p>
        </div>

        {/* Card */}
        <div className="card-dark rounded-xl p-6 border border-dark-50">
          <h2 className="text-xl font-bold text-white mb-6 text-center">تسجيل الدخول</h2>

          {error && (
            <div className="bg-bear/10 border border-bear/30 rounded-lg p-3 mb-4 text-bear text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            {!requires2FA ? (
              <>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="example@email.com"
                    className="w-full bg-dark-300 border border-dark-50 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-gold-500 transition-colors"
                    required
                    dir="ltr"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">كلمة المرور</label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-dark-300 border border-dark-50 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-gold-500 transition-colors"
                    required
                    dir="ltr"
                  />
                </div>
                <div className="text-left">
                  <Link href="/auth/forgot-password" className="text-xs text-gold-500 hover:text-gold-400">
                    نسيت كلمة المرور؟
                  </Link>
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm text-gray-400 mb-1">رمز التحقق الثنائي (2FA)</label>
                <input
                  type="text"
                  value={totpCode}
                  onChange={e => setTotpCode(e.target.value)}
                  placeholder="000000"
                  maxLength={6}
                  className="w-full bg-dark-300 border border-dark-50 rounded-lg px-4 py-3 text-white text-center text-xl font-mono tracking-widest focus:outline-none focus:border-gold-500"
                  autoFocus
                  dir="ltr"
                />
                <p className="text-xs text-gray-500 mt-1 text-center">أدخل الرمز من تطبيق المصادقة</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-gold w-full py-3 rounded-lg font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-dark-900 border-t-transparent rounded-full animate-spin" />
                  جاري الدخول...
                </span>
              ) : requires2FA ? 'تأكيد' : 'دخول'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            ليس لديك حساب؟{' '}
            <Link href="/auth/register" className="text-gold-500 hover:text-gold-400 font-medium">
              إنشاء حساب مجاني
            </Link>
          </div>
        </div>

        {/* Demo hint */}
        <p className="text-center text-xs text-gray-700 mt-4">
          للتجربة: demo@marketlion.ai / Demo@1234
        </p>
      </div>
    </div>
  )
}
