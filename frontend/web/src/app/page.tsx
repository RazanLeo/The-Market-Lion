'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { LionLogo } from '@/components/ui/LionLogo'

export default function LandingPage() {
  const router = useRouter()
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    setIsLoaded(true)
  }, [])

  return (
    <main className="min-h-screen bg-dark-300 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: 'linear-gradient(rgba(201,162,39,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(201,162,39,0.1) 1px, transparent 1px)',
          backgroundSize: '50px 50px',
        }}
      />

      {/* Radial glow */}
      <div className="absolute inset-0 bg-gradient-radial from-gold-500/5 via-transparent to-transparent" />

      {isLoaded && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="flex flex-col items-center gap-8 z-10 px-4 text-center"
        >
          {/* Lion Logo */}
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <LionLogo size={160} />
          </motion.div>

          {/* Brand */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <h1 className="text-6xl font-black text-gold-gradient mb-2">أسد السوق</h1>
            <h2 className="text-2xl font-bold text-gray-300 tracking-wider">The Market Lion</h2>
            <p className="text-sm text-gray-500 mt-2 font-mono">Razan AI Trading Bot & Indicator — v2.0</p>
          </motion.div>

          {/* Tagline */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-lg text-gray-400 max-w-xl leading-relaxed"
          >
            أقوى بوت ومؤشر تداول في العالم — يدمج 65+ مدرسة تحليل فني مع تحليل أساسي لحظي
            وذكاء اصطناعي متطور لتحقيق نسبة نجاح تاريخية استثنائية
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="flex gap-4 flex-wrap justify-center"
          >
            <button
              onClick={() => router.push('/dashboard')}
              className="btn-gold text-lg px-8 py-4 rounded-xl"
            >
              🦁 ابدأ التداول الآن
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="btn-outline-gold text-lg px-8 py-4 rounded-xl"
            >
              تجربة مجانية 7 أيام
            </button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1 }}
            className="grid grid-cols-3 gap-8 mt-4"
          >
            {[
              { label: 'مدرسة تحليل', value: '65+' },
              { label: 'بروكر مدعوم', value: '10+' },
              { label: 'لغة', value: '14' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-black text-gold-500">{stat.value}</div>
                <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      )}
    </main>
  )
}
