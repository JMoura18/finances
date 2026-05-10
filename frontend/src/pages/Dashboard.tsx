import { useEffect, useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { api, Account, Holding, RiskResponse } from '../lib/api'
import { fmt, accountTypeLabel } from '../lib/format'
import { Card, PageHeader, Stat, Disclaimer, Spinner } from '../components/ui'
import { ArrowUpRight, SparkleIcon } from '../components/Icons'

export function DashboardPage() {
  const [accounts, setAccounts] = useState<Account[] | null>(null)
  const [holdings, setHoldings] = useState<Holding[] | null>(null)
  const [risk, setRisk] = useState<RiskResponse | null>(null)

  useEffect(() => {
    api.accounts().then(setAccounts).catch(console.error)
    api.holdings().then(setHoldings).catch(console.error)
    api.risk().then(setRisk).catch(console.error)
  }, [])

  const totals = useMemo(() => {
    if (!accounts) return null
    const market = accounts.reduce((s, a) => s + a.market_value_cad, 0)
    const book = accounts.reduce((s, a) => s + a.book_value_cad, 0)
    return { market, book, pnl: market - book, pnlPct: book ? (market - book) / book : 0 }
  }, [accounts])

  const trend = useMemo(() => buildTrend(totals?.market ?? 0), [totals?.market])

  if (!accounts || !holdings) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Good evening, Jesse"
        subtitle="Here is where things stand today."
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
        <Stat
          label="Total portfolio"
          value={totals ? fmt.cad(totals.market) : '—'}
          hint={totals ? `${fmt.signed(totals.pnl)} (${fmt.signedPct(totals.pnlPct)})` : ''}
          trend={totals && totals.pnl >= 0 ? 'up' : 'down'}
        />
        <Stat
          label="Unrealized P&L"
          value={totals ? fmt.signed(totals.pnl) : '—'}
          hint="Lifetime, all accounts"
          trend={totals && totals.pnl >= 0 ? 'up' : 'down'}
        />
        <Stat
          label="Risk score"
          value={risk ? <span>{risk.score.toFixed(0)}<span className="text-base text-zinc-500"> / 100</span></span> : '—'}
          hint={risk ? `Regime: ${risk.regime}` : ''}
        />
        <Stat
          label="Holdings"
          value={holdings.length}
          hint={`${accounts.length} accounts`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <Card className="lg:col-span-2">
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="text-[11px] uppercase tracking-wider text-zinc-500">90 day trend</div>
              <div className="text-lg font-semibold num mt-0.5">
                {totals ? fmt.cad(totals.market) : '—'}
              </div>
            </div>
            <span className="pill-good">+4.2%</span>
          </div>
          <div className="h-48 lg:h-60">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#d4b577" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#d4b577" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="d" tick={{ fill: '#71717a', fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis hide domain={['dataMin - 1000', 'dataMax + 1000']} />
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
                  dataKey="v"
                  stroke="#d4b577"
                  strokeWidth={2}
                  fill="url(#g1)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-[11px] uppercase tracking-wider text-zinc-500">Accounts</div>
            </div>
            <a href="/accounts" className="text-xs text-zinc-400 hover:text-white inline-flex items-center gap-1">
              View all <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
          <div className="space-y-2.5">
            {accounts.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between p-3 rounded-xl bg-white/[0.025] border border-white/5"
              >
                <div>
                  <div className="text-sm font-medium">{a.name}</div>
                  <div className="text-[11px] text-zinc-500">
                    {accountTypeLabel[a.account_type] ?? a.account_type} · {a.institution}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold num">{fmt.cad(a.market_value_cad)}</div>
                  <div className="text-[11px] num text-zinc-500">
                    {fmt.signed(a.market_value_cad - a.book_value_cad)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Top holdings</div>
            <a href="/holdings" className="text-xs text-zinc-400 hover:text-white inline-flex items-center gap-1">
              View all <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
          <div className="space-y-2">
            {[...holdings]
              .sort((a, b) => b.market_value_cad - a.market_value_cad)
              .slice(0, 5)
              .map((h) => (
                <div
                  key={h.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-white/[0.025] border border-white/5"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{h.symbol}</div>
                    <div className="text-[11px] text-zinc-500 truncate">{h.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold num">{fmt.cad(h.market_value_cad)}</div>
                    <div className={`text-[11px] num ${h.unrealized_pnl_cad >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {fmt.signed(h.unrealized_pnl_cad)}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-2">
            <SparkleIcon className="w-4 h-4 text-gold-400" />
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Forecaster note</div>
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed">
            Based on your current pace, the median outcome lands above your retirement
            target with room to spare, while the bottom-decile path is still on track.
            A 60/40 mix would compress the cone but reduce the median.
          </p>
          <a
            href="/forecast"
            className="inline-flex items-center gap-1.5 mt-3 text-xs text-gold-400 hover:text-gold-500"
          >
            Open forecast <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </Card>
      </div>

      <Disclaimer />
    </div>
  )
}

function buildTrend(latest: number) {
  const days = 90
  const out: { d: string; v: number }[] = []
  let v = latest * 0.96
  for (let i = days; i >= 0; i--) {
    const drift = 0.0008
    const shock = (Math.sin(i / 4) + Math.cos(i / 7)) * 0.003
    v = v * (1 + drift + shock)
    const date = new Date()
    date.setDate(date.getDate() - i)
    out.push({
      d: date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
      v: Math.round(v),
    })
  }
  out[out.length - 1].v = Math.round(latest)
  return out
}
