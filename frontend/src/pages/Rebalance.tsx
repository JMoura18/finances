import { useEffect, useState } from 'react'
import { api, RebalanceSuggestion } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'

const ACTION_PILL: Record<string, string> = {
  add: 'pill-good',
  trim: 'pill-warn',
  deploy: 'pill-good',
  hold: 'pill-neutral',
}

const LABELS: Record<string, string> = {
  equity_us: 'US equity',
  equity_ca: 'CA equity',
  bonds: 'Bonds',
  reit: 'REITs',
  cash: 'Cash',
}

export function RebalancePage() {
  const [items, setItems] = useState<RebalanceSuggestion[] | null>(null)
  useEffect(() => {
    api.rebalance().then(setItems).catch(console.error)
  }, [])

  if (!items) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Rebalance"
        subtitle="Drift from your target allocation, by asset class."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 lg:gap-4">
        {items.map((s) => (
          <Card key={s.asset_class}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">{LABELS[s.asset_class] ?? s.asset_class}</div>
                <div className="text-[11px] text-zinc-500">
                  Target {fmt.pct(s.target_weight)} · Current {fmt.pct(s.current_weight)}
                </div>
              </div>
              <span className={ACTION_PILL[s.action] ?? 'pill-neutral'}>{s.action}</span>
            </div>
            <div className="mt-3 relative h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className="absolute top-0 h-full bg-zinc-500/40"
                style={{
                  left: `${Math.min(s.target_weight * 100, 100)}%`,
                  width: '2px',
                }}
              />
              <div
                className={`h-full ${
                  Math.abs(s.drift) > 0.05 ? 'bg-accent-amber' : 'bg-accent-green'
                }`}
                style={{ width: `${Math.min(s.current_weight * 100, 100)}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between text-[11px] text-zinc-500 num">
              <span>Drift</span>
              <span className={s.drift >= 0 ? 'text-accent-amber' : 'text-accent-blue'}>
                {fmt.signedPct(s.drift)}
              </span>
            </div>
          </Card>
        ))}
      </div>

      <Disclaimer />
    </div>
  )
}
