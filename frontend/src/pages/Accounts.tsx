import { useEffect, useState } from 'react'
import { api, Account, SnaptradeStatus } from '../lib/api'
import { fmt, accountTypeLabel } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'
import { Modal, FormField, Input, Select, PrimaryButton } from '../components/Modal'
import { LinkIcon, PlusIcon } from '../components/Icons'

export function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[] | null>(null)
  const [snap, setSnap] = useState<SnaptradeStatus | null>(null)
  const [open, setOpen] = useState(false)
  const [syncBusy, setSyncBusy] = useState(false)
  const [syncMsg, setSyncMsg] = useState<string | null>(null)

  async function reload() {
    const [a, s] = await Promise.all([api.accounts(), api.snaptradeStatus().catch(() => null)])
    setAccounts(a)
    setSnap(s)
  }
  useEffect(() => {
    reload().catch(console.error)
  }, [])

  async function connect() {
    const r = await api.snaptradeConnect()
    window.open(r.url, '_blank', 'noopener,noreferrer')
  }

  async function sync() {
    setSyncBusy(true)
    setSyncMsg(null)
    try {
      const r = await api.snaptradeSync()
      setSyncMsg(`Reconciled ${r.reconciled} account${r.reconciled === 1 ? '' : 's'}.`)
      await reload()
    } catch (e) {
      setSyncMsg(`Error: ${(e as Error).message}`)
    } finally {
      setSyncBusy(false)
    }
  }

  if (!accounts) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Accounts"
        subtitle="All registered and non-registered accounts in one place."
        action={
          <div className="hidden lg:flex gap-2">
            <button
              onClick={connect}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-white/10 text-sm hover:bg-white/5"
            >
              <LinkIcon className="w-4 h-4" /> Connect brokerage
            </button>
            <PrimaryButton
              onClick={() => setOpen(true)}
              className="inline-flex items-center gap-1.5"
            >
              <PlusIcon className="w-4 h-4" /> Add account
            </PrimaryButton>
          </div>
        }
      />

      <Card className="mb-4 flex items-center justify-between">
        <div className="text-sm">
          <div className="font-medium">SnapTrade · {snap?.connected ? 'connected' : 'not connected'}</div>
          <div className="text-[11px] text-zinc-500 mt-0.5">
            Read-only by contract. Cofre never trades on your behalf.
            {snap?.brokerages?.length ? ` · ${snap.brokerages.join(', ')}` : ''}
          </div>
        </div>
        <div className="flex gap-2">
          {!snap?.connected && (
            <button onClick={connect} className="text-xs px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/5">
              Connect
            </button>
          )}
          <button
            onClick={sync}
            disabled={syncBusy}
            className="text-xs px-3 py-1.5 rounded-lg bg-gold-500 text-ink-950 font-medium hover:bg-gold-400 disabled:opacity-60"
          >
            {syncBusy ? 'Syncing…' : 'Sync now'}
          </button>
        </div>
      </Card>
      {syncMsg && (
        <div className="mb-4 text-xs text-zinc-400 px-3 py-2 rounded-xl bg-white/5 border border-white/10">
          {syncMsg}
        </div>
      )}

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

      <button
        aria-label="Add account"
        onClick={() => setOpen(true)}
        className="lg:hidden fixed right-5 bottom-20 w-12 h-12 rounded-full bg-gold-500 text-ink-950 grid place-items-center shadow-glow"
      >
        <PlusIcon className="w-5 h-5" />
      </button>

      <NewAccountModal open={open} onClose={() => setOpen(false)} onCreated={async () => {
        setOpen(false)
        await reload()
      }} />

      <Disclaimer />
    </div>
  )
}

function NewAccountModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean
  onClose: () => void
  onCreated: () => Promise<void>
}) {
  const [form, setForm] = useState({
    name: '',
    account_type: 'tfsa',
    institution: '',
    currency: 'CAD',
  })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function submit() {
    setBusy(true)
    setErr(null)
    try {
      await api.createAccount(form)
      await onCreated()
    } catch (e) {
      setErr((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New account">
      <FormField label="Name">
        <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="TFSA" />
      </FormField>
      <FormField label="Type">
        <Select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })}>
          <option value="tfsa">TFSA</option>
          <option value="rrsp">RRSP</option>
          <option value="fhsa">FHSA</option>
          <option value="non_reg">Non-registered</option>
          <option value="rrif">RRIF</option>
          <option value="lira">LIRA</option>
          <option value="resp">RESP</option>
          <option value="corporate">Corporate</option>
        </Select>
      </FormField>
      <FormField label="Institution">
        <Input value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} placeholder="Wealthsimple" />
      </FormField>
      {err && <div className="text-xs text-accent-red mb-2">{err}</div>}
      <PrimaryButton className="w-full" disabled={busy || !form.name} onClick={submit}>
        {busy ? 'Saving…' : 'Save account'}
      </PrimaryButton>
    </Modal>
  )
}
