import { useEffect, useState } from 'react'
import { api, Transaction } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'

const TYPE_PILL: Record<string, string> = {
  buy: 'pill-good',
  sell: 'pill-bad',
  dividend: 'pill-good',
  contribution: 'pill-neutral',
  withdrawal: 'pill-warn',
  fee: 'pill-warn',
}

export function TransactionsPage() {
  const [items, setItems] = useState<Transaction[] | null>(null)
  useEffect(() => {
    api.transactions().then(setItems).catch(console.error)
  }, [])

  if (!items) return <Spinner />

  return (
    <div>
      <PageHeader title="Activity" subtitle="Source of truth for every position." />

      <Card className="!p-0 overflow-hidden">
        {items.map((t, i) => (
          <div
            key={t.id}
            className={`flex items-center justify-between px-4 lg:px-5 py-3.5 ${
              i !== items.length - 1 ? 'border-b border-white/5' : ''
            }`}
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className={TYPE_PILL[t.txn_type] ?? 'pill-neutral'}>{t.txn_type}</span>
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">
                  {t.symbol ?? <span className="text-zinc-400">{t.txn_type}</span>}
                </div>
                <div className="text-[11px] text-zinc-500">
                  {new Date(t.occurred_at).toLocaleString('en-CA', {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold num">{fmt.cad2(t.amount_cad)}</div>
              {t.quantity != null && t.price != null && (
                <div className="text-[11px] text-zinc-500 num">
                  {fmt.num(t.quantity)} × {fmt.cad2(t.price)}
                </div>
              )}
            </div>
          </div>
        ))}
      </Card>

      <Disclaimer />
    </div>
  )
}
