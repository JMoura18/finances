import { useEffect, useMemo, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api, CalibrationReport } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, Disclaimer, Empty, PageHeader, Spinner, Stat } from '../components/ui'

export function CalibrationPage() {
  const [reports, setReports] = useState<CalibrationReport[] | null>(null)

  useEffect(() => {
    api.calibration().then(setReports).catch(console.error)
  }, [])

  const stats = useMemo(() => {
    if (!reports || reports.length === 0) return null
    const inBand = reports.filter((r) => r.in_p10_p90).length
    const meanErr =
      reports.reduce((s, r) => s + r.pct_error, 0) / reports.length
    const absErr =
      reports.reduce((s, r) => s + Math.abs(r.pct_error), 0) / reports.length
    return {
      total: reports.length,
      inBand,
      hitRate: inBand / reports.length,
      meanErr,
      absErr,
    }
  }, [reports])

  if (!reports) return <Spinner />

  const chartData = reports.map((r) => ({
    name: r.scenario_name,
    err: r.pct_error * 100,
  }))

  return (
    <div>
      <PageHeader
        title="Calibration"
        subtitle="How forecasts compare to what actually happened."
      />

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
          <Stat label="Forecasts tracked" value={stats.total} />
          <Stat
            label="Hit rate"
            value={fmt.pct(stats.hitRate)}
            hint="Inside P10–P90 band"
            trend={stats.hitRate >= 0.7 ? 'up' : stats.hitRate >= 0.5 ? 'flat' : 'down'}
          />
          <Stat
            label="Mean error"
            value={`${(stats.meanErr * 100).toFixed(1)}%`}
            hint="Bias direction"
            trend={Math.abs(stats.meanErr) < 0.05 ? 'up' : 'flat'}
          />
          <Stat
            label="Abs error"
            value={`${(stats.absErr * 100).toFixed(1)}%`}
            hint="Average magnitude"
          />
        </div>
      )}

      <Card className="mt-4">
        <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-3">
          Error per scenario (% of median forecast)
        </div>
        {chartData.length === 0 ? (
          <Empty message="No calibration data yet." />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 8, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 11 }} tickLine={false} axisLine={false} />
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
                    borderRadius: 12, fontSize: 12,
                  }}
                  formatter={(v: number) => `${v.toFixed(1)}%`}
                />
                <Bar dataKey="err" radius={[6, 6, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.err >= 0 ? '#5fd09b' : '#7aa3ff'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <Card className="mt-4 !p-0 overflow-hidden">
        <div className="grid grid-cols-12 px-5 py-3 text-[11px] uppercase tracking-wider text-zinc-500 border-b border-white/5">
          <div className="col-span-4">Scenario</div>
          <div className="col-span-3 text-right">Predicted (median)</div>
          <div className="col-span-2 text-right">Observed</div>
          <div className="col-span-2 text-right">Error</div>
          <div className="col-span-1 text-right">Band</div>
        </div>
        {reports.map((r) => (
          <div key={r.forecast_id} className="grid grid-cols-12 px-5 py-3 text-sm items-center border-b border-white/5 last:border-b-0">
            <div className="col-span-4">
              <div className="font-medium">{r.scenario_name}</div>
              <div className="text-[11px] text-zinc-500">{r.horizon_years}y horizon</div>
            </div>
            <div className="col-span-3 text-right num text-zinc-300">{fmt.cad(r.median_predicted_cad)}</div>
            <div className="col-span-2 text-right num">{fmt.cad(r.observed_cad)}</div>
            <div className={`col-span-2 text-right num ${Math.abs(r.pct_error) > 0.1 ? 'text-accent-amber' : 'text-zinc-300'}`}>
              {(r.pct_error * 100).toFixed(1)}%
            </div>
            <div className="col-span-1 text-right">
              {r.in_p10_p90 ? <span className="pill-good">in</span> : <span className="pill-bad">out</span>}
            </div>
          </div>
        ))}
      </Card>

      <Disclaimer />
    </div>
  )
}
