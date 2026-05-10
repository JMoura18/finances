import { useEffect, useMemo, useState } from 'react'
import { api, Holding } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'

export function HoldingsPage() {
  const [holdings, setHoldings] = useState<Holding[] | null>(null)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    api.holdings().then(setHoldings).catch(console.error)
  }, [])

  const filtered = useMemo(() => {
    if (!holdings) return null
    const sorted = [...holdings].sort((a, b) => b.market_value_cad - a.market_value_cad)
    if (filter === 'all') return sorted
    return sorted.filter((h) => h.asset_class === filter)
  }, [holdings, filter])

  if (!filtered) return <Spinner />

  const filters = ['all', 'equity', 'etf', 'reit']

  return (
    <div>
      <PageHeader title="Holdings" subtitle="Every position across every account." />

      <div className="flex gap-2 overflow-x-auto no-scrollbar mb-4 -mx-1 px-1">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`shrink-0 px-3 py-1.5 rounded-full text-xs border ${
              filter === f
                ? 'bg-white/10 border-white/20 text-white'
                : 'border-white/5 text-zinc-400 hover:text-white'
            }`}
          >
            {f === 'all' ? 'All' : f.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Mobile cards */}
      <div className="lg:hidden space-y-2.5">
        {filtered.map((h) => (
          <Card key={h.id} className="!p-3">
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <div className="font-semibold">{h.symbol}</div>
                <div className="text-[11px] text-zinc-500 truncate">{h.name}</div>
              </div>
              <div className="text-right">
                <div className="font-semibold num">{fmt.cad(h.market_value_cad)}</div>
                <div className={`text-[11px] num ${h.unrealized_pnl_cad >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {fmt.signed(h.unrealized_pnl_cad)}
                </div>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-2 text-[11px] text-zinc-500">
              <span className="pill-neutral">{h.asset_class}</span>
              {h.sector && <span className="pill-neutral">{h.sector}</span>}
              <span className="ml-auto num">{fmt.num(h.quantity)} sh · {fmt.pct(h.weight)}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Desktop table */}
      <Card className="hidden lg:block !p-0 overflow-hidden">
        <div className="grid grid-cols-12 px-5 py-3 text-[11px] uppercase tracking-wider text-zinc-500 border-b border-white/5">
          <div className="col-span-3">Symbol</div>
          <div className="col-span-2">Asset class</div>
          <div className="col-span-1 text-right">Qty</div>
          <div className="col-span-2 text-right">Last price</div>
          <div className="col-span-2 text-right">Market value</div>
          <div className="col-span-1 text-right">Weight</div>
          <div className="col-span-1 text-right">P&amp;L</div>
        </div>
        {filtered.map((h, i) => (
          <div
            key={h.id}
            className={`grid grid-cols-12 px-5 py-3 text-sm items-center ${
              i % 2 ? 'bg-white/[0.015]' : ''
            } hover:bg-white/[0.04] transition-colors`}
          >
            <div className="col-span-3 min-w-0">
              <div className="font-medium">{h.symbol}</div>
              <div className="text-[11px] text-zinc-500 truncate">{h.name}</div>
            </div>
            <div className="col-span-2 text-zinc-400 text-xs">
              <span className="pill-neutral">{h.asset_class}</span>
            </div>
            <div className="col-span-1 text-right num">{fmt.num(h.quantity)}</div>
            <div className="col-span-2 text-right num">{fmt.cad2(h.last_price_cad)}</div>
            <div className="col-span-2 text-right num font-semibold">{fmt.cad(h.market_value_cad)}</div>
            <div className="col-span-1 text-right num text-zinc-400">{fmt.pct(h.weight)}</div>
            <div className={`col-span-1 text-right num ${h.unrealized_pnl_cad >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              {fmt.signed(h.unrealized_pnl_cad)}
            </div>
          </div>
        ))}
      </Card>

      <Disclaimer />
    </div>
  )
}
