import { useEffect, useState } from 'react'
import { api, Alert } from '../lib/api'
import { Card, PageHeader, Disclaimer, Spinner, Empty } from '../components/ui'

const SEV_PILL: Record<string, string> = {
  info: 'pill-neutral',
  warn: 'pill-warn',
  critical: 'pill-bad',
}

export function AlertsPage() {
  const [items, setItems] = useState<Alert[] | null>(null)

  async function reload() {
    setItems(await api.alerts())
  }

  useEffect(() => {
    reload().catch(console.error)
  }, [])

  async function dismiss(id: string) {
    await api.dismissAlert(id)
    await reload()
  }

  if (!items) return <Spinner />

  const unread = items.filter((a) => !a.is_read)
  const read = items.filter((a) => a.is_read)

  return (
    <div>
      <PageHeader
        title="Alerts"
        subtitle="Observations from the deterministic rule pipeline."
      />

      {unread.length === 0 ? (
        <Empty message="No unread alerts." />
      ) : (
        <div className="space-y-2.5">
          {unread.map((a) => (
            <Card key={a.id} className="!p-4">
              <div className="flex items-start gap-3">
                <span className={`${SEV_PILL[a.severity] ?? 'pill-neutral'} mt-0.5`}>
                  {a.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold">{a.title}</div>
                  <div className="text-xs text-zinc-400 mt-0.5">{a.body}</div>
                  <div className="text-[10px] text-zinc-600 mt-2">
                    {a.category} · {new Date(a.created_at).toLocaleString('en-CA', {
                      dateStyle: 'medium', timeStyle: 'short',
                    })}
                  </div>
                </div>
                <button
                  onClick={() => dismiss(a.id)}
                  className="text-xs text-zinc-400 hover:text-white"
                >
                  Dismiss
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {read.length > 0 && (
        <>
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 mt-8 mb-2">
            Dismissed
          </div>
          <div className="space-y-2">
            {read.map((a) => (
              <div
                key={a.id}
                className="px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5 opacity-60"
              >
                <div className="flex items-start gap-3">
                  <span className={SEV_PILL[a.severity] ?? 'pill-neutral'}>{a.severity}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm">{a.title}</div>
                    <div className="text-xs text-zinc-500">{a.body}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <Disclaimer />
    </div>
  )
}
