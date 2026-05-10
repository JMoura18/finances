import { useEffect, useState } from 'react'
import { api, RebalancePlan } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner, Empty } from '../components/ui'

const ACTION_PILL: Record<string, string> = {
  add: 'pill-good',
  trim: 'pill-warn',
  deploy: 'pill-good',
  deploy_cash: 'pill-good',
  hold: 'pill-neutral',
}

const LABELS: Record<string, string> = {
  equity_us: 'US equity',
  equity_ca: 'CA equity',
  bonds: 'Bonds',
  fixed_income: 'Bonds',
  reit: 'REITs',
  cash: 'Cash',
  etf: 'Diversified ETFs',
  equity: 'Single-name equity',
}

export function RebalancePage() {
  const [data, setData] = useState<RebalancePlan | null>(null)

  useEffect(() => {
    api.rebalancePlan().then(setData).catch(console.error)
  }, [])

  if (!data) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Rebalance"
        subtitle="Tax-aware actions to bring drift back to target."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 lg:gap-4">
        {data.suggestions.map((s) => (
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
                style={{ left: `${Math.min(s.target_weight * 100, 100)}%`, width: '2px' }}
              />
              <div
                className={`h-full ${Math.abs(s.drift) > 0.05 ? 'bg-accent-amber' : 'bg-accent-green'}`}
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

      <div className="text-[11px] uppercase tracking-wider text-zinc-500 mt-8 mb-2">
        Suggested actions
      </div>

      {data.actions.length === 0 ? (
        <Empty message="No actions needed right now." />
      ) : (
        <Card className="!p-0 overflow-hidden">
          {data.actions.map((a, i) => (
            <div
              key={i}
              className={`px-4 lg:px-5 py-4 ${
                i !== data.actions.length - 1 ? 'border-b border-white/5' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className={ACTION_PILL[a.action] ?? 'pill-neutral'}>{a.action.replace('_', ' ')}</span>
                    {a.symbol && <span className="text-sm font-semibold">{a.symbol}</span>}
                  </div>
                  <div className="text-[11px] text-zinc-400 mt-1.5">{a.reason}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-semibold num">{fmt.cad(a.amount_cad)}</div>
                  <div className="text-[10px] text-zinc-500 num">CAD</div>
                </div>
              </div>
            </div>
          ))}
        </Card>
      )}

      <Disclaimer />
    </div>
  )
}
