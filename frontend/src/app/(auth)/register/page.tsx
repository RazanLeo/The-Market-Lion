'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { register as registerUser } from '@/lib/api'
import { useAppStore } from '@/lib/store'

const registerSchema = z.object({
  full_name: z.string().min(2, 'الاسم يجب أن يكون حرفين على الأقل'),
  email: z.string().email('البريد الإلكتروني غير صحيح'),
  password: z.string().min(8, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل'),
  confirm_password: z.string(),
  language: z.enum(['ar', 'en']),
  agree_terms: z.boolean().refine(val => val === true, 'يجب الموافقة على الشروط والأحكام'),
}).refine(data => data.password === data.confirm_password, {
  message: 'كلمتا المرور غير متطابقتين',
  path: ['confirm_password'],
})

type RegisterForm = z.infer<typeof registerSchema>

const LionLogo = () => (
  <img
    src="/logo.jpg"
    alt="أسد السوق"
    width={64}
    height={64}
    style={{ borderRadius: '50%', objectFit: 'cover', width: 64, height: 64 }}
  />
)

export default function RegisterPage() {
  const router = useRouter()
  const { setUser, setToken, setLanguage } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { language: 'ar', agree_terms: false },
  })

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      const response = await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        language: data.language,
      })
      const { token, user } = response.data
      setToken(token)
      setUser(user)
      setLanguage(data.language as 'ar' | 'en')
      toast.success('مرحباً! تم إنشاء حسابك بنجاح 🦁')
      router.push('/dashboard')
    } catch (error: any) {
      const msg = error?.response?.data?.message || 'حدث خطأ أثناء إنشاء الحساب. حاول مرة أخرى.'
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4 py-8" dir="rtl">
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
          <p className="text-gray-400 text-sm">انضم إلى أقوى مجتمع تداول</p>
        </div>

        {/* Card */}
        <div className="bg-dark-800 rounded-2xl p-8 gold-border">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">إنشاء حساب جديد</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full Name */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">الاسم الكامل</label>
              <input
                {...register('full_name')}
                type="text"
                placeholder="محمد أحمد"
                className="input-dark"
              />
              {errors.full_name && <p className="text-sell text-xs mt-1">{errors.full_name.message}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">البريد الإلكتروني</label>
              <input
                {...register('email')}
                type="email"
                placeholder="example@email.com"
                className="input-dark"
                dir="ltr"
              />
              {errors.email && <p className="text-sell text-xs mt-1">{errors.email.message}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">كلمة المرور</label>
              <input
                {...register('password')}
                type="password"
                placeholder="8 أحرف على الأقل"
                className="input-dark"
                dir="ltr"
              />
              {errors.password && <p className="text-sell text-xs mt-1">{errors.password.message}</p>}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">تأكيد كلمة المرور</label>
              <input
                {...register('confirm_password')}
                type="password"
                placeholder="أعد كتابة كلمة المرور"
                className="input-dark"
                dir="ltr"
              />
              {errors.confirm_password && <p className="text-sell text-xs mt-1">{errors.confirm_password.message}</p>}
            </div>

            {/* Language */}
            <div>
              <label className="block text-gray-300 text-sm mb-2">اللغة المفضلة</label>
              <select
                {...register('language')}
                className="input-dark"
              >
                <option value="ar">🇸🇦 العربية</option>
                <option value="en">🇬🇧 English</option>
              </select>
            </div>

            {/* Terms */}
            <div className="flex items-start gap-3">
              <input
                {...register('agree_terms')}
                type="checkbox"
                id="terms"
                className="mt-1 accent-gold w-4 h-4"
              />
              <label htmlFor="terms" className="text-gray-400 text-sm cursor-pointer">
                أوافق على{' '}
                <a href="#" className="text-gold hover:text-gold-light">الشروط والأحكام</a>
                {' '}و{' '}
                <a href="#" className="text-gold hover:text-gold-light">سياسة الخصوصية</a>
              </label>
            </div>
            {errors.agree_terms && <p className="text-sell text-xs">{errors.agree_terms.message}</p>}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-gold w-full text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  جاري الإنشاء...
                </span>
              ) : 'إنشاء الحساب'}
            </button>
          </form>

          {/* Login Link */}
          <p className="text-center text-gray-400 text-sm mt-6">
            لديك حساب بالفعل؟{' '}
            <Link href="/login" className="text-gold hover:text-gold-light transition-colors font-semibold">
              تسجيل الدخول
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
