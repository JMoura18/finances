import { getAuthToken } from './auth'

const BASE = '/api'

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

async function httpForm<T>(path: string, form: FormData): Promise<T> {
  const token = getAuthToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: form, headers })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export type Account = {
  id: string
  name: string
  account_type: 'tfsa' | 'rrsp' | 'fhsa' | 'non_reg' | string
  institution: string | null
  currency: string
  market_value_cad: number
  book_value_cad: number
}

export type Holding = {
  id: string
  account_id: string
  symbol: string
  name: string
  asset_class: string
  sector: string | null
  region: string | null
  quantity: number
  last_price_cad: number
  market_value_cad: number
  acb_total_cad: number
  unrealized_pnl_cad: number
  weight: number
}

export type Transaction = {
  id: string
  account_id: string
  symbol: string | null
  txn_type: string
  quantity: number | null
  price: number | null
  amount_cad: number
  occurred_at: string
  notes: string | null
}

export type RiskResponse = {
  score: number
  regime: string
  concentration: {
    hhi: number
    by_sector: Record<string, number>
    by_region: Record<string, number>
    top: { symbol: string; weight: number }[]
  }
  stress_results: Record<string, number>
}

export type Room = {
  account_type: string
  tax_year: number
  total_room_cad: number
  used_cad: number
  available_cad: number
}

export type RebalanceSuggestion = {
  asset_class: string
  current_weight: number
  target_weight: number
  drift: number
  action: string
}

export type ForecastRequest = {
  scenario_name: string
  starting_balance_cad: number
  annual_contribution_cad: number
  horizon_years: number
  equity_weight: number
  target_cad?: number | null
}

export type ForecastResponse = {
  inputs: ForecastRequest
  results: {
    percentiles: { p10: number[]; p25: number[]; p50: number[]; p75: number[]; p90: number[] }
    median_terminal: number
    p10_terminal: number
    p90_terminal: number
    prob_hit_target: number | null
    real_median_terminal: number
  }
  narrative: { output_text: string } | null
}

export type ScenarioCompareResponse = {
  scenarios: ForecastResponse[]
}

export type Alert = {
  id: string
  severity: 'info' | 'warn' | 'critical'
  title: string
  body: string
  category: string
  is_read: boolean
  created_at: string
}

export type AssetLocation = {
  symbol: string
  current_account_type: string
  recommended_account_type: string
  reason: string
}

export type RebalancePlan = {
  suggestions: RebalanceSuggestion[]
  actions: { account: string; action: string; symbol?: string; amount_cad: number; reason: string }[]
}

export type CalibrationReport = {
  forecast_id: string
  scenario_name: string
  horizon_years: number
  median_predicted_cad: number
  observed_cad: number
  pct_error: number
  in_p10_p90: boolean
  generated_at: string
}

export type HoldingResearch = {
  symbol: string
  narrative: string
  fundamentals: Record<string, string | number | null>
}

export type NewsItem = {
  id: string
  headline: string
  url: string
  published_at: string
  source: string
  relevance: number | null
  sentiment: number | null
  summary: string | null
}

export type EarningsItem = {
  symbol: string
  next_date: string | null
  last_date: string | null
  consensus_eps: number | null
  reported_eps: number | null
}

export type SnaptradeStatus = {
  connected: boolean
  brokerages: string[]
  last_sync: string | null
}

export const api = {
  me: () => http<{ id: string; email: string; display_name: string | null; is_dev: boolean }>('/users/me'),

  accounts: () => http<Account[]>('/accounts'),
  createAccount: (a: { name: string; account_type: string; institution?: string; currency?: string }) =>
    http<Account>('/accounts', { method: 'POST', body: JSON.stringify(a) }),

  holdings: () => http<Holding[]>('/holdings'),
  holding: (id: string) => http<Holding>(`/holdings/${id}`),
  holdingResearch: (id: string) => http<HoldingResearch>(`/holdings/${id}/research`),
  holdingNews: (id: string) => http<NewsItem[]>(`/holdings/${id}/news`),
  holdingEarnings: (id: string) => http<EarningsItem>(`/holdings/${id}/earnings`),

  transactions: () => http<Transaction[]>('/transactions'),
  createTransaction: (t: {
    account_id: string
    symbol?: string | null
    txn_type: string
    quantity?: number | null
    price?: number | null
    amount_native: number
    currency?: string
    fx_rate?: number
    occurred_at: string
    notes?: string | null
  }) => http<Transaction>('/transactions', { method: 'POST', body: JSON.stringify(t) }),

  importCsv: (accountId: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return httpForm<{ imported: number; skipped: number; errors: { row: string; error: string }[] }>(
      `/transactions/import-csv?account_id=${encodeURIComponent(accountId)}`,
      fd,
    )
  },

  risk: () => http<RiskResponse>('/risk'),
  riskNarrative: () => http<{ output_text: string }>('/risk/narrative'),

  rooms: () => http<Room[]>('/tax/rooms'),
  assetLocation: () => http<AssetLocation[]>('/tax/asset-location'),

  rebalance: () => http<RebalanceSuggestion[]>('/rebalance/suggestions'),
  rebalancePlan: () => http<RebalancePlan>('/rebalance/plan'),

  forecast: (body: ForecastRequest) =>
    http<ForecastResponse>('/forecast', { method: 'POST', body: JSON.stringify(body) }),
  forecastScenarios: (scenarios: ForecastRequest[]) =>
    http<ScenarioCompareResponse>('/forecast/scenarios', {
      method: 'POST',
      body: JSON.stringify({ scenarios }),
    }),

  alerts: () => http<Alert[]>('/alerts'),
  dismissAlert: (id: string) => http<{ ok: true }>(`/alerts/${id}/dismiss`, { method: 'POST' }),

  calibration: () => http<CalibrationReport[]>('/calibration'),

  snaptradeStatus: () => http<SnaptradeStatus>('/snaptrade/status'),
  snaptradeConnect: () => http<{ url: string }>('/snaptrade/connect-url', { method: 'POST' }),
  snaptradeSync: () => http<{ ok: true; reconciled: number }>('/snaptrade/sync', { method: 'POST' }),
}
