# Architecture — The Market Lion

```
Browser  ──▶  Caddy (TLS, WAF)  ──▶  ┬─▶ Frontend (Next.js 14)
                                     └─▶ Backend (FastAPI)  ──▶ Postgres + TimescaleDB
                                              │                    Redis (cache + pubsub)
                                              ├─▶ Celery Workers (news, schools, indicators, voting, execution)
                                              └─▶ Capital.com REST/WS · Stripe · PayPal · HyperPay · OpenAI
```

## Concurrency model
- HTTP API: FastAPI async + asyncpg.
- Workers: Celery (queues per concern) + Celery Beat for periodic ingest.
- Pub/sub: Redis Streams + classic pubsub.

## Voting flow
1. Worker `tasks.voting.recompute_all` runs every minute.
2. For each (symbol, tf), pulls 300 OHLCV bars from Capital.com.
3. Runs 18 analyzers (production-implemented in this sprint).
4. Aggregates via `compute_confluence` → score 0..100 + decision.
5. Persists in `confluence_scores` and publishes to `analysis:{symbol}:{tf}`.
6. Frontend WS subscribes per symbol/tf and updates UI.

## Trade execution
1. User selects symbol/risk/tf/manual-or-auto.
2. Manual buy/sell → `POST /trades/manual` → `risk_engine.build_trade_plan` → `CapitalAdapter.open_market` → save Position + TradeEvent.
3. Auto bot: every minute checks Confluence ≥ threshold + risk limits → opens position → trailing SL after each TP.

## Security
- Argon2id passwords + bcrypt fallback.
- JWT with refresh-rotation.
- 2FA TOTP via `pyotp`.
- API keys encrypted at rest (AES-GCM + key from env).
- Rate-limit at Caddy + nginx (configurable).
- Audit logs for every privileged action.
