'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { LionLogo } from '@/components/ui/LionLogo'

const COUNTRIES = [
  { code: 'SA', name: 'المملكة العربية السعودية' },
  { code: 'AE', name: 'الإمارات العربية المتحدة' },
  { code: 'KW', name: 'الكويت' },
  { code: 'QA', name: 'قطر' },
  { code: 'BH', name: 'البحرين' },
  { code: 'OM', name: 'عُمان' },
  { code: 'EG', name: 'مصر' },
  { code: 'JO', name: 'الأردن' },
  { code: 'US', name: 'الولايات المتحدة' },
  { code: 'GB', name: 'المملكة المتحدة' },
  { code: 'OTHER', name: 'دولة أخرى' },
]

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    email: '', username: '', password: '', confirmPassword: '',
    full_name: '', phone: '', country: 'SA', referral_code: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState(1)

  const update = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.password !== form.confirmPassword) {
      setError('كلمات المرور غير متطابقة')
      return
    }
    setLoading(true)
    setError('')
    try {
      const apiUrl = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8001'
      const resp = await fetch(`${apiUrl}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: form.email, username: form.username, password: form.password,
          full_name: form.full_name, phone: form.phone, country: form.country,
          referral_code: form.referral_code || undefined,
        }),
      })
      const data = await resp.json()
      if (!resp.ok) {
        setError(data.detail || 'خطأ في إنشاء الحساب')
        return
      }
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      router.push('/dashboard')
    } catch {
      setError('خطأ في الاتصال')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-3"><LionLogo size={64} /></div>
          <h1 className="text-2xl font-bold text-gold-500">أسد السوق</h1>
          <p className="text-gray-500 text-sm mt-1">ابدأ مجاناً — لا بطاقة بنكية مطلوبة</p>
        </div>

        <div className="card-dark rounded-xl p-6 border border-dark-50">
          <h2 className="text-xl font-bold text-white mb-6 text-center">إنشاء حساب جديد</h2>

          {error && (
            <div className="bg-bear/10 border border-bear/30 rounded-lg p-3 mb-4 text-bear text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">الاسم الكامل</label>
                <input value={form.full_name} onChange={e => update('full_name', e.target.value)}
                  placeholder="محمد أحمد" className="input-dark w-full" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">اسم المستخدم *</label>
                <input value={form.username} onChange={e => update('username', e.target.value)}
                  placeholder="trader123" className="input-dark w-full" dir="ltr" required />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">البريد الإلكتروني *</label>
              <input type="email" value={form.email} onChange={e => update('email', e.target.value)}
                placeholder="you@example.com" className="input-dark w-full" dir="ltr" required />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">رقم الجوال</label>
              <input value={form.phone} onChange={e => update('phone', e.target.value)}
                placeholder="+966501234567" className="input-dark w-full" dir="ltr" />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">الدولة *</label>
              <select value={form.country} onChange={e => update('country', e.target.value)}
                className="input-dark w-full">
                {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">كلمة المرور *</label>
                <input type="password" value={form.password} onChange={e => update('password', e.target.value)}
                  placeholder="••••••••" className="input-dark w-full" dir="ltr" required />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">تأكيد المرور *</label>
                <input type="password" value={form.confirmPassword} onChange={e => update('confirmPassword', e.target.value)}
                  placeholder="••••••••" className="input-dark w-full" dir="ltr" required />
              </div>
            </div>
            <p className="text-xs text-gray-600">يجب أن تحتوي على 8+ أحرف، حرف كبير ورقم</p>

            <div>
              <label className="block text-xs text-gray-400 mb-1">كود الإحالة (اختياري)</label>
              <input value={form.referral_code} onChange={e => update('referral_code', e.target.value)}
                placeholder="LION1234" className="input-dark w-full" dir="ltr" />
            </div>

            <p className="text-xs text-gray-600 text-center">
              بالتسجيل توافق على{' '}
              <Link href="/terms" className="text-gold-500">الشروط والأحكام</Link>
              {' '}و{' '}
              <Link href="/privacy" className="text-gold-500">سياسة الخصوصية</Link>
            </p>

            <button type="submit" disabled={loading}
              className="btn-gold w-full py-3 rounded-lg font-bold text-sm disabled:opacity-50">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-dark-900 border-t-transparent rounded-full animate-spin" />
                  جاري الإنشاء...
                </span>
              ) : 'إنشاء حساب مجاني 🦁'}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-500">
            لديك حساب؟{' '}
            <Link href="/auth/login" className="text-gold-500 hover:text-gold-400 font-medium">سجل دخولك</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
