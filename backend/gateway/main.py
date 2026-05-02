"""The Market Lion — FastAPI Backend Gateway."""
import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market_data_service.main import MarketDataService
from services.fundamental_data_service.fundamental_engine import FundamentalEngine
from services.technical_analysis_service.indicators import analyze_all_schools
from services.vote_engine_service.engine import run_vote_engine
from services.risk_manager_service.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("market-lion")

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_production_market_lion_2025")
JWT_ALGORITHM = "HS256"

_CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
CORS_ORIGINS = [o.strip() for o in _CORS_ORIGINS_RAW.split(",") if o.strip()]

VALID_TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9/_.-]{1,20}$")


def _validate_symbol(symbol: str) -> str:
    if not SYMBOL_RE.match(symbol):
        raise HTTPException(status_code=400, detail="رمز الأصل غير صالح")
    return symbol.upper()


def _validate_timeframe(timeframe: str) -> str:
    tf = timeframe.upper()
    if tf not in VALID_TIMEFRAMES:
        raise HTTPException(
            status_code=400,
            detail=f"الإطار الزمني غير صالح. المسموح: {sorted(VALID_TIMEFRAMES)}",
        )
    return tf


async def require_auth(authorization: Optional[str] = Header(default=None)):
    """Validate Bearer JWT token — raises 401 if missing or invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header مطلوب")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="نوع التوكن غير صالح")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="التوكن منتهي أو غير صالح")


app = FastAPI(
    title="أسد السوق — The Market Lion API",
    description="Razan AI Trading Bot & Indicator — Backend API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Services
market_data = MarketDataService()
fundamental_engine = FundamentalEngine()
risk_manager = RiskManager()


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, key: str):
        await ws.accept()
        if key not in self.connections:
            self.connections[key] = []
        self.connections[key].append(ws)

    def disconnect(self, ws: WebSocket, key: str):
        if key in self.connections:
            try:
                self.connections[key].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, key: str, data: dict):
        for ws in list(self.connections.get(key, [])):
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


@app.get("/")
async def root():
    return {
        "name": "أسد السوق — The Market Lion",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "services": [
            "market-data", "fundamental", "technical",
            "vote-engine", "risk-manager",
        ],
    }


@app.get("/api/v1/signal/{symbol}/{timeframe}")
async def get_signal(
    symbol: str,
    timeframe: str,
    capital: float = 10000,
    risk_pct: float = 2.0,
    current_user=Depends(require_auth),
):
    """Generate a full trading signal — requires auth."""
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    if capital <= 0:
        raise HTTPException(status_code=400, detail="رأس المال يجب أن يكون موجباً")
    if not 0 < risk_pct <= 10:
        raise HTTPException(status_code=400, detail="نسبة المخاطرة بين 0 و 10")

    try:
        df = await market_data.get_ohlcv_dataframe(symbol, timeframe)
        school_results = analyze_all_schools(df)
        fund_report = await fundamental_engine.get_full_report(symbol)
        fund_score = fund_report.overall_score
        fund_dir = fund_report.direction.value

        import numpy as np
        from services.technical_analysis_service.indicators import atr

        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        atr_vals = atr(high, low, close)
        current_atr = float(atr_vals[-1]) if not np.isnan(atr_vals[-1]) else float(close[-1]) * 0.005
        entry = float(close[-1])

        vote_result = run_vote_engine(
            school_results=school_results,
            fundamental_score=fund_score,
            fundamental_direction=fund_dir,
            mtf_aligned=True,
            killzone_active=False,
            news_shield=fund_report.news_shield_active,
            drawdown_pct=0,
            daily_loss_pct=0,
            consecutive_losses=0,
        )

        swing_high = float(np.max(high[-20:]))
        swing_low = float(np.min(low[-20:]))
        sl = risk_manager.smart_stop_loss(entry, vote_result.side, current_atr, swing_high, swing_low)
        tp1, tp2, tp3 = risk_manager.calculate_take_profits(entry, sl, vote_result.side)
        pos = risk_manager.position_size(capital, entry, sl, 0.0001, 100)

        risk = abs(entry - sl)
        rr1 = abs(tp1 - entry) / risk if risk else 1
        rr2 = abs(tp2 - entry) / risk if risk else 2
        rr3 = abs(tp3 - entry) / risk if risk else 3

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "side": vote_result.side,
            "confluenceScore": vote_result.confluence_score,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "tp3": round(tp3, 5),
            "lotSize": pos.lot_size,
            "riskPct": pos.risk_pct,
            "rr1": round(rr1, 2),
            "rr2": round(rr2, 2),
            "rr3": round(rr3, 2),
            "fundamentalScore": round(fund_score, 1),
            "technicalScore": round(vote_result.confluence_score, 1),
            "shouldTrade": vote_result.should_trade,
            "rejectionReasons": vote_result.rejection_reasons,
            "topFactors": [f["school"] for f in vote_result.top_factors[:5]],
            "schoolBreakdown": vote_result.school_breakdown,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal generation error for {symbol}/{timeframe}: {e}")
        raise HTTPException(status_code=500, detail="خطأ في توليد الإشارة")


@app.get("/api/v1/fundamental/{symbol}")
async def get_fundamental(symbol: str, current_user=Depends(require_auth)):
    symbol = _validate_symbol(symbol)
    try:
        report = await fundamental_engine.get_full_report(symbol)
        return {
            "asset": report.asset,
            "overall_score": report.overall_score,
            "direction": report.direction.value,
            "market_regime": report.market_regime,
            "news_shield_active": report.news_shield_active,
            "top_drivers": report.top_drivers,
            "events_today": [
                {
                    "title": e.title,
                    "impact": e.impact.value,
                    "actual": e.actual,
                    "forecast": e.forecast,
                    "previous": e.previous,
                    "bias": e.bias.value,
                    "sentiment_score": round(e.sentiment_score, 1),
                }
                for e in report.events_today[:20]
            ],
            "generated_at": report.generated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fundamental error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="خطأ في التحليل الأساسي")


@app.get("/api/v1/technical/{symbol}/{timeframe}")
async def get_technical(
    symbol: str, timeframe: str, current_user=Depends(require_auth)
):
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    try:
        df = await market_data.get_ohlcv_dataframe(symbol, timeframe)
        results = analyze_all_schools(df)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "schools": [
                {
                    "school": r.name,
                    "vote": r.vote.value,
                    "strength": round(r.strength, 3),
                    "confidence": round(r.confidence, 3),
                    "details": {
                        k: round(v, 5) if isinstance(v, float) else v
                        for k, v in r.details.items()
                    },
                }
                for r in results
            ],
            "summary": {
                "buy": sum(1 for r in results if r.vote.value == "BUY"),
                "sell": sum(1 for r in results if r.vote.value == "SELL"),
                "neutral": sum(1 for r in results if r.vote.value == "NEUTRAL"),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Technical error for {symbol}/{timeframe}: {e}")
        raise HTTPException(status_code=500, detail="خطأ في التحليل الفني")


@app.get("/api/v1/prices")
async def get_prices(current_user=Depends(require_auth)):
    prices = await asyncio.gather(
        *[
            market_data.fetch_yahoo_quote(sym)
            for sym in ["XAUUSD", "USOIL", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]
        ]
    )
    return {p["symbol"]: p for p in prices if p}


@app.websocket("/ws/{symbol}/{timeframe}")
async def websocket_endpoint(
    ws: WebSocket, symbol: str, timeframe: str, token: Optional[str] = None
):
    """WebSocket: pass ?token=<access_token> to authenticate."""
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                await ws.close(code=4001)
                return
        except JWTError:
            await ws.close(code=4001)
            return

    try:
        symbol = _validate_symbol(symbol)
        timeframe = _validate_timeframe(timeframe)
    except HTTPException:
        await ws.close(code=4000)
        return

    key = f"{symbol}_{timeframe}"
    await manager.connect(ws, key)
    logger.info(f"WS connected: {key}")
    try:
        while True:
            await ws.send_json(
                {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            )
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=5.0)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(ws, key)
        logger.info(f"WS disconnected: {key}")


# ─── Proxy routes to Phase-2 microservices ───────────────────────────────────
import aiohttp as _aiohttp

NEWS_SVC = os.getenv("NEWS_SVC_URL", "http://news_ingestion_service:8007")
ML_SVC = os.getenv("ML_SVC_URL", "http://ai_ml_service:8008")
PATTERNS_SVC = os.getenv("PATTERNS_SVC_URL", "http://patterns_service:8009")
PA_SVC = os.getenv("PA_SVC_URL", "http://price_action_service:8010")
USER_SVC = os.getenv("USER_SVC_URL", "http://user_service:8011")
WHALE_SVC = os.getenv("WHALE_SVC_URL", "http://whale_tracker_service:8012")
RISK_SVC  = os.getenv("RISK_SVC_URL",  "http://risk_manager_service:8013")
NOTIF_SVC = os.getenv("NOTIF_SVC_URL", "http://notification_service:8014")


async def _proxy_get(base: str, path: str, params: dict = None):
    async with _aiohttp.ClientSession() as s:
        r = await s.get(
            f"{base}{path}",
            params=params,
            timeout=_aiohttp.ClientTimeout(total=15),
        )
        return await r.json()


async def _proxy_post(base: str, path: str, payload: dict):
    async with _aiohttp.ClientSession() as s:
        r = await s.post(
            f"{base}{path}",
            json=payload,
            timeout=_aiohttp.ClientTimeout(total=15),
        )
        return await r.json()


@app.get("/api/v1/news/{asset}")
async def proxy_news(asset: str, hours: int = 24, current_user=Depends(require_auth)):
    asset = _validate_symbol(asset)
    if not 1 <= hours <= 168:
        raise HTTPException(status_code=400, detail="hours بين 1 و 168")
    return await _proxy_get(NEWS_SVC, f"/news/{asset}", {"hours": hours})


@app.get("/api/v1/sentiment/{asset}")
async def proxy_sentiment(asset: str, hours: int = 4, current_user=Depends(require_auth)):
    asset = _validate_symbol(asset)
    return await _proxy_get(NEWS_SVC, f"/sentiment/{asset}", {"hours": hours})


@app.get("/api/v1/calendar")
async def proxy_calendar(hours_ahead: int = 24, current_user=Depends(require_auth)):
    return await _proxy_get(NEWS_SVC, "/calendar", {"hours_ahead": hours_ahead})


@app.get("/api/v1/calendar/high-impact")
async def proxy_high_impact(current_user=Depends(require_auth)):
    return await _proxy_get(NEWS_SVC, "/calendar/high-impact")


@app.post("/api/v1/ml/predict")
async def proxy_ml_predict(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(ML_SVC, "/predict", payload)


@app.post("/api/v1/patterns/scan")
async def proxy_patterns(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(PATTERNS_SVC, "/scan", payload)


@app.post("/api/v1/price-action/analyze")
async def proxy_price_action(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(PA_SVC, "/analyze", payload)


@app.get("/api/v1/users/me")
async def proxy_user_me(current_user=Depends(require_auth), authorization: str = Header(...)):
    async with _aiohttp.ClientSession(headers={"Authorization": authorization}) as s:
        r = await s.get(f"{USER_SVC}/users/me", timeout=_aiohttp.ClientTimeout(total=10))
        return await r.json()


@app.post("/api/v1/users")
async def proxy_create_user(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(USER_SVC, "/users", payload)


@app.post("/api/v1/whale/analyze")
async def proxy_whale(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(WHALE_SVC, "/analyze", payload)


@app.get("/api/v1/whale/fear-greed")
async def proxy_fear_greed(current_user=Depends(require_auth)):
    return await _proxy_get(WHALE_SVC, "/fear-greed")


@app.post("/api/v1/risk/validate")
async def proxy_risk_validate(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(RISK_SVC, "/validate", payload)


@app.post("/api/v1/risk/position-size")
async def proxy_position_size(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(RISK_SVC, "/position-size", payload)


@app.post("/api/v1/risk/entry-strategy")
async def proxy_entry_strategy(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(RISK_SVC, "/entry-strategy", payload)


@app.post("/api/v1/risk/trailing-stop")
async def proxy_trailing_stop(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(RISK_SVC, "/trailing-stop", payload)


@app.post("/api/v1/risk/pyramid")
async def proxy_pyramid(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(RISK_SVC, "/pyramid", payload)


@app.get("/api/v1/risk/session")
async def proxy_session_info(current_user=Depends(require_auth)):
    return await _proxy_get(RISK_SVC, "/session-info")


# Notifications
@app.post("/api/v1/notify/signal")
async def proxy_notify_signal(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(NOTIF_SVC, "/notify/signal", payload)


@app.post("/api/v1/notify/subscribe")
async def proxy_notify_subscribe(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(NOTIF_SVC, "/subscribe", payload)


@app.get("/api/v1/notify/subscribers/{symbol}")
async def proxy_notify_subs(symbol: str, current_user=Depends(require_auth)):
    symbol = _validate_symbol(symbol)
    return await _proxy_get(NOTIF_SVC, f"/subscribers/{symbol}")


# ML extras
@app.post("/api/v1/ml/rl/episode")
async def proxy_rl_episode(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(ML_SVC, "/rl/record-episode", payload)


@app.get("/api/v1/ml/rl/weights/{asset}/{timeframe}")
async def proxy_rl_weights(asset: str, timeframe: str, current_user=Depends(require_auth)):
    asset = _validate_symbol(asset)
    timeframe = _validate_timeframe(timeframe)
    return await _proxy_get(ML_SVC, f"/rl/school-weights/{asset}/{timeframe}")


@app.post("/api/v1/ml/drift/check")
async def proxy_drift_check(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post(ML_SVC, "/drift/check", payload)


# Backtesting extras
@app.post("/api/v1/backtest/walk-forward")
async def proxy_walk_forward(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post("http://backtesting_service:8002", "/backtest/walk-forward", payload)


@app.post("/api/v1/backtest/monte-carlo")
async def proxy_monte_carlo(payload: dict, current_user=Depends(require_auth)):
    return await _proxy_post("http://backtesting_service:8002", "/backtest/monte-carlo", payload)


# ─── Multi-Timeframe Analysis ─────────────────────────────────────────────────

MTF_TIMEFRAMES = ["M15", "M30", "H1", "H4", "D1"]


async def _analyze_single_tf(symbol: str, tf: str) -> dict:
    """Run full vote engine on one timeframe — returns compact result."""
    import numpy as np
    from services.technical_analysis_service.indicators import atr as _atr
    try:
        df = await market_data.get_ohlcv_dataframe(symbol, tf)
        school_results = analyze_all_schools(df)
        vote_result = run_vote_engine(
            school_results=school_results,
            fundamental_score=50.0,
            fundamental_direction="NEUTRAL",
            mtf_aligned=True,
            killzone_active=False,
            news_shield=False,
            drawdown_pct=0,
            daily_loss_pct=0,
            consecutive_losses=0,
        )
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        atr_vals = _atr(high, low, close)
        current_atr = float(atr_vals[-1]) if not np.isnan(atr_vals[-1]) else float(close[-1]) * 0.005
        return {
            "timeframe": tf,
            "side": vote_result.side,
            "confluenceScore": round(vote_result.confluence_score, 1),
            "buyVotes": vote_result.buy_votes,
            "sellVotes": vote_result.sell_votes,
            "neutralVotes": vote_result.neutral_votes,
            "weightedScore": round(vote_result.weighted_score, 4),
            "atr": round(current_atr, 5),
            "close": round(float(close[-1]), 5),
            "topFactors": [f["school"] for f in vote_result.top_factors[:3]],
            "error": None,
        }
    except Exception as exc:
        return {"timeframe": tf, "side": "NEUTRAL", "confluenceScore": 0.0,
                "buyVotes": 0, "sellVotes": 0, "neutralVotes": 0,
                "weightedScore": 0.0, "atr": 0.0, "close": 0.0,
                "topFactors": [], "error": str(exc)}


@app.get("/api/v1/signal/{symbol}/mtf")
async def get_mtf_signal(
    symbol: str,
    capital: float = 10000,
    risk_pct: float = 2.0,
    current_user=Depends(require_auth),
):
    """Multi-Timeframe analysis — runs M15/M30/H1/H4/D1 in parallel.
    Returns alignment table + recommended entry TF."""
    symbol = _validate_symbol(symbol)
    if capital <= 0:
        raise HTTPException(status_code=400, detail="رأس المال يجب أن يكون موجباً")

    try:
        tf_results = await asyncio.gather(*[_analyze_single_tf(symbol, tf) for tf in MTF_TIMEFRAMES])
        valid = [r for r in tf_results if r["error"] is None]

        buy_count = sum(1 for r in valid if r["side"] == "BUY")
        sell_count = sum(1 for r in valid if r["side"] == "SELL")
        total = len(valid) or 1

        # Determine dominant direction
        if buy_count / total >= 0.6:
            overall_side = "BUY"
        elif sell_count / total >= 0.6:
            overall_side = "SELL"
        else:
            overall_side = "NEUTRAL"

        # Alignment score: % of TFs agreeing with dominant side
        agreeing = buy_count if overall_side == "BUY" else (sell_count if overall_side == "SELL" else 0)
        alignment_pct = round((agreeing / total) * 100, 1)

        # Best entry TF: highest confluence that agrees with overall direction
        entry_candidates = [r for r in valid if r["side"] == overall_side]
        best_entry_tf = max(entry_candidates, key=lambda r: r["confluenceScore"])["timeframe"] if entry_candidates else "H1"

        # Higher-TF confirmation: D1 + H4 both agree?
        htf_confirm = all(
            r["side"] == overall_side
            for r in valid if r["timeframe"] in ("H4", "D1") and r["error"] is None
        )

        # Average confluence
        avg_conf = round(sum(r["confluenceScore"] for r in valid) / total, 1) if valid else 0.0

        # SHAP-style attribution: which schools drive the overall direction
        # Use the best entry TF's breakdown
        import numpy as np
        from services.technical_analysis_service.indicators import atr as _atr
        try:
            df_entry = await market_data.get_ohlcv_dataframe(symbol, best_entry_tf)
            school_results_entry = analyze_all_schools(df_entry)
            fund_report = await fundamental_engine.get_full_report(symbol)
            vote_entry = run_vote_engine(
                school_results=school_results_entry,
                fundamental_score=fund_report.overall_score,
                fundamental_direction=fund_report.direction.value,
                mtf_aligned=htf_confirm,
                killzone_active=False,
                news_shield=fund_report.news_shield_active,
                drawdown_pct=0,
                daily_loss_pct=0,
                consecutive_losses=0,
            )
            # SHAP attribution: contribution % of each top factor
            total_abs = sum(abs(f["weight"] * f["strength"]) for f in vote_entry.school_breakdown) or 1
            shap_factors = [
                {
                    "school": f["school"],
                    "vote": f["vote"],
                    "contribution_pct": round(abs(f["weight"] * f["strength"]) / total_abs * 100, 1),
                    "strength": f["strength"],
                    "confidence": f["confidence"],
                }
                for f in sorted(vote_entry.school_breakdown, key=lambda x: abs(x["weight"] * x["strength"]), reverse=True)[:7]
            ]

            close = df_entry["close"].values
            high = df_entry["high"].values
            low = df_entry["low"].values
            atr_vals = _atr(high, low, close)
            current_atr = float(atr_vals[-1]) if not np.isnan(atr_vals[-1]) else float(close[-1]) * 0.005
            entry = float(close[-1])
            sl = risk_manager.smart_stop_loss(entry, vote_entry.side, current_atr, float(np.max(high[-20:])), float(np.min(low[-20:])))
            tp1, tp2, tp3 = risk_manager.calculate_take_profits(entry, sl, vote_entry.side)
            pos = risk_manager.position_size(capital, entry, sl, 0.0001, 100)
            risk_dist = abs(entry - sl)

            mtf_signal = {
                "symbol": symbol,
                "overallSide": overall_side,
                "overallConfluence": avg_conf,
                "alignmentPct": alignment_pct,
                "htfConfirmed": htf_confirm,
                "bestEntryTF": best_entry_tf,
                "shouldTrade": vote_entry.should_trade and htf_confirm,
                "rejectionReasons": vote_entry.rejection_reasons + ([] if htf_confirm else ["HTF_NOT_ALIGNED"]),
                "entry": round(entry, 5),
                "sl": round(sl, 5),
                "tp1": round(tp1, 5),
                "tp2": round(tp2, 5),
                "tp3": round(tp3, 5),
                "lotSize": pos.lot_size,
                "riskPct": pos.risk_pct,
                "rr1": round(abs(tp1 - entry) / risk_dist, 2) if risk_dist else 1.0,
                "rr2": round(abs(tp2 - entry) / risk_dist, 2) if risk_dist else 2.0,
                "rr3": round(abs(tp3 - entry) / risk_dist, 2) if risk_dist else 3.0,
                "shapFactors": shap_factors,
                "fundamentalScore": round(fund_report.overall_score, 1),
                "newShieldActive": fund_report.news_shield_active,
                "timeframes": tf_results,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as inner_exc:
            logger.warning(f"MTF entry analysis error: {inner_exc}")
            mtf_signal = {
                "symbol": symbol,
                "overallSide": overall_side,
                "overallConfluence": avg_conf,
                "alignmentPct": alignment_pct,
                "htfConfirmed": htf_confirm,
                "bestEntryTF": best_entry_tf,
                "shouldTrade": False,
                "rejectionReasons": ["ANALYSIS_ERROR"],
                "shapFactors": [],
                "timeframes": tf_results,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            }

        return mtf_signal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MTF signal error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="خطأ في التحليل متعدد الإطارات")


@app.get("/api/v1/signal/{symbol}/{timeframe}/shap")
async def get_shap_attribution(
    symbol: str,
    timeframe: str,
    current_user=Depends(require_auth),
):
    """SHAP-style attribution: returns contribution % of each school to the signal."""
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    try:
        df = await market_data.get_ohlcv_dataframe(symbol, timeframe)
        school_results = analyze_all_schools(df)
        fund_report = await fundamental_engine.get_full_report(symbol)
        vote_result = run_vote_engine(
            school_results=school_results,
            fundamental_score=fund_report.overall_score,
            fundamental_direction=fund_report.direction.value,
            mtf_aligned=True,
            killzone_active=False,
            news_shield=fund_report.news_shield_active,
            drawdown_pct=0,
            daily_loss_pct=0,
            consecutive_losses=0,
        )
        total_abs = sum(abs(f["weight"] * f["strength"]) for f in vote_result.school_breakdown) or 1
        shap_data = []
        for f in vote_result.school_breakdown:
            raw_contrib = f["weight"] * vote_to_score_val(f["vote"]) * f["strength"]
            shap_data.append({
                "school": f["school"],
                "vote": f["vote"],
                "contribution_pct": round(abs(f["weight"] * f["strength"]) / total_abs * 100, 2),
                "signed_contribution": round(raw_contrib / total_abs * 100, 2),
                "weight": round(f["weight"], 4),
                "strength": round(f["strength"], 3),
                "confidence": round(f["confidence"], 3),
            })
        shap_data.sort(key=lambda x: abs(x["contribution_pct"]), reverse=True)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "side": vote_result.side,
            "confluenceScore": vote_result.confluence_score,
            "shapAttribution": shap_data,
            "top5": shap_data[:5],
            "fundamentalScore": round(fund_report.overall_score, 1),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SHAP error for {symbol}/{timeframe}: {e}")
        raise HTTPException(status_code=500, detail="خطأ في حساب SHAP")


def vote_to_score_val(vote_str: str) -> float:
    return 1.0 if vote_str == "BUY" else (-1.0 if vote_str == "SELL" else 0.0)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
