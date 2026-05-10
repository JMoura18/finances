const BASE = '/api'

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
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

export const api = {
  accounts: () => http<Account[]>('/accounts'),
  holdings: () => http<Holding[]>('/holdings'),
  transactions: () => http<Transaction[]>('/transactions'),
  risk: () => http<RiskResponse>('/risk'),
  rooms: () => http<Room[]>('/tax/rooms'),
  rebalance: () => http<RebalanceSuggestion[]>('/rebalance/suggestions'),
  forecast: (body: ForecastRequest) =>
    http<ForecastResponse>('/forecast', { method: 'POST', body: JSON.stringify(body) }),
}
