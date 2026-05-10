import { useEffect, useState } from 'react'
import { api, AssetLocation, Room } from '../lib/api'
import { fmt, accountTypeLabel } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner, Empty } from '../components/ui'

export function TaxPage() {
  const [rooms, setRooms] = useState<Room[] | null>(null)
  const [placement, setPlacement] = useState<AssetLocation[] | null>(null)

  useEffect(() => {
    api.rooms().then(setRooms).catch(console.error)
    api.assetLocation().then(setPlacement).catch(console.error)
  }, [])

  if (!rooms) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Tax"
        subtitle="Contribution room and asset-location observations."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 lg:gap-4">
        {rooms.map((r) => {
          const usedPct = r.total_room_cad ? r.used_cad / r.total_room_cad : 0
          return (
            <Card key={r.account_type}>
              <div className="flex items-center justify-between mb-1">
                <div className="text-lg font-semibold">
                  {accountTypeLabel[r.account_type] ?? r.account_type}
                </div>
                <span className="pill-neutral">{r.tax_year}</span>
              </div>
              <div className="text-[11px] text-zinc-500">Available room</div>
              <div className="text-2xl font-semibold num mt-0.5">
                {fmt.cad(r.available_cad)}
              </div>
              <div className="mt-3">
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-accent-blue to-gold-500"
                    style={{ width: `${Math.min(usedPct * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-zinc-500 mt-1.5 num">
                  <span>{fmt.cad(r.used_cad)} used</span>
                  <span>{fmt.cad(r.total_room_cad)} total</span>
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="text-[11px] uppercase tracking-wider text-zinc-500 mt-8 mb-2">
        Asset location
      </div>

      {placement && placement.length > 0 ? (
        <div className="space-y-2">
          {placement.map((p, i) => (
            <Card key={i} className="!p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-semibold">{p.symbol}</div>
                  <div className="text-[11px] text-zinc-400 mt-0.5">{p.reason}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">From → To</div>
                  <div className="text-xs num mt-0.5">
                    <span className="text-zinc-400">{accountTypeLabel[p.current_account_type] ?? p.current_account_type}</span>
                    <span className="text-zinc-600 mx-1">→</span>
                    <span className="text-gold-400">{accountTypeLabel[p.recommended_account_type] ?? p.recommended_account_type}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Empty message="Asset location is reasonable across all holdings." />
      )}

      <Card className="mt-4">
        <div className="text-sm font-semibold mb-1">Asset location reminder</div>
        <p className="text-sm text-zinc-400 leading-relaxed">
          Hold US-listed dividend equities inside an RRSP to avoid the 15% withholding
          tax. Hold Canadian dividends in a non-registered account to claim the dividend
          tax credit. Use a TFSA for high-growth equities you intend to hold long-term.
        </p>
      </Card>

      <Disclaimer />
    </div>
  )
}
