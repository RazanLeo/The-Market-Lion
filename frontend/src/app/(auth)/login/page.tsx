'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { login } from '@/lib/api'
import { useAppStore } from '@/lib/store'

const loginSchema = z.object({
  email: z.string().email('البريد الإلكتروني غير صحيح'),
  password: z.string().min(6, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'),
})

type LoginForm = z.infer<typeof loginSchema>

const LionLogo = () => (
  <img
    src="/logo.jpg"
    alt="أسد السوق"
    width={64}
    height={64}
    style={{ borderRadius: '50%', objectFit: 'cover', width: 64, height: 64 }}
  />
)

export default function LoginPage() {
  const router = useRouter()
  const { setUser, setToken } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      const response = await login(data.email, data.password)
      const { token, user } = response.data
      setToken(token)
      setUser(user)
      toast.success('مرحباً بك في أسد السوق! 🦁')
      router.push('/dashboard')
    } catch (error: any) {
      const msg = error?.response?.data?.message || 'خطأ في تسجيل الدخول. تحقق من بياناتك.'
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  // Demo login
  const demoLogin = () => {
    setToken('demo_token_123')
    setUser({
      id: 'demo',
      email: 'demo@marketlion.ai',
      full_name: 'مستخدم تجريبي',
      language: 'ar',
      role: 'user',
      subscription: { plan: 'pro', status: 'active', expires_at: '2025-12-31', features: [] },
      created_at: new Date().toISOString(),
      is_active: true,
    })
    toast.success('تم تسجيل الدخول في الوضع التجريبي')
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4" dir="rtl">
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(201,162,39,0.05) 0%, transparent 70%)' }} />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <LionLogo />
          </div>
          <h1 className="text-3xl font-black text-gold mb-1" style={{ fontFamily: 'Cairo' }}>
            أسد السوق
          </h1>
          <p className="text-gray-400 text-sm">The Market Lion</p>
        </div>

        {/* Card */}
        <div className="bg-dark-800 rounded-2xl p-8 gold-border">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">تسجيل الدخول</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">البريد الإلكتروني</label>
              <div className="relative">
                <input
                  {...register('email')}
                  type="email"
                  placeholder="example@email.com"
                  className="input-dark"
                  dir="ltr"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">✉️</span>
              </div>
              {errors.email && (
                <p className="text-sell text-xs mt-1">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">كلمة المرور</label>
              <div className="relative">
                <input
                  {...register('password')}
                  type="password"
                  placeholder="••••••••"
                  className="input-dark"
                  dir="ltr"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔑</span>
              </div>
              {errors.password && (
                <p className="text-sell text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Forgot Password */}
            <div className="text-left">
              <a href="#" className="text-gold text-xs hover:text-gold-light transition-colors">
                نسيت كلمة المرور؟
              </a>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-gold w-full text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  جاري الدخول...
                </span>
              ) : 'دخول'}
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-dark-600" />
              <span className="text-gray-500 text-xs">أو</span>
              <div className="flex-1 h-px bg-dark-600" />
            </div>

            {/* Demo Login */}
            <button
              type="button"
              onClick={demoLogin}
              className="btn-outline-gold w-full text-sm py-3"
            >
              🎯 جرب النسخة التجريبية
            </button>
          </form>

          {/* Register Link */}
          <p className="text-center text-gray-400 text-sm mt-6">
            ليس لديك حساب؟{' '}
            <Link href="/register" className="text-gold hover:text-gold-light transition-colors font-semibold">
              سجل الآن
            </Link>
          </p>
        </div>

        {/* Back to home */}
        <div className="text-center mt-4">
          <Link href="/" className="text-gray-500 text-sm hover:text-gray-300 transition-colors">
            ← العودة للرئيسية
          </Link>
        </div>
      </div>
    </div>
  )
}
