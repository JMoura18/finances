import { useEffect, useState } from 'react'
import { api, Room } from '../lib/api'
import { fmt, accountTypeLabel } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'

export function TaxPage() {
  const [rooms, setRooms] = useState<Room[] | null>(null)
  useEffect(() => {
    api.rooms().then(setRooms).catch(console.error)
  }, [])

  if (!rooms) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Tax"
        subtitle="Contribution room across registered accounts."
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

      <Card className="mt-4">
        <div className="text-sm font-semibold mb-1">Asset location reminder</div>
        <p className="text-sm text-zinc-400 leading-relaxed">
          Hold US-listed dividend equities inside an RRSP to avoid the 15% withholding
          tax. Hold Canadian dividends in a non-registered account to claim the dividend
          tax credit. Use TFSA for high-growth equities you intend to hold long-term.
        </p>
      </Card>

      <Disclaimer />
    </div>
  )
}
