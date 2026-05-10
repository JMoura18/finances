import { useEffect, useRef, useState } from 'react'
import { api, Account, Transaction } from '../lib/api'
import { fmt } from '../lib/format'
import { Card, PageHeader, Disclaimer, Spinner } from '../components/ui'
import { Modal, FormField, Input, Select, PrimaryButton } from '../components/Modal'
import { PlusIcon } from '../components/Icons'

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
  const [accounts, setAccounts] = useState<Account[]>([])
  const [open, setOpen] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const [importMsg, setImportMsg] = useState<string | null>(null)

  async function reload() {
    const [t, a] = await Promise.all([api.transactions(), api.accounts()])
    setItems(t)
    setAccounts(a)
  }

  useEffect(() => {
    reload().catch(console.error)
  }, [])

  async function onImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const target = accounts[0]
    if (!target) return
    try {
      const r = await api.importCsv(target.id, file)
      setImportMsg(`Imported ${r.imported}, skipped ${r.skipped}`)
      await reload()
    } catch (err) {
      setImportMsg(`Error: ${(err as Error).message}`)
    } finally {
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  if (!items) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Activity"
        subtitle="Source of truth for every position."
        action={
          <div className="hidden lg:flex items-center gap-2">
            <input
              ref={fileInput}
              type="file"
              accept=".csv,text/csv"
              onChange={onImport}
              className="hidden"
              id="csv-input"
            />
            <label
              htmlFor="csv-input"
              className="px-3 py-2 rounded-xl border border-white/10 text-sm hover:bg-white/5 cursor-pointer"
            >
              Import CSV
            </label>
            <PrimaryButton onClick={() => setOpen(true)} className="inline-flex items-center gap-1.5">
              <PlusIcon className="w-4 h-4" /> New transaction
            </PrimaryButton>
          </div>
        }
      />

      {importMsg && (
        <div className="mb-4 text-xs text-zinc-400 px-3 py-2 rounded-xl bg-white/5 border border-white/10">
          {importMsg}
        </div>
      )}

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

      {/* Mobile FAB */}
      <button
        aria-label="Add transaction"
        onClick={() => setOpen(true)}
        className="lg:hidden fixed right-5 bottom-20 w-12 h-12 rounded-full bg-gold-500 text-ink-950 grid place-items-center shadow-glow"
      >
        <PlusIcon className="w-5 h-5" />
      </button>

      <NewTransactionModal
        open={open}
        onClose={() => setOpen(false)}
        accounts={accounts}
        onCreated={async () => {
          setOpen(false)
          await reload()
        }}
      />

      <Disclaimer />
    </div>
  )
}

function NewTransactionModal({
  open,
  onClose,
  accounts,
  onCreated,
}: {
  open: boolean
  onClose: () => void
  accounts: Account[]
  onCreated: () => Promise<void>
}) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [form, setForm] = useState({
    account_id: '',
    symbol: '',
    txn_type: 'buy',
    quantity: '',
    price: '',
    amount_native: '',
    occurred_at: new Date().toISOString().slice(0, 16),
    notes: '',
  })

  useEffect(() => {
    if (open && !form.account_id && accounts[0]) {
      setForm((f) => ({ ...f, account_id: accounts[0].id }))
    }
  }, [open, accounts, form.account_id])

  async function submit() {
    setBusy(true)
    setErr(null)
    try {
      const qty = form.quantity ? parseFloat(form.quantity) : null
      const px = form.price ? parseFloat(form.price) : null
      const amount = form.amount_native
        ? parseFloat(form.amount_native)
        : qty != null && px != null
        ? qty * px
        : 0
      await api.createTransaction({
        account_id: form.account_id,
        symbol: form.symbol || null,
        txn_type: form.txn_type,
        quantity: qty,
        price: px,
        amount_native: amount,
        currency: 'CAD',
        fx_rate: 1,
        occurred_at: new Date(form.occurred_at).toISOString(),
        notes: form.notes || null,
      })
      await onCreated()
    } catch (e) {
      setErr((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New transaction">
      <FormField label="Account">
        <Select
          value={form.account_id}
          onChange={(e) => setForm({ ...form, account_id: e.target.value })}
        >
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </Select>
      </FormField>
      <FormField label="Type">
        <Select
          value={form.txn_type}
          onChange={(e) => setForm({ ...form, txn_type: e.target.value })}
        >
          {['buy', 'sell', 'dividend', 'contribution', 'withdrawal', 'fee'].map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </Select>
      </FormField>
      <FormField label="Symbol">
        <Input
          value={form.symbol}
          placeholder="VFV.TO"
          onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })}
        />
      </FormField>
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Quantity">
          <Input
            type="number"
            value={form.quantity}
            onChange={(e) => setForm({ ...form, quantity: e.target.value })}
          />
        </FormField>
        <FormField label="Price">
          <Input
            type="number"
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
          />
        </FormField>
      </div>
      <FormField label="Amount (CAD)">
        <Input
          type="number"
          value={form.amount_native}
          placeholder="auto = qty × price"
          onChange={(e) => setForm({ ...form, amount_native: e.target.value })}
        />
      </FormField>
      <FormField label="When">
        <Input
          type="datetime-local"
          value={form.occurred_at}
          onChange={(e) => setForm({ ...form, occurred_at: e.target.value })}
        />
      </FormField>
      {err && <div className="text-xs text-accent-red mb-2">{err}</div>}
      <PrimaryButton className="w-full" disabled={busy} onClick={submit}>
        {busy ? 'Saving…' : 'Save transaction'}
      </PrimaryButton>
    </Modal>
  )
}
