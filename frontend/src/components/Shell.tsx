import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  WalletIcon,
  PieIcon,
  ListIcon,
  TrendingIcon,
  ShieldIcon,
  TaxIcon,
  ScaleIcon,
} from './Icons'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: HomeIcon },
  { to: '/accounts', label: 'Accounts', icon: WalletIcon },
  { to: '/holdings', label: 'Holdings', icon: PieIcon },
  { to: '/transactions', label: 'Activity', icon: ListIcon },
  { to: '/forecast', label: 'Forecast', icon: TrendingIcon },
  { to: '/risk', label: 'Risk', icon: ShieldIcon },
  { to: '/tax', label: 'Tax', icon: TaxIcon },
  { to: '/rebalance', label: 'Rebalance', icon: ScaleIcon },
]

const PRIMARY_MOBILE = ['/dashboard', '/accounts', '/holdings', '/forecast', '/risk']

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-white/5 bg-ink-900/60 backdrop-blur-xl">
        <div className="px-6 py-6">
          <Brand />
        </div>
        <nav className="px-3 flex-1 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-colors ${
                  isActive
                    ? 'bg-white/5 text-white shadow-glow'
                    : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-[10px] leading-relaxed text-zinc-500 border-t border-white/5">
          Cofre is for informational purposes only. Not investment, tax, or legal advice.
        </div>
      </aside>

      {/* Main column */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Mobile top bar */}
        <header className="lg:hidden sticky top-0 z-20 bg-ink-950/80 backdrop-blur-xl border-b border-white/5">
          <div className="flex items-center justify-between px-4 py-3">
            <Brand compact />
            <button
              aria-label="Account menu"
              className="w-9 h-9 rounded-full bg-white/5 border border-white/10 grid place-items-center text-xs font-semibold"
            >
              JM
            </button>
          </div>
        </header>

        <main className="flex-1 px-4 lg:px-10 py-5 lg:py-8 pb-24 lg:pb-10 max-w-[1400px] w-full mx-auto">
          {children}
        </main>

        {/* Mobile bottom tab bar */}
        <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-ink-900/85 backdrop-blur-xl border-t border-white/5 pb-[env(safe-area-inset-bottom)]">
          <div className="grid grid-cols-5">
            {NAV.filter((n) => PRIMARY_MOBILE.includes(n.to)).map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center gap-1 py-2.5 text-[10px] ${
                    isActive ? 'text-gold-400' : 'text-zinc-500'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
      </div>
    </div>
  )
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gold-400 to-gold-600 grid place-items-center text-ink-950 font-bold">
        C
      </div>
      <div className={compact ? 'leading-tight' : ''}>
        <div className="text-base font-semibold tracking-tight">Cofre</div>
        {!compact && <div className="text-[11px] text-zinc-500 -mt-0.5">Portfolio command center</div>}
      </div>
    </div>
  )
}
