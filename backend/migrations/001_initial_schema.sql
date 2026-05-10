-- Cofre initial schema
-- Twelve-table foundation: users, accounts, holdings, transactions,
-- securities, prices, agent_runs, forecasts, risk_snapshots,
-- contribution_rooms, alerts, news_items.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firebase_uid TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    province TEXT,
    birth_year INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL
        CHECK (account_type IN ('tfsa','rrsp','fhsa','non_reg','rrif','lira','resp','corporate')),
    currency CHAR(3) NOT NULL DEFAULT 'CAD',
    institution TEXT,
    snaptrade_account_id TEXT UNIQUE,
    is_synced BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_accounts_user ON accounts(user_id);

CREATE TABLE securities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    asset_class TEXT NOT NULL
        CHECK (asset_class IN ('equity','etf','bond','reit','cash','crypto','option')),
    currency CHAR(3) NOT NULL,
    name TEXT,
    sector TEXT,
    region TEXT,
    UNIQUE(symbol, exchange)
);
CREATE INDEX idx_securities_symbol ON securities(symbol);

CREATE TABLE holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES securities(id) ON DELETE RESTRICT,
    quantity NUMERIC(20,8) NOT NULL DEFAULT 0,
    acb_total_cad NUMERIC(20,4) NOT NULL DEFAULT 0,
    last_recomputed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(account_id, security_id)
);
CREATE INDEX idx_holdings_account ON holdings(account_id);
CREATE INDEX idx_holdings_security ON holdings(security_id);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    security_id UUID REFERENCES securities(id) ON DELETE RESTRICT,
    txn_type TEXT NOT NULL
        CHECK (txn_type IN ('buy','sell','dividend','interest','contribution','withdrawal','fee','split','transfer_in','transfer_out')),
    quantity NUMERIC(20,8),
    price NUMERIC(20,8),
    amount_native NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    fx_rate NUMERIC(20,8) NOT NULL DEFAULT 1.0,
    amount_cad NUMERIC(20,4) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    source TEXT NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual','csv','snaptrade')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_security ON transactions(security_id);
CREATE INDEX idx_transactions_occurred ON transactions(occurred_at);

CREATE TABLE prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
    as_of DATE NOT NULL,
    close NUMERIC(20,8) NOT NULL,
    currency CHAR(3) NOT NULL,
    source TEXT NOT NULL DEFAULT 'yahoo',
    UNIQUE(security_id, as_of)
);
CREATE INDEX idx_prices_security_date ON prices(security_id, as_of DESC);

CREATE TABLE forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scenario_name TEXT NOT NULL,
    horizon_years INT NOT NULL,
    target_cad NUMERIC(20,2),
    inputs JSONB NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_forecasts_user ON forecasts(user_id);

CREATE TABLE risk_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score NUMERIC(5,2) NOT NULL,
    regime TEXT NOT NULL CHECK (regime IN ('calm','normal','elevated','crisis')),
    concentration JSONB NOT NULL,
    stress_results JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_risk_user_date ON risk_snapshots(user_id, created_at DESC);

CREATE TABLE contribution_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_type TEXT NOT NULL
        CHECK (account_type IN ('tfsa','rrsp','fhsa')),
    tax_year INT NOT NULL,
    total_room_cad NUMERIC(20,2) NOT NULL,
    used_cad NUMERIC(20,2) NOT NULL DEFAULT 0,
    UNIQUE(user_id, account_type, tax_year)
);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    severity TEXT NOT NULL CHECK (severity IN ('info','warn','critical')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_alerts_user_unread ON alerts(user_id, is_read, created_at DESC);

CREATE TABLE news_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id UUID REFERENCES securities(id) ON DELETE CASCADE,
    headline TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    relevance NUMERIC(4,3),
    sentiment NUMERIC(4,3),
    summary TEXT
);
CREATE INDEX idx_news_security_date ON news_items(security_id, published_at DESC);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    input_payload JSONB NOT NULL,
    output_text TEXT,
    input_tokens INT,
    output_tokens INT,
    cost_usd NUMERIC(10,6),
    duration_ms INT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_agent_runs_user_date ON agent_runs(user_id, created_at DESC);
CREATE INDEX idx_agent_runs_agent ON agent_runs(agent_name);
