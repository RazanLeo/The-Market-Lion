'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { Logo } from '../brand/Logo';
import { LanguageSwitcher } from './LanguageSwitcher';
import { Bell, ChevronDown, LayoutDashboard, ListChecks, Briefcase, FileText, MessageSquare, Settings, LogIn, UserPlus } from 'lucide-react';

export function Header() {
  const t = useTranslations('nav');
  return (
    <header className="sticky top-0 z-40 w-full border-b border-[rgba(201,162,39,0.15)] bg-[rgba(10,10,10,0.85)] backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 md:px-6">
        <Link href="/" className="glow-on-hover rounded-md"><Logo /></Link>

        <nav className="hidden md:flex items-center gap-1">
          <NavItem href="/dashboard" icon={<LayoutDashboard size={16} />} label={t('dashboard')} />
          <NavItem href="/trades"    icon={<ListChecks size={16} />}      label={t('trades')} />
          <NavItem href="/portfolio" icon={<Briefcase size={16} />}       label={t('portfolio')} />
          <NavItem href="/reports"   icon={<FileText size={16} />}        label={t('reports')} />
          <NavItem href="/chat"      icon={<MessageSquare size={16} />}   label={t('chat')} />
          <NavItem href="/settings"  icon={<Settings size={16} />}        label={t('settings')} />
        </nav>

        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <button className="rounded-md p-2 text-gold hover:bg-[rgba(201,162,39,0.08)]"><Bell size={18}/></button>
          <Link href="/auth/login"  className="hidden md:inline-flex items-center gap-1 rounded-md border border-gold px-3 py-1.5 text-gold text-sm hover:shadow-glow-soft"><LogIn size={14}/> {t('login')}</Link>
          <Link href="/auth/register" className="hidden md:inline-flex items-center gap-1 rounded-md bg-gold px-3 py-1.5 text-bg-primary text-sm font-semibold hover:shadow-glow"><UserPlus size={14}/> {t('register')}</Link>
        </div>
      </div>
    </header>
  );
}

function NavItem({ href, label, icon }: { href: string; label: string; icon: React.ReactNode }) {
  return (
    <Link href={href} className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-muted hover:bg-[rgba(201,162,39,0.06)] hover:text-gold">
      {icon} <span>{label}</span>
    </Link>
  );
}
