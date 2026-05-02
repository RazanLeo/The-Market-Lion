-- Market Lion — PostgreSQL Main Schema
-- Users, Trades, Subscriptions, Sessions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ──────────────────────────────────────────────
-- Users
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) UNIQUE NOT NULL,
    username            VARCHAR(100) UNIQUE NOT NULL,
    password_hash       TEXT NOT NULL,
    full_name           VARCHAR(255),
    phone               VARCHAR(50),
    country             VARCHAR(10) DEFAULT 'SA',
    language            VARCHAR(10) DEFAULT 'ar',
    avatar_url          TEXT,
    status              VARCHAR(20) DEFAULT 'active',   -- active/suspended/deleted/banned
    is_active           BOOLEAN DEFAULT TRUE,
    is_verified         BOOLEAN DEFAULT FALSE,
    is_email_verified   BOOLEAN DEFAULT FALSE,
    email_verify_token  TEXT,
    reset_token         TEXT,
    reset_token_expires TIMESTAMPTZ,
    is_2fa_enabled      BOOLEAN DEFAULT FALSE,
    totp_secret         TEXT,
    plan                VARCHAR(20) DEFAULT 'free',     -- free/starter/pro/vip/enterprise
    plan_expires_at     TIMESTAMPTZ,
    kyc_status          VARCHAR(20) DEFAULT 'pending',  -- pending/submitted/approved/rejected
    kyc_level           SMALLINT DEFAULT 0,
    kyc_notes           TEXT,
    kyc_reviewed_at     TIMESTAMPTZ,
    kyc_reviewed_by     TEXT,
    total_referrals     INTEGER DEFAULT 0,
    referral_code       VARCHAR(20) UNIQUE DEFAULT substr(md5(random()::text), 0, 9),
    referred_by         UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    last_login          TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_referral ON users(referral_code);

-- ──────────────────────────────────────────────
-- Plans & Subscriptions
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plans (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL,        -- free / starter / pro / vip / enterprise
    name_ar         VARCHAR(100),
    price_monthly   DECIMAL(10,2) NOT NULL,
    price_yearly    DECIMAL(10,2),
    currency        VARCHAR(5) DEFAULT 'USD',
    max_symbols     SMALLINT DEFAULT 3,
    max_signals     INTEGER DEFAULT 10,
    has_auto_trade  BOOLEAN DEFAULT FALSE,
    has_backtesting BOOLEAN DEFAULT FALSE,
    has_api_access  BOOLEAN DEFAULT FALSE,
    has_telegram    BOOLEAN DEFAULT FALSE,
    has_mobile      BOOLEAN DEFAULT FALSE,
    has_vip_support BOOLEAN DEFAULT FALSE,
    features        JSONB DEFAULT '{}',
    stripe_price_id VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    sort_order      SMALLINT DEFAULT 0
);

INSERT INTO plans (name, name_ar, price_monthly, price_yearly, max_symbols, max_signals, has_auto_trade, has_backtesting, has_api_access, has_telegram, has_mobile, has_vip_support, sort_order) VALUES
('free',       'مجاني',         0,    0,      3,    10,  FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, 1),
('starter',    'مبتدئ',        49,   470,     5,    50,  FALSE, FALSE, FALSE, TRUE,  TRUE,  FALSE, 2),
('pro',        'احترافي',     149,  1430,    20,  500,  TRUE,  TRUE,  FALSE, TRUE,  TRUE,  FALSE, 3),
('vip',        'في آي بي',    399,  3830,    -1, -1,    TRUE,  TRUE,  TRUE,  TRUE,  TRUE,  TRUE,  4),
('enterprise', 'مؤسسي',         0,    0,      -1, -1,    TRUE,  TRUE,  TRUE,  TRUE,  TRUE,  TRUE,  5);

CREATE TABLE IF NOT EXISTS subscriptions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id         INTEGER NOT NULL REFERENCES plans(id),
    status          VARCHAR(20) DEFAULT 'active',  -- active/canceled/past_due/trialing
    billing_cycle   VARCHAR(10) DEFAULT 'monthly', -- monthly/yearly
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ends_at         TIMESTAMPTZ,
    trial_ends_at   TIMESTAMPTZ,
    stripe_sub_id   VARCHAR(100),
    hyperpay_sub_id VARCHAR(100),
    auto_renew      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(status);

-- ──────────────────────────────────────────────
-- Sessions / Refresh Tokens
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   TEXT NOT NULL,
    device_info     JSONB DEFAULT '{}',
    ip_address      VARCHAR(45),
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(refresh_token);

-- ──────────────────────────────────────────────
-- Trades
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trades (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id),
    broker              VARCHAR(50) NOT NULL,
    broker_ticket       VARCHAR(100),
    symbol              VARCHAR(20) NOT NULL,
    timeframe           VARCHAR(5),
    side                VARCHAR(5) NOT NULL,    -- BUY / SELL
    entry_price         DECIMAL(18,8),
    sl_price            DECIMAL(18,8),
    tp1_price           DECIMAL(18,8),
    tp2_price           DECIMAL(18,8),
    tp3_price           DECIMAL(18,8),
    lot_size            DECIMAL(10,4),
    close_price         DECIMAL(18,8),
    pnl                 DECIMAL(14,2),
    pnl_pct             DECIMAL(8,4),
    confluence_score    DECIMAL(6,2),
    school_breakdown    JSONB DEFAULT '{}',
    status              VARCHAR(20) DEFAULT 'open',  -- open/closed/canceled/pending
    close_reason        VARCHAR(50),              -- tp1/tp2/tp3/sl/manual/circuit_breaker
    pyramiding_level    SMALLINT DEFAULT 0,
    parent_trade_id     UUID REFERENCES trades(id),
    opened_at           TIMESTAMPTZ DEFAULT NOW(),
    closed_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_opened_at ON trades(opened_at DESC);

-- ──────────────────────────────────────────────
-- Payments
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    subscription_id UUID REFERENCES subscriptions(id),
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(5) DEFAULT 'USD',
    status          VARCHAR(20) DEFAULT 'pending',  -- pending/succeeded/failed/refunded
    provider        VARCHAR(30) NOT NULL,   -- stripe/hyperpay/stcpay/crypto
    provider_id     VARCHAR(200),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- Broker Connections
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS broker_connections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    broker          VARCHAR(50) NOT NULL,       -- capital_com / exness / icmarkets / mt5
    account_id      VARCHAR(100),
    account_login   VARCHAR(100),
    is_demo         BOOLEAN DEFAULT TRUE,
    is_active       BOOLEAN DEFAULT TRUE,
    encrypted_creds TEXT,                       -- AES-256 encrypted
    meta_api_id     VARCHAR(200),
    connected_at    TIMESTAMPTZ DEFAULT NOW(),
    last_sync       TIMESTAMPTZ
);

CREATE INDEX idx_broker_user ON broker_connections(user_id);

-- ──────────────────────────────────────────────
-- Signals Log
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          VARCHAR(20) NOT NULL,
    timeframe       VARCHAR(5),
    side            VARCHAR(5),
    confluence_score DECIMAL(6,2),
    entry           DECIMAL(18,8),
    sl              DECIMAL(18,8),
    tp1             DECIMAL(18,8),
    tp2             DECIMAL(18,8),
    tp3             DECIMAL(18,8),
    should_trade    BOOLEAN,
    school_breakdown JSONB,
    top_factors     JSONB,
    rejection_reasons JSONB,
    generated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_signals_symbol ON signals_log(symbol, generated_at DESC);

-- ──────────────────────────────────────────────
-- Affiliates
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS affiliate_rewards (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id     UUID NOT NULL REFERENCES users(id),
    referred_id     UUID NOT NULL REFERENCES users(id),
    payment_id      UUID REFERENCES payments(id),
    commission_pct  DECIMAL(5,2) DEFAULT 30.00,
    amount          DECIMAL(10,2),
    currency        VARCHAR(5) DEFAULT 'USD',
    status          VARCHAR(20) DEFAULT 'pending',  -- pending/paid/canceled
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────
-- KYC Documents
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kyc_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    doc_type        VARCHAR(50),   -- national_id/passport/driver_license/selfie/proof_of_address
    file_url        TEXT,
    status          VARCHAR(20) DEFAULT 'pending',
    reviewer_notes  TEXT,
    submitted_at    TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
