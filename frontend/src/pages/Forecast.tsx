import { useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ComposedChart,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, ForecastResponse, ForecastRequest } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Stat } from '../components/ui'
import { SparkleIcon } from '../components/Icons'

const SCENARIO_COLORS = ['#d4b577', '#7aa3ff', '#5fd09b', '#f1c062']

export function ForecastPage() {
  const [mode, setMode] = useState<'single' | 'compare'>('single')
  return (
    <div>
      <PageHeader
        title="Forecast"
        subtitle="Monte Carlo projections, computed deterministically."
        action={
          <div className="hidden lg:flex rounded-xl bg-ink-700/60 p-1 border border-white/5">
            <ModeButton active={mode === 'single'} onClick={() => setMode('single')}>Single</ModeButton>
            <ModeButton active={mode === 'compare'} onClick={() => setMode('compare')}>Compare</ModeButton>
          </div>
        }
      />

      <div className="lg:hidden flex rounded-xl bg-ink-700/60 p-1 border border-white/5 mb-4 w-full">
        <ModeButton active={mode === 'single'} onClick={() => setMode('single')} grow>Single</ModeButton>
        <ModeButton active={mode === 'compare'} onClick={() => setMode('compare')} grow>Compare</ModeButton>
      </div>

      {mode === 'single' ? <SinglePane /> : <ComparePane />}
      <Disclaimer />
    </div>
  )
}

function ModeButton({
  active, onClick, children, grow,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
  grow?: boolean
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium ${grow ? 'flex-1' : ''} ${
        active ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'
      }`}
    >
      {children}
    </button>
  )
}

function SinglePane() {
  const [form, setForm] = useState<ForecastRequest>({
    scenario_name: 'Base case',
    starting_balance_cad: 250000,
    annual_contribution_cad: 24000,
    horizon_years: 25,
    equity_weight: 0.7,
    target_cad: 1500000,
  })
  const [result, setResult] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setResult(await api.forecast(form))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const chart = result
    ? result.results.percentiles.p50.map((_, i) => ({
        year: i,
        p10: result.results.percentiles.p10[i],
        p50: result.results.percentiles.p50[i],
        p90: result.results.percentiles.p90[i],
        target: form.target_cad,
      }))
    : []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <Card>
        <div className="text-sm font-semibold mb-3">Inputs</div>
        <NumField label="Starting balance" v={form.starting_balance_cad}
          onChange={(v) => setForm({ ...form, starting_balance_cad: v })} />
        <NumField label="Annual contribution" v={form.annual_contribution_cad}
          onChange={(v) => setForm({ ...form, annual_contribution_cad: v })} />
        <NumField label="Horizon (years)" v={form.horizon_years}
          onChange={(v) => setForm({ ...form, horizon_years: v })} />
        <Slider label={`Equity weight: ${Math.round(form.equity_weight * 100)}%`}
          v={form.equity_weight} onChange={(v) => setForm({ ...form, equity_weight: v })} />
        <NumField label="Target (optional)" v={form.target_cad ?? 0}
          onChange={(v) => setForm({ ...form, target_cad: v })} />
        <button
          onClick={run}
          disabled={loading}
          className="w-full mt-2 px-3 py-2.5 rounded-xl bg-gold-500 text-ink-950 font-semibold hover:bg-gold-400 disabled:opacity-60"
        >
          {loading ? 'Running…' : 'Run forecast'}
        </button>
        {error && <div className="mt-3 text-xs text-accent-red">{error}</div>}
      </Card>

      <div className="lg:col-span-2 space-y-4">
        {result ? (
          <>
            <div className="grid grid-cols-3 gap-3">
              <Stat label="Median terminal" value={fmt.cad(result.results.median_terminal)} hint="Nominal CAD" />
              <Stat
                label="P10 / P90"
                value={
                  <span className="text-base lg:text-lg num">
                    {fmt.cad(result.results.p10_terminal)}
                    <span className="text-zinc-500"> – </span>
                    {fmt.cad(result.results.p90_terminal)}
                  </span>
                }
                hint="80% range"
              />
              <Stat
                label="Hits target"
                value={result.results.prob_hit_target != null ? fmt.pct(result.results.prob_hit_target) : '—'}
                hint="Probability"
              />
            </div>

            <Card>
              <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">Outcome cone</div>
              <div className="h-72 lg:h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chart} margin={{ top: 4, right: 8, bottom: 8, left: 0 }}>
                    <defs>
                      <linearGradient id="cone" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#7aa3ff" stopOpacity={0.25} />
                        <stop offset="100%" stopColor="#7aa3ff" stopOpacity={0.04} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                    <XAxis dataKey="year" tick={{ fill: '#71717a', fontSize: 11 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: '#71717a', fontSize: 11 }} tickLine={false} axisLine={false}
                      tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(12,13,18,0.95)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: 12, fontSize: 12,
                      }}
                      labelStyle={{ color: '#a1a1aa' }}
                      formatter={(v: number) => fmt.cad(v)}
                    />
                    <Area type="monotone" dataKey="p90" stroke="none" fill="url(#cone)" stackId="1" />
                    <Line type="monotone" dataKey="p50" stroke="#d4b577" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="p10" stroke="#7aa3ff" strokeWidth={1} strokeDasharray="3 3" dot={false} />
                    {form.target_cad ? (
                      <Line type="monotone" dataKey="target" stroke="#5fd09b" strokeWidth={1} strokeDasharray="2 4" dot={false} />
                    ) : null}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {result.narrative?.output_text && (
              <Card>
                <div className="flex items-center gap-2 mb-2">
                  <SparkleIcon className="w-4 h-4 text-gold-400" />
                  <div className="text-[11px] uppercase tracking-wider text-zinc-500">Forecaster narrative</div>
                </div>
                <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
                  {result.narrative.output_text}
                </p>
              </Card>
            )}
          </>
        ) : (
          <Card>
            <div className="py-12 text-center text-sm text-zinc-500">
              Set your inputs and run a forecast to see the cone.
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

function ComparePane() {
  const [scenarios, setScenarios] = useState<ForecastRequest[]>([
    { scenario_name: 'Retire at 60', starting_balance_cad: 250000, annual_contribution_cad: 24000, horizon_years: 25, equity_weight: 0.7, target_cad: 1500000 },
    { scenario_name: 'Retire at 65', starting_balance_cad: 250000, annual_contribution_cad: 24000, horizon_years: 30, equity_weight: 0.7, target_cad: 1500000 },
    { scenario_name: 'Conservative 50/50', starting_balance_cad: 250000, annual_contribution_cad: 24000, horizon_years: 25, equity_weight: 0.5, target_cad: 1500000 },
  ])
  const [results, setResults] = useState<ForecastResponse[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const r = await api.forecastScenarios(scenarios)
      setResults(r.scenarios)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function update(i: number, patch: Partial<ForecastRequest>) {
    setScenarios((s) => s.map((sc, idx) => (idx === i ? { ...sc, ...patch } : sc)))
  }

  // Build a combined chart of medians
  const combined = results
    ? Array.from({ length: Math.max(...results.map((r) => r.results.percentiles.p50.length)) }, (_, i) => {
        const row: Record<string, number | string> = { year: i }
        results.forEach((r, k) => {
          row[`s${k}`] = r.results.percentiles.p50[i] ?? 0
        })
        return row
      })
    : []

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 lg:gap-4">
        {scenarios.map((s, i) => (
          <Card key={i}>
            <div className="flex items-center justify-between mb-2">
              <input
                value={s.scenario_name}
                onChange={(e) => update(i, { scenario_name: e.target.value })}
                className="bg-transparent font-semibold text-sm w-full outline-none"
              />
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: SCENARIO_COLORS[i] }}
              />
            </div>
            <NumField compact label="Start balance" v={s.starting_balance_cad}
              onChange={(v) => update(i, { starting_balance_cad: v })} />
            <NumField compact label="Annual contrib" v={s.annual_contribution_cad}
              onChange={(v) => update(i, { annual_contribution_cad: v })} />
            <NumField compact label="Horizon (yrs)" v={s.horizon_years}
              onChange={(v) => update(i, { horizon_years: v })} />
            <Slider label={`Equity ${Math.round(s.equity_weight * 100)}%`}
              v={s.equity_weight} onChange={(v) => update(i, { equity_weight: v })} />
          </Card>
        ))}
      </div>

      <div className="flex gap-2">
        <button
          onClick={run}
          disabled={loading}
          className="px-3 py-2.5 rounded-xl bg-gold-500 text-ink-950 font-semibold hover:bg-gold-400 disabled:opacity-60"
        >
          {loading ? 'Running…' : 'Run all'}
        </button>
        <button
          onClick={() =>
            setScenarios([
              ...scenarios,
              { scenario_name: `Scenario ${scenarios.length + 1}`, starting_balance_cad: 250000, annual_contribution_cad: 24000, horizon_years: 25, equity_weight: 0.7, target_cad: 1500000 },
            ])
          }
          disabled={scenarios.length >= 4}
          className="px-3 py-2.5 rounded-xl border border-white/10 text-sm hover:bg-white/5 disabled:opacity-50"
        >
          Add scenario
        </button>
      </div>

      {error && <div className="text-xs text-accent-red">{error}</div>}

      {results && (
        <>
          <Card>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">Median terminal balances</div>
            <div className="h-72 lg:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={combined} margin={{ top: 4, right: 8, bottom: 8, left: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="year" tick={{ fill: '#71717a', fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 11 }} tickLine={false} axisLine={false}
                    tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ background: 'rgba(12,13,18,0.95)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, fontSize: 12 }}
                    labelStyle={{ color: '#a1a1aa' }}
                    formatter={(v: number) => fmt.cad(v)}
                  />
                  {results.map((r, k) => (
                    <Line key={k} type="monotone" dataKey={`s${k}`} stroke={SCENARIO_COLORS[k]}
                      name={r.inputs.scenario_name as string} strokeWidth={2} dot={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="!p-0 overflow-hidden">
            <div className="grid grid-cols-12 px-5 py-3 text-[11px] uppercase tracking-wider text-zinc-500 border-b border-white/5">
              <div className="col-span-4">Scenario</div>
              <div className="col-span-2 text-right">Median</div>
              <div className="col-span-2 text-right">P10</div>
              <div className="col-span-2 text-right">P90</div>
              <div className="col-span-2 text-right">Hit target</div>
            </div>
            {results.map((r, i) => (
              <div key={i} className="grid grid-cols-12 px-5 py-3 text-sm items-center border-b border-white/5 last:border-b-0">
                <div className="col-span-4 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: SCENARIO_COLORS[i] }} />
                  <span className="font-medium">{r.inputs.scenario_name as string}</span>
                </div>
                <div className="col-span-2 text-right num">{fmt.cad(r.results.median_terminal)}</div>
                <div className="col-span-2 text-right num text-zinc-400">{fmt.cad(r.results.p10_terminal)}</div>
                <div className="col-span-2 text-right num text-zinc-400">{fmt.cad(r.results.p90_terminal)}</div>
                <div className="col-span-2 text-right num">
                  {r.results.prob_hit_target != null ? fmt.pct(r.results.prob_hit_target) : '—'}
                </div>
              </div>
            ))}
          </Card>
        </>
      )}
    </div>
  )
}

function NumField({
  label, v, onChange, compact,
}: {
  label: string; v: number; onChange: (v: number) => void; compact?: boolean
}) {
  return (
    <label className={`block ${compact ? 'mb-2' : 'mb-3'}`}>
      <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">{label}</div>
      <input
        type="number"
        value={v}
        onChange={(e) => onChange(parseFloat(e.target.value || '0'))}
        className="w-full bg-ink-700/60 border border-white/5 rounded-xl px-3 py-2 text-sm outline-none num"
      />
    </label>
  )
}

function Slider({
  label, v, onChange,
}: {
  label: string; v: number; onChange: (v: number) => void
}) {
  return (
    <label className="block mb-3">
      <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">{label}</div>
      <input
        type="range" min={0} max={1} step={0.05} value={v}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-gold-500"
      />
    </label>
  )
}
