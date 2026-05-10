import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, RiskResponse } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner, Stat } from '../components/ui'
import { SparkleIcon } from '../components/Icons'

const SHOCK_LABELS: Record<string, string> = {
  covid_2020: 'COVID 2020',
  gfc_2008: 'GFC 2008',
  rates_2022: 'Rates 2022',
}

export function RiskPage() {
  const [risk, setRisk] = useState<RiskResponse | null>(null)
  const [narrative, setNarrative] = useState<string | null>(null)
  const [narrLoading, setNarrLoading] = useState(false)

  useEffect(() => {
    api.risk().then(setRisk).catch(console.error)
  }, [])

  async function loadNarrative() {
    setNarrLoading(true)
    try {
      const r = await api.riskNarrative()
      setNarrative(r.output_text)
    } catch (e) {
      setNarrative(`Error: ${(e as Error).message}`)
    } finally {
      setNarrLoading(false)
    }
  }

  if (!risk) return <Spinner />

  const stressData = Object.entries(risk.stress_results).map(([k, v]) => ({
    name: SHOCK_LABELS[k] ?? k,
    value: v * 100,
  }))

  const sectorData = Object.entries(risk.concentration.by_sector)
    .map(([k, v]) => ({ name: k, value: v as number }))
    .sort((a, b) => b.value - a.value)

  const regimeColor =
    risk.regime === 'crisis'
      ? 'text-accent-red'
      : risk.regime === 'elevated'
      ? 'text-accent-amber'
      : 'text-accent-green'

  return (
    <div>
      <PageHeader title="Risk" subtitle="Concentration, regime, and historical stress." />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
        <Stat
          label="Composite score"
          value={
            <span>
              {risk.score.toFixed(0)}
              <span className="text-base text-zinc-500"> / 100</span>
            </span>
          }
          hint={risk.regime}
          trend={risk.score > 70 ? 'down' : risk.score > 40 ? 'flat' : 'up'}
        />
        <Stat
          label="HHI"
          value={risk.concentration.hhi.toFixed(2)}
          hint="0 = diversified · 1 = single-name"
        />
        <Stat
          label="Regime"
          value={<span className={regimeColor}>{risk.regime}</span>}
          hint="Updated weekly"
        />
        <Stat
          label="Worst stress"
          value={
            <span className="text-accent-red">
              {(Math.min(...Object.values(risk.stress_results)) * 100).toFixed(1)}%
            </span>
          }
          hint="Modeled drawdown"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <Card>
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">
            Stress tests
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stressData} margin={{ top: 4, right: 8, bottom: 8, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#a1a1aa', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fill: '#71717a', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(12,13,18,0.95)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                  formatter={(v: number) => `${v.toFixed(1)}%`}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {stressData.map((d, i) => (
                    <Cell key={i} fill={d.value < -25 ? '#ef6b73' : '#f1c062'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">
            Sector concentration
          </div>
          <div className="space-y-2.5">
            {sectorData.map((s) => (
              <div key={s.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="capitalize">{s.name.replace('_', ' ')}</span>
                  <span className="num text-zinc-400">{fmt.pct(s.value)}</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-gold-400 to-gold-600"
                    style={{ width: `${Math.min(s.value * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-4">
        <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">
          Top weights
        </div>
        <div className="space-y-2">
          {risk.concentration.top.map((t) => (
            <div
              key={t.symbol}
              className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.025] border border-white/5"
            >
              <span className="text-sm font-medium">{t.symbol}</span>
              <span className="num text-sm text-zinc-300">{fmt.pct(t.weight)}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="mt-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <SparkleIcon className="w-4 h-4 text-gold-400" />
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">
              Risk Analyst narrative
            </div>
          </div>
          {!narrative && (
            <button
              onClick={loadNarrative}
              disabled={narrLoading}
              className="text-xs px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-50"
            >
              {narrLoading ? 'Generating…' : 'Generate'}
            </button>
          )}
        </div>
        {narrative ? (
          <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
            {narrative}
          </p>
        ) : (
          <p className="text-sm text-zinc-500">
            Click Generate to interpret these numbers in plain language.
          </p>
        )}
      </Card>

      <Disclaimer />
    </div>
  )
}
