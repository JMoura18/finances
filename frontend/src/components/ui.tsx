import { ReactNode } from 'react'

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="flex items-end justify-between gap-4 mb-5 lg:mb-7">
      <div>
        <h1 className="text-xl lg:text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-zinc-400 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Card({
  children,
  className = '',
  padded = true,
}: {
  children: ReactNode
  className?: string
  padded?: boolean
}) {
  return (
    <div className={`glass ${padded ? 'p-4 lg:p-5' : ''} ${className}`}>{children}</div>
  )
}

export function Stat({
  label,
  value,
  hint,
  trend,
}: {
  label: string
  value: ReactNode
  hint?: string
  trend?: 'up' | 'down' | 'flat'
}) {
  const color =
    trend === 'up' ? 'text-accent-green' : trend === 'down' ? 'text-accent-red' : 'text-zinc-400'
  return (
    <Card>
      <div className="text-[11px] uppercase tracking-wider text-zinc-500">{label}</div>
      <div className="mt-1 text-2xl lg:text-3xl font-semibold num">{value}</div>
      {hint && <div className={`mt-1 text-xs ${color}`}>{hint}</div>}
    </Card>
  )
}

export function Disclaimer() {
  return (
    <div className="mt-8 text-[11px] leading-relaxed text-zinc-500 px-1">
      Cofre provides portfolio analytics and information. It does not provide
      investment, tax, or legal advice. Consult a licensed advisor before making
      investment decisions.
    </div>
  )
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12 text-zinc-500 text-sm">
      Loading…
    </div>
  )
}

export function Empty({ message }: { message: string }) {
  return (
    <Card>
      <div className="py-8 text-center text-sm text-zinc-500">{message}</div>
    </Card>
  )
}
