'use client'
interface LionLogoProps { size?: number; className?: string }

export function LionLogo({ size = 80, className = '' }: LionLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`lion-logo ${className}`}
    >
      <defs>
        <radialGradient id="lionGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#f0c040" />
          <stop offset="60%" stopColor="#C9A227" />
          <stop offset="100%" stopColor="#a07818" />
        </radialGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Mane - outer circle petals */}
      {[0,30,60,90,120,150,180,210,240,270,300,330].map((angle, i) => (
        <ellipse
          key={i}
          cx={100 + 62 * Math.cos((angle * Math.PI) / 180)}
          cy={100 + 62 * Math.sin((angle * Math.PI) / 180)}
          rx="18" ry="26"
          transform={`rotate(${angle + 90}, ${100 + 62 * Math.cos((angle * Math.PI) / 180)}, ${100 + 62 * Math.sin((angle * Math.PI) / 180)})`}
          fill="url(#lionGrad)"
          opacity="0.7"
          filter="url(#glow)"
        />
      ))}

      {/* Face circle */}
      <circle cx="100" cy="100" r="52" fill="url(#lionGrad)" filter="url(#glow)" />

      {/* Eyes */}
      <ellipse cx="84" cy="92" rx="7" ry="8" fill="#1a0a00" />
      <ellipse cx="116" cy="92" rx="7" ry="8" fill="#1a0a00" />
      <circle cx="86" cy="90" r="2.5" fill="#fff" opacity="0.8" />
      <circle cx="118" cy="90" r="2.5" fill="#fff" opacity="0.8" />

      {/* Nose */}
      <path d="M96 108 Q100 112 104 108 Q100 105 96 108Z" fill="#8b5000" />

      {/* Mouth */}
      <path d="M92 112 Q100 120 108 112" stroke="#8b5000" strokeWidth="2" fill="none" strokeLinecap="round" />
      <path d="M96 112 Q98 116 100 116" stroke="#8b5000" strokeWidth="1.5" fill="none" />
      <path d="M104 112 Q102 116 100 116" stroke="#8b5000" strokeWidth="1.5" fill="none" />

      {/* Ears */}
      <path d="M62 62 L75 78 L48 80 Z" fill="url(#lionGrad)" />
      <path d="M138 62 L125 78 L152 80 Z" fill="url(#lionGrad)" />
      <path d="M65 65 L74 76 L55 77 Z" fill="#c87020" opacity="0.6" />
      <path d="M135 65 L126 76 L145 77 Z" fill="#c87020" opacity="0.6" />

      {/* Crown accent */}
      <path d="M80 55 L90 45 L100 55 L110 45 L120 55" stroke="#f0c040" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
