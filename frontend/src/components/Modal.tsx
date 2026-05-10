import { ReactNode, useEffect } from 'react'

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-end lg:place-items-center bg-black/60 backdrop-blur-sm">
      <div
        className="w-full lg:max-w-md glass rounded-t-2xl lg:rounded-2xl p-5 max-h-[92vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="w-8 h-8 rounded-full bg-white/5 grid place-items-center text-zinc-400 hover:text-white"
          >
            ×
          </button>
        </div>
        {children}
      </div>
      <div className="absolute inset-0 -z-10" onClick={onClose} />
    </div>
  )
}

export function FormField({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <label className="block mb-3">
      <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">{label}</div>
      {children}
    </label>
  )
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full bg-ink-700/60 border border-white/5 rounded-xl px-3 py-2 text-sm outline-none focus:border-gold-500/40 ${
        props.className ?? ''
      }`}
    />
  )
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`w-full bg-ink-700/60 border border-white/5 rounded-xl px-3 py-2 text-sm outline-none focus:border-gold-500/40 ${
        props.className ?? ''
      }`}
    />
  )
}

export function PrimaryButton(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`px-3 py-2 rounded-xl bg-gold-500 text-ink-950 font-semibold hover:bg-gold-400 disabled:opacity-60 ${
        props.className ?? ''
      }`}
    />
  )
}
