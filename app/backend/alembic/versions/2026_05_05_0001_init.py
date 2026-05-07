"""initial schema + timescale extensions + hypertables + seed plans

Revision ID: 0001init
Revises:
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"citext\";")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"timescaledb\";")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"vector\";")

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("email_verified", sa.Boolean, server_default=sa.text("false")),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("phone", sa.String(40)),
        sa.Column("country", sa.String(80)),
        sa.Column("city", sa.String(120)),
        sa.Column("preferred_lang", sa.String(8), server_default="ar"),
        sa.Column("preferred_tz", sa.String(64), server_default="Asia/Riyadh"),
        sa.Column("role", sa.String(32), nullable=False, server_default="trader"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("twofa_secret", sa.Text),
        sa.Column("twofa_enabled", sa.Boolean, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_hash", sa.Text, nullable=False),
        sa.Column("ip", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "password_resets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean, server_default=sa.text("false")),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name_ar", sa.String(120), nullable=False),
        sa.Column("name_en", sa.String(120), nullable=False),
        sa.Column("monthly_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="SAR"),
        sa.Column("features_json", postgresql.JSONB, server_default=sa.text("'{}'")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_renew", sa.Boolean, server_default=sa.text("true")),
        sa.Column("payment_provider", sa.String(32)),
        sa.Column("external_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id")),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_ref", sa.String(255)),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "broker_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker", sa.String(32), nullable=False),
        sa.Column("account_login", sa.String(64), nullable=False),
        sa.Column("api_key_enc", sa.Text, nullable=False),
        sa.Column("api_secret_enc", sa.Text, nullable=False),
        sa.Column("account_type", sa.String(16), server_default="demo"),
        sa.Column("base_currency", sa.String(8)),
        sa.Column("leverage_max", sa.Integer),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "trading_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("default_symbol", sa.String(32)),
        sa.Column("risk_pct", sa.Numeric(4, 2), server_default="1.00"),
        sa.Column("default_tf", sa.String(8), server_default="15M"),
        sa.Column("reference_tf", sa.String(8), server_default="4H"),
        sa.Column("trade_mode", sa.String(16), server_default="manual"),
        sa.Column("bot_enabled", sa.Boolean, server_default=sa.text("false")),
        sa.Column("custom_palette", postgresql.JSONB),
        sa.Column("toggles_json", postgresql.JSONB),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "news_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("url", sa.Text),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("body", sa.Text),
        sa.Column("symbols", postgresql.ARRAY(sa.String)),
        sa.Column("sentiment", sa.Numeric(5, 2)),
        sa.Column("impact", sa.Numeric(5, 2)),
        sa.Column("category", sa.String(32)),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("raw", postgresql.JSONB),
    )
    op.create_index("idx_news_ts", "news_items", ["ts"], postgresql_using="btree")
    op.create_index("idx_news_sym", "news_items", ["symbols"], postgresql_using="gin")

    op.create_table(
        "economic_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country", sa.String(8)),
        sa.Column("category", sa.String(64)),
        sa.Column("title", sa.Text),
        sa.Column("previous_v", sa.Numeric(20, 6)),
        sa.Column("forecast_v", sa.Numeric(20, 6)),
        sa.Column("actual_v", sa.Numeric(20, 6)),
        sa.Column("impact_level", sa.String(16)),
        sa.Column("symbols_affected", postgresql.ARRAY(sa.String)),
    )

    # Trade tables
    op.create_table(
        "trade_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("tf", sa.String(8), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8)),
        sa.Column("tp1_price", sa.Numeric(20, 8)),
        sa.Column("tp2_price", sa.Numeric(20, 8)),
        sa.Column("tp3_price", sa.Numeric(20, 8)),
        sa.Column("final_tp_price", sa.Numeric(20, 8)),
        sa.Column("sl_price", sa.Numeric(20, 8)),
        sa.Column("add_zone_price", sa.Numeric(20, 8)),
        sa.Column("lot_size", sa.Numeric(12, 4)),
        sa.Column("leverage", sa.Integer),
        sa.Column("risk_pct", sa.Numeric(5, 2)),
        sa.Column("risk_amount", sa.Numeric(20, 2)),
        sa.Column("pip_value", sa.Numeric(20, 8)),
        sa.Column("expected_profit", sa.Numeric(20, 2)),
        sa.Column("expected_loss", sa.Numeric(20, 2)),
        sa.Column("confidence", sa.Numeric(5, 2)),
        sa.Column("status", sa.String(32), server_default="proposed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("broker_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("broker_accounts.id")),
        sa.Column("trade_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trade_plans.id")),
        sa.Column("broker_ticket", sa.String(64)),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8)),
        sa.Column("lot_size", sa.Numeric(12, 4)),
        sa.Column("entry_price", sa.Numeric(20, 8)),
        sa.Column("exit_price", sa.Numeric(20, 8)),
        sa.Column("tp_price", sa.Numeric(20, 8)),
        sa.Column("sl_price", sa.Numeric(20, 8)),
        sa.Column("trailing_sl", sa.Numeric(20, 8)),
        sa.Column("swap", sa.Numeric(20, 2), server_default="0"),
        sa.Column("commission", sa.Numeric(20, 2), server_default="0"),
        sa.Column("spread_cost", sa.Numeric(20, 2), server_default="0"),
        sa.Column("pl", sa.Numeric(20, 2), server_default="0"),
        sa.Column("pl_pct", sa.Numeric(8, 4), server_default="0"),
        sa.Column("status", sa.String(32), server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "trade_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("positions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("event", sa.String(32), nullable=False),
        sa.Column("meta", postgresql.JSONB),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_role", sa.String(32)),
        sa.Column("action", sa.String(64)),
        sa.Column("resource", sa.String(64)),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("ip", postgresql.INET),
        sa.Column("ua", sa.Text),
        sa.Column("meta", postgresql.JSONB),
    )

    op.create_table(
        "feature_toggles",
        sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("meta", postgresql.JSONB),
    )

    # ── time-series tables (hypertables) ─────────────────────────────
    op.execute("""
        CREATE TABLE market_ticks (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            bid NUMERIC(20,8),
            ask NUMERIC(20,8),
            last NUMERIC(20,8),
            volume NUMERIC(20,2)
        );
        SELECT create_hypertable('market_ticks','ts', if_not_exists => TRUE);

        CREATE TABLE market_ohlcv (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            tf TEXT NOT NULL,
            o NUMERIC(20,8),
            h NUMERIC(20,8),
            l NUMERIC(20,8),
            c NUMERIC(20,8),
            v NUMERIC(20,2),
            PRIMARY KEY (symbol, tf, ts)
        );
        SELECT create_hypertable('market_ohlcv','ts', if_not_exists => TRUE);

        CREATE TABLE order_flow_events (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT,
            bucket TEXT,
            price NUMERIC(20,8),
            notional NUMERIC(20,2),
            participant_hint TEXT
        );
        SELECT create_hypertable('order_flow_events','ts', if_not_exists => TRUE);

        CREATE TABLE confluence_scores (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            tf TEXT NOT NULL,
            fundamental_pct NUMERIC(5,2),
            basics_pct NUMERIC(5,2),
            schools_pct NUMERIC(5,2),
            indicators_pct NUMERIC(5,2),
            flow_pct NUMERIC(5,2),
            total_pct NUMERIC(5,2),
            decision TEXT,
            payload JSONB,
            PRIMARY KEY (symbol, tf, ts)
        );
        SELECT create_hypertable('confluence_scores','ts', if_not_exists => TRUE);

        CREATE TABLE school_signals (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            tf TEXT NOT NULL,
            school_code TEXT NOT NULL,
            result TEXT,
            confidence NUMERIC(5,2),
            weight NUMERIC(5,2),
            payload JSONB,
            PRIMARY KEY (symbol, tf, school_code, ts)
        );
        SELECT create_hypertable('school_signals','ts', if_not_exists => TRUE);
        CREATE INDEX idx_school_signals_lookup ON school_signals(symbol, tf, school_code, ts DESC);

        CREATE TABLE indicator_signals (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            tf TEXT NOT NULL,
            indicator_code TEXT NOT NULL,
            result TEXT,
            confidence NUMERIC(5,2),
            weight NUMERIC(5,2),
            payload JSONB,
            PRIMARY KEY (symbol, tf, indicator_code, ts)
        );
        SELECT create_hypertable('indicator_signals','ts', if_not_exists => TRUE);
    """)

    # ── seed plans ─────────────────────────────────────────────────
    op.execute("""
        INSERT INTO plans (code, name_ar, name_en, monthly_price, currency, features_json, is_active) VALUES
        ('individual', 'الأفراد', 'Individual', 2000.00, 'SAR',
            '{"max_concurrent_trades": 5, "broker_accounts": 1, "auto_trading": true, "chat_ai": true, "all_schools": true}'::jsonb,
            true),
        ('institution', 'المؤسسات', 'Institution', 6000.00, 'SAR',
            '{"max_concurrent_trades": 50, "broker_accounts": 5, "sub_users": 20, "auto_trading": true, "chat_ai": true, "all_schools": true, "api_access": true, "institutional_reports": true}'::jsonb,
            true);
    """)

    # ── seed feature toggles ───────────────────────────────────────
    op.execute("""
        INSERT INTO feature_toggles (key, enabled, meta) VALUES
        ('auto_trading', true, '{}'),
        ('news_pipeline', true, '{}'),
        ('bookmap', true, '{}'),
        ('rl_learning', true, '{}'),
        ('chat_ai', true, '{}'),
        ('paytabs_payment', false, '{"reason":"awaiting subscription per رزان"}'),
        ('exness_broker', false, '{"reason":"deferred — Capital.com only at launch"}')
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS indicator_signals CASCADE;")
    op.execute("DROP TABLE IF EXISTS school_signals CASCADE;")
    op.execute("DROP TABLE IF EXISTS confluence_scores CASCADE;")
    op.execute("DROP TABLE IF EXISTS order_flow_events CASCADE;")
    op.execute("DROP TABLE IF EXISTS market_ohlcv CASCADE;")
    op.execute("DROP TABLE IF EXISTS market_ticks CASCADE;")
    for t in ["feature_toggles","audit_logs","trade_events","positions","trade_plans","economic_events","news_items","trading_preferences","broker_accounts","payments","subscriptions","plans","password_resets","auth_sessions","users"]:
        op.drop_table(t)
