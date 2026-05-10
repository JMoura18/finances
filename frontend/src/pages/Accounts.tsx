import { useEffect, useState } from 'react'
import { api, Account } from '../lib/api'
import { fmt, accountTypeLabel } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'
import { PlusIcon } from '../components/Icons'

export function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[] | null>(null)
  useEffect(() => {
    api.accounts().then(setAccounts).catch(console.error)
  }, [])

  if (!accounts) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Accounts"
        subtitle="All registered and non-registered accounts in one place."
        action={
          <button className="hidden lg:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-gold-500 text-ink-950 text-sm font-medium hover:bg-gold-400">
            <PlusIcon className="w-4 h-4" /> Add account
          </button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 lg:gap-4">
        {accounts.map((a) => {
          const pnl = a.market_value_cad - a.book_value_cad
          const pnlPct = a.book_value_cad ? pnl / a.book_value_cad : 0
          return (
            <Card key={a.id} className="glass-hover">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs text-zinc-500">{accountTypeLabel[a.account_type] ?? a.account_type}</div>
                  <div className="text-lg font-semibold mt-0.5">{a.name}</div>
                  <div className="text-[11px] text-zinc-500 mt-0.5">{a.institution}</div>
                </div>
                <span className="pill-neutral">{a.currency}</span>
              </div>
              <div className="mt-4">
                <div className="text-[11px] text-zinc-500 uppercase tracking-wider">Market value</div>
                <div className="text-2xl font-semibold num mt-0.5">{fmt.cad(a.market_value_cad)}</div>
                <div className={`text-xs num mt-1 ${pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {fmt.signed(pnl)} ({fmt.signedPct(pnlPct)})
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Mobile FAB */}
      <button
        aria-label="Add account"
        className="lg:hidden fixed right-5 bottom-20 w-12 h-12 rounded-full bg-gold-500 text-ink-950 grid place-items-center shadow-glow"
      >
        <PlusIcon className="w-5 h-5" />
      </button>

      <Disclaimer />
    </div>
  )
}
