import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  api,
  EarningsItem,
  Holding,
  HoldingResearch,
  NewsItem,
} from '../lib/api'
import { fmt } from '../lib/format'
import { Card, Disclaimer, PageHeader, Spinner, Stat } from '../components/ui'
import { NewsIcon, SparkleIcon } from '../components/Icons'

export function HoldingDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const [holding, setHolding] = useState<Holding | null>(null)
  const [news, setNews] = useState<NewsItem[] | null>(null)
  const [earnings, setEarnings] = useState<EarningsItem | null>(null)
  const [research, setResearch] = useState<HoldingResearch | null>(null)
  const [researchLoading, setResearchLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let active = true
    Promise.all([
      api.holding(id),
      api.holdingNews(id).catch(() => []),
      api.holdingEarnings(id).catch(() => null),
    ]).then(([h, n, e]) => {
      if (!active) return
      setHolding(h)
      setNews(n)
      setEarnings(e)
    }).catch((e) => setError((e as Error).message))
    return () => { active = false }
  }, [id])

  async function loadResearch() {
    setResearchLoading(true)
    try {
      setResearch(await api.holdingResearch(id))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setResearchLoading(false)
    }
  }

  if (error) return (
    <Card><div className="py-8 text-center text-sm text-accent-red">{error}</div></Card>
  )
  if (!holding) return <Spinner />

  return (
    <div>
      <Link to="/holdings" className="text-xs text-zinc-500 hover:text-white inline-flex items-center gap-1.5 mb-3">
        ← All holdings
      </Link>
      <PageHeader
        title={holding.symbol}
        subtitle={holding.name}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
        <Stat label="Market value" value={fmt.cad(holding.market_value_cad)}
          hint={`${fmt.num(holding.quantity)} sh`} />
        <Stat label="Last price" value={fmt.cad2(holding.last_price_cad)} />
        <Stat label="ACB total" value={fmt.cad(holding.acb_total_cad)} />
        <Stat
          label="Unrealized"
          value={fmt.signed(holding.unrealized_pnl_cad)}
          trend={holding.unrealized_pnl_cad >= 0 ? 'up' : 'down'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <SparkleIcon className="w-4 h-4 text-gold-400" />
              <div className="text-[11px] uppercase tracking-wider text-zinc-500">
                Researcher narrative
              </div>
            </div>
            {!research && (
              <button
                onClick={loadResearch}
                disabled={researchLoading}
                className="text-xs px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-50"
              >
                {researchLoading ? 'Generating…' : 'Generate'}
              </button>
            )}
          </div>
          {research ? (
            <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
              {research.narrative}
            </p>
          ) : (
            <p className="text-sm text-zinc-500">
              Click Generate for a balanced read on {holding.symbol}.
            </p>
          )}
          {research && (
            <div className="mt-4 grid grid-cols-2 gap-2">
              {Object.entries(research.fundamentals).map(([k, v]) => (
                <div key={k} className="px-3 py-2 rounded-lg bg-white/[0.025] border border-white/5">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                    {k.replace(/_/g, ' ')}
                  </div>
                  <div className="text-sm num">{v == null ? '—' : String(v)}</div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-2">Earnings</div>
          {earnings && earnings.next_date ? (
            <>
              <div className="text-2xl font-semibold num">
                {new Date(earnings.next_date).toLocaleDateString('en-CA', {
                  month: 'short', day: 'numeric',
                })}
              </div>
              <div className="text-[11px] text-zinc-500 mt-1">Next report</div>
            </>
          ) : (
            <div className="text-sm text-zinc-500">No upcoming earnings on file.</div>
          )}
        </Card>
      </div>

      <div className="mt-4">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-zinc-500 mb-2">
          <NewsIcon className="w-4 h-4 text-zinc-500" /> Headlines
        </div>
        {news && news.length > 0 ? (
          <Card className="!p-0 overflow-hidden">
            {news.slice(0, 8).map((n, i) => (
              <a
                key={n.id}
                href={n.url}
                target="_blank"
                rel="noreferrer"
                className={`block px-4 lg:px-5 py-3.5 hover:bg-white/[0.03] ${
                  i !== news.length - 1 ? 'border-b border-white/5' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{n.headline}</div>
                    <div className="text-[11px] text-zinc-500 mt-1">
                      {n.source}
                      {n.published_at && ' · ' + new Date(n.published_at).toLocaleDateString('en-CA')}
                    </div>
                  </div>
                  <div className="text-right">
                    {n.relevance != null && (
                      <div className="text-[10px] text-zinc-500">rel {n.relevance.toFixed(2)}</div>
                    )}
                    {n.sentiment != null && (
                      <div className={`text-[10px] num ${n.sentiment > 0 ? 'text-accent-green' : n.sentiment < 0 ? 'text-accent-red' : 'text-zinc-500'}`}>
                        {n.sentiment >= 0 ? '+' : ''}
                        {n.sentiment.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </Card>
        ) : (
          <Card>
            <div className="py-8 text-center text-sm text-zinc-500">No headlines yet.</div>
          </Card>
        )}
      </div>

      <Disclaimer />
    </div>
  )
}
