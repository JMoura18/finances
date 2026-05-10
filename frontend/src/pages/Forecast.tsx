import { useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, ForecastResponse } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Stat } from '../components/ui'
import { SparkleIcon } from '../components/Icons'

export function ForecastPage() {
  const [form, setForm] = useState({
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
      const res = await api.forecast({
        scenario_name: 'Base case',
        ...form,
      })
      setResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const chartData = result
    ? result.results.percentiles.p50.map((_, i) => ({
        year: i,
        p10: result.results.percentiles.p10[i],
        p25: result.results.percentiles.p25[i],
        p50: result.results.percentiles.p50[i],
        p75: result.results.percentiles.p75[i],
        p90: result.results.percentiles.p90[i],
        target: form.target_cad,
      }))
    : []

  return (
    <div>
      <PageHeader
        title="Forecast"
        subtitle="Monte Carlo projections, computed deterministically."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <div className="text-sm font-semibold mb-3">Inputs</div>
          <Field label="Starting balance">
            <NumInput
              value={form.starting_balance_cad}
              onChange={(v) => setForm({ ...form, starting_balance_cad: v })}
              suffix="CAD"
            />
          </Field>
          <Field label="Annual contribution">
            <NumInput
              value={form.annual_contribution_cad}
              onChange={(v) => setForm({ ...form, annual_contribution_cad: v })}
              suffix="CAD"
            />
          </Field>
          <Field label="Horizon (years)">
            <NumInput
              value={form.horizon_years}
              onChange={(v) => setForm({ ...form, horizon_years: v })}
              suffix="yrs"
            />
          </Field>
          <Field label={`Equity weight: ${Math.round(form.equity_weight * 100)}%`}>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={form.equity_weight}
              onChange={(e) =>
                setForm({ ...form, equity_weight: parseFloat(e.target.value) })
              }
              className="w-full accent-gold-500"
            />
          </Field>
          <Field label="Target (optional)">
            <NumInput
              value={form.target_cad}
              onChange={(v) => setForm({ ...form, target_cad: v })}
              suffix="CAD"
            />
          </Field>
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
                <Stat
                  label="Median terminal"
                  value={fmt.cad(result.results.median_terminal)}
                  hint="Nominal CAD"
                />
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
                  value={
                    result.results.prob_hit_target != null
                      ? fmt.pct(result.results.prob_hit_target)
                      : '—'
                  }
                  hint="Probability"
                />
              </div>

              <Card>
                <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">
                  Outcome cone
                </div>
                <div className="h-72 lg:h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 8, left: 0 }}>
                      <defs>
                        <linearGradient id="cone" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#7aa3ff" stopOpacity={0.25} />
                          <stop offset="100%" stopColor="#7aa3ff" stopOpacity={0.04} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis
                        dataKey="year"
                        tick={{ fill: '#71717a', fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        tick={{ fill: '#71717a', fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
                      />
                      <Tooltip
                        contentStyle={{
                          background: 'rgba(12,13,18,0.95)',
                          border: '1px solid rgba(255,255,255,0.08)',
                          borderRadius: 12,
                          fontSize: 12,
                        }}
                        labelStyle={{ color: '#a1a1aa' }}
                        formatter={(v: number) => fmt.cad(v)}
                      />
                      <Area
                        type="monotone"
                        dataKey="p90"
                        stroke="none"
                        fill="url(#cone)"
                        activeDot={false}
                        stackId="1"
                      />
                      <Line
                        type="monotone"
                        dataKey="p50"
                        stroke="#d4b577"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="p10"
                        stroke="#7aa3ff"
                        strokeWidth={1}
                        strokeDasharray="3 3"
                        dot={false}
                      />
                      {form.target_cad ? (
                        <Line
                          type="monotone"
                          dataKey="target"
                          stroke="#5fd09b"
                          strokeWidth={1}
                          strokeDasharray="2 4"
                          dot={false}
                        />
                      ) : null}
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex items-center gap-4 text-[11px] text-zinc-400 mt-2">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-gold-400" /> Median
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-accent-blue" /> P10 floor
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-2 bg-accent-blue/20 rounded-sm" /> P90 cone
                  </span>
                  {form.target_cad ? (
                    <span className="flex items-center gap-1.5">
                      <span className="w-3 h-0.5 bg-accent-green" /> Target
                    </span>
                  ) : null}
                </div>
              </Card>

              {result.narrative?.output_text && (
                <Card>
                  <div className="flex items-center gap-2 mb-2">
                    <SparkleIcon className="w-4 h-4 text-gold-400" />
                    <div className="text-[11px] uppercase tracking-wider text-zinc-500">
                      Forecaster narrative
                    </div>
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

      <Disclaimer />
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mb-3">
      <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">{label}</div>
      {children}
    </label>
  )
}

function NumInput({
  value,
  onChange,
  suffix,
}: {
  value: number
  onChange: (v: number) => void
  suffix?: string
}) {
  return (
    <div className="flex items-center bg-ink-700/60 border border-white/5 rounded-xl px-3 py-2">
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value || '0'))}
        className="bg-transparent w-full outline-none num text-sm"
      />
      {suffix && <span className="text-[11px] text-zinc-500">{suffix}</span>}
    </div>
  )
}
