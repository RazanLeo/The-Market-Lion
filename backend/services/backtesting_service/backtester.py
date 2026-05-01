"""Market Lion — Backtesting Engine.
Uses numpy-based vectorized backtesting over historical OHLCV data.
Supports: all 24+ technical schools, walk-forward validation, Monte Carlo simulation.
"""
import asyncio
import numpy as np
import pandas as pd
import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger("backtester")

sys_path_inserted = False
try:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from services.technical_analysis_service.indicators import analyze_all_schools
    from services.vote_engine_service.engine import run_vote_engine
    from services.risk_manager_service.risk_manager import RiskManager
    sys_path_inserted = True
except Exception:
    pass


# ──────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────
@dataclass
class BacktestConfig:
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    risk_per_trade: float = 2.0        # %
    commission_per_lot: float = 7.0    # USD round-trip
    slippage_pips: float = 1.0
    max_open_trades: int = 3
    compound: bool = True
    use_walk_forward: bool = False
    wf_train_pct: float = 0.70


@dataclass
class TradeRecord:
    open_time: pd.Timestamp
    close_time: Optional[pd.Timestamp]
    symbol: str
    side: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    lot_size: float
    exit_price: float = 0.0
    pnl_pips: float = 0.0
    pnl_usd: float = 0.0
    close_reason: str = ""
    confluence_score: float = 0.0
    bars_held: int = 0


@dataclass
class BacktestResult:
    config: BacktestConfig
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)
    # Summary stats
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    calmar_ratio: float = 0.0
    avg_rr: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_bars_held: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0


# ──────────────────────────────────────────────
# Backtester Core
# ──────────────────────────────────────────────
class Backtester:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._risk_mgr = RiskManager() if sys_path_inserted else None

    async def init(self):
        self._pool = await asyncpg.create_pool(
            os.getenv("TIMESCALE_URL", "postgresql://lion:lion_secret_2024@localhost:5433/market_lion_ts")
        )

    async def _load_data(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        if self._pool:
            rows = await self._pool.fetch(
                "SELECT time, open, high, low, close, volume FROM ohlcv WHERE symbol=$1 AND timeframe=$2 AND time BETWEEN $3 AND $4 ORDER BY time",
                symbol, timeframe, start, end
            )
            if rows:
                df = pd.DataFrame([dict(r) for r in rows])
                df.set_index("time", inplace=True)
                return df

        # Synthetic fallback for demo
        return self._generate_demo_data(symbol, 1000)

    def _generate_demo_data(self, symbol: str, n: int = 1000) -> pd.DataFrame:
        np.random.seed(42)
        base_prices = {"XAUUSD": 2350.0, "USOIL": 78.5, "EURUSD": 1.08, "GBPUSD": 1.27,
                       "USDJPY": 149.5, "BTCUSD": 65000.0}
        price = base_prices.get(symbol, 1.0)
        volatility = price * 0.001

        returns = np.random.normal(0.0001, volatility, n)
        closes = price * np.exp(np.cumsum(returns))
        highs = closes * (1 + np.abs(np.random.normal(0, 0.0005, n)))
        lows = closes * (1 - np.abs(np.random.normal(0, 0.0005, n)))
        opens = np.roll(closes, 1)
        opens[0] = closes[0]
        volumes = np.random.uniform(1000, 5000, n)

        dates = pd.date_range("2023-01-01", periods=n, freq="1h")
        return pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes}, index=dates)

    def _pip_value(self, symbol: str, lot_size: float, price: float) -> float:
        forex_majors = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"]
        if symbol in forex_majors:
            return lot_size * 100000 * 0.0001
        if symbol == "USDJPY":
            return lot_size * 100000 * 0.01 / price
        if symbol == "XAUUSD":
            return lot_size * 100 * 0.1
        if symbol in ("USOIL", "XBRUSD"):
            return lot_size * 1000 * 0.01
        if symbol == "BTCUSD":
            return lot_size * 0.01
        return lot_size * 0.0001

    def run(self, config: BacktestConfig, df: pd.DataFrame) -> BacktestResult:
        result = BacktestResult(config=config)
        capital = config.initial_capital
        open_trades: list[TradeRecord] = []
        equity = [capital]

        warmup = 200  # bars needed for indicators

        for i in range(warmup, len(df) - 1):
            bar = df.iloc[:i + 1]
            next_bar = df.iloc[i + 1]
            current_price = float(bar["close"].iloc[-1])
            current_time = bar.index[-1]

            # Check exits first
            for trade in open_trades[:]:
                close_reason = ""
                exit_price = current_price

                if trade.side == "BUY":
                    if float(next_bar["low"]) <= trade.sl:
                        exit_price, close_reason = trade.sl, "sl"
                    elif float(next_bar["high"]) >= trade.tp3:
                        exit_price, close_reason = trade.tp3, "tp3"
                    elif float(next_bar["high"]) >= trade.tp2:
                        exit_price, close_reason = trade.tp2, "tp2"
                    elif float(next_bar["high"]) >= trade.tp1:
                        exit_price, close_reason = trade.tp1, "tp1"
                else:
                    if float(next_bar["high"]) >= trade.sl:
                        exit_price, close_reason = trade.sl, "sl"
                    elif float(next_bar["low"]) <= trade.tp3:
                        exit_price, close_reason = trade.tp3, "tp3"
                    elif float(next_bar["low"]) <= trade.tp2:
                        exit_price, close_reason = trade.tp2, "tp2"
                    elif float(next_bar["low"]) <= trade.tp1:
                        exit_price, close_reason = trade.tp1, "tp1"

                if close_reason:
                    pip_val = self._pip_value(config.symbol, trade.lot_size, exit_price)
                    if trade.side == "BUY":
                        pips = (exit_price - trade.entry) / (trade.sl * 0.0001 if "JPY" not in config.symbol else 0.01) if trade.sl else 0
                        pnl = (exit_price - trade.entry) * trade.lot_size * 100000 if "USD" in config.symbol[:3] else pip_val * abs(exit_price - trade.entry) / 0.0001
                    else:
                        pnl = (trade.entry - exit_price) * trade.lot_size * 100000 if "USD" in config.symbol[:3] else pip_val * abs(trade.entry - exit_price) / 0.0001

                    pnl -= config.commission_per_lot * trade.lot_size
                    capital += pnl if config.compound else pnl
                    trade.exit_price = exit_price
                    trade.pnl_usd = pnl
                    trade.close_reason = close_reason
                    trade.close_time = next_bar.name
                    trade.bars_held = i - warmup
                    open_trades.remove(trade)
                    result.trades.append(trade)

            equity.append(capital)

            if len(open_trades) >= config.max_open_trades:
                continue

            # Generate signal
            if not sys_path_inserted:
                continue

            try:
                school_results = analyze_all_schools(bar)
                vote = run_vote_engine(school_results=school_results, fundamental_score=50.0,
                                      fundamental_direction="NEUTRAL", mtf_aligned=True,
                                      killzone_active=False, news_shield=False,
                                      drawdown_pct=0, daily_loss_pct=0, consecutive_losses=0)

                if not vote.should_trade:
                    continue

                from services.technical_analysis_service.indicators import atr
                close_arr = bar["close"].values
                high_arr = bar["high"].values
                low_arr = bar["low"].values
                atr_vals = atr(high_arr, low_arr, close_arr)
                current_atr = float(atr_vals[-1]) if not np.isnan(atr_vals[-1]) else current_price * 0.005

                entry = current_price * (1 + config.slippage_pips * 0.0001)
                swing_high = float(np.max(high_arr[-20:]))
                swing_low = float(np.min(low_arr[-20:]))
                sl = self._risk_mgr.smart_stop_loss(entry, vote.side, current_atr, swing_high, swing_low)
                tp1, tp2, tp3 = self._risk_mgr.calculate_take_profits(entry, sl, vote.side)

                risk_amount = capital * (config.risk_per_trade / 100)
                risk_per_unit = abs(entry - sl)
                lot_size = round(risk_amount / (risk_per_unit * 100000 + 1e-9), 2)
                lot_size = max(0.01, min(lot_size, 10.0))

                trade = TradeRecord(
                    open_time=current_time, close_time=None,
                    symbol=config.symbol, side=vote.side,
                    entry=entry, sl=sl, tp1=tp1, tp2=tp2, tp3=tp3,
                    lot_size=lot_size, confluence_score=vote.confluence_score
                )
                open_trades.append(trade)
            except Exception:
                continue

        # Close remaining open trades at last price
        last_price = float(df["close"].iloc[-1])
        for trade in open_trades:
            pip_val = self._pip_value(config.symbol, trade.lot_size, last_price)
            if trade.side == "BUY":
                pnl = (last_price - trade.entry) * trade.lot_size * 10000
            else:
                pnl = (trade.entry - last_price) * trade.lot_size * 10000
            pnl -= config.commission_per_lot * trade.lot_size
            capital += pnl
            trade.exit_price = last_price
            trade.pnl_usd = pnl
            trade.close_reason = "end_of_test"
            trade.close_time = df.index[-1]
            result.trades.append(trade)
        equity.append(capital)

        result.equity_curve = equity
        self._calculate_stats(result, config.initial_capital)
        return result

    def _calculate_stats(self, result: BacktestResult, initial_capital: float):
        trades = result.trades
        result.total_trades = len(trades)
        if not trades:
            return

        pnls = [t.pnl_usd for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        result.win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        result.avg_win = float(np.mean(wins)) if wins else 0
        result.avg_loss = float(np.mean(losses)) if losses else 0
        result.total_pnl = float(sum(pnls))
        result.total_pnl_pct = result.total_pnl / initial_capital * 100
        result.best_trade = float(max(pnls)) if pnls else 0
        result.worst_trade = float(min(pnls)) if pnls else 0
        result.avg_bars_held = float(np.mean([t.bars_held for t in trades]))

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        result.expectancy = (result.win_rate / 100 * result.avg_win) + ((1 - result.win_rate / 100) * result.avg_loss)

        # Drawdown
        equity = result.equity_curve
        if equity:
            peak = initial_capital
            max_dd = 0.0
            for eq in equity:
                if eq > peak:
                    peak = eq
                dd = peak - eq
                if dd > max_dd:
                    max_dd = dd
            result.max_drawdown = max_dd
            result.max_drawdown_pct = max_dd / initial_capital * 100

        # Sharpe (annualized, assuming hourly bars)
        if len(pnls) > 1:
            ret_series = pd.Series(pnls)
            daily_ret = result.total_pnl / max(1, len(pnls))
            std_ret = float(ret_series.std())
            result.sharpe_ratio = (daily_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0

            neg_rets = ret_series[ret_series < 0]
            sortino_std = float(neg_rets.std()) if len(neg_rets) > 1 else 1
            result.sortino_ratio = (daily_ret / sortino_std * np.sqrt(252)) if sortino_std > 0 else 0

        result.calmar_ratio = (result.total_pnl_pct / result.max_drawdown_pct) if result.max_drawdown_pct > 0 else 0

        # Consecutive wins/losses
        max_cw = max_cl = cw = cl = 0
        for p in pnls:
            if p > 0:
                cw += 1; cl = 0
                max_cw = max(max_cw, cw)
            else:
                cl += 1; cw = 0
                max_cl = max(max_cl, cl)
        result.consecutive_wins = max_cw
        result.consecutive_losses = max_cl

    def to_dict(self, result: BacktestResult) -> dict:
        return {
            "config": {
                "symbol": result.config.symbol,
                "timeframe": result.config.timeframe,
                "start_date": result.config.start_date,
                "end_date": result.config.end_date,
                "initial_capital": result.config.initial_capital,
                "risk_per_trade": result.config.risk_per_trade,
            },
            "stats": {
                "total_trades": result.total_trades,
                "win_rate": round(result.win_rate, 2),
                "profit_factor": round(result.profit_factor, 2),
                "sharpe_ratio": round(result.sharpe_ratio, 2),
                "sortino_ratio": round(result.sortino_ratio, 2),
                "calmar_ratio": round(result.calmar_ratio, 2),
                "max_drawdown": round(result.max_drawdown, 2),
                "max_drawdown_pct": round(result.max_drawdown_pct, 2),
                "total_pnl": round(result.total_pnl, 2),
                "total_pnl_pct": round(result.total_pnl_pct, 2),
                "avg_win": round(result.avg_win, 2),
                "avg_loss": round(result.avg_loss, 2),
                "expectancy": round(result.expectancy, 2),
                "best_trade": round(result.best_trade, 2),
                "worst_trade": round(result.worst_trade, 2),
                "consecutive_wins": result.consecutive_wins,
                "consecutive_losses": result.consecutive_losses,
                "avg_bars_held": round(result.avg_bars_held, 1),
            },
            "equity_curve": result.equity_curve[::10],  # downsample for transfer
            "trades_count": result.total_trades,
        }


# ──────────────────────────────────────────────
# FastAPI endpoint (can be embedded in main)
# ──────────────────────────────────────────────
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel

bt_app = FastAPI(title="Market Lion Backtester", version="1.0.0")
backtester = Backtester()


@bt_app.on_event("startup")
async def startup():
    await backtester.init()


class RunBacktestRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "H1"
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    initial_capital: float = 10000
    risk_per_trade: float = 2.0
    compound: bool = True


@bt_app.post("/backtest/run")
async def run_backtest(req: RunBacktestRequest):
    config = BacktestConfig(**req.dict())
    df = await backtester._load_data(config.symbol, config.timeframe, config.start_date, config.end_date)
    result = backtester.run(config, df)
    return backtester.to_dict(result)


# ─── Walk-Forward Optimization ────────────────────────────────────────────────

class WalkForwardRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "H1"
    start_date: str = "2022-01-01"
    end_date: str = "2024-01-01"
    initial_capital: float = 10000
    risk_per_trade: float = 2.0
    train_months: int = 6
    test_months: int = 1
    compound: bool = True


@bt_app.post("/backtest/walk-forward")
async def walk_forward_optimization(req: WalkForwardRequest):
    """Walk-Forward Optimization: sliding train/test windows.
    Default: 6-month train + 1-month test, step 1 month.
    Returns per-window stats + aggregate summary.
    Criteria: Sharpe ≥ 1.5, Profit Factor ≥ 2, Max DD ≤ 20%.
    """
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse as parse_date

    train_size = relativedelta(months=req.train_months)
    test_size = relativedelta(months=req.test_months)

    start = parse_date(req.start_date)
    end = parse_date(req.end_date)

    windows = []
    cursor = start
    while cursor + train_size + test_size <= end:
        train_start = cursor
        train_end = cursor + train_size
        test_start = train_end
        test_end = test_start + test_size
        windows.append({
            "train_start": train_start.strftime("%Y-%m-%d"),
            "train_end": train_end.strftime("%Y-%m-%d"),
            "test_start": test_start.strftime("%Y-%m-%d"),
            "test_end": test_end.strftime("%Y-%m-%d"),
        })
        cursor += test_size  # step by test_months

    if not windows:
        raise HTTPException(status_code=400, detail="نطاق زمني غير كافٍ للـ Walk-Forward")

    window_results = []
    for w in windows:
        try:
            # Load test data (we use test window for out-of-sample metrics)
            test_df = await backtester._load_data(req.symbol, req.timeframe, w["test_start"], w["test_end"])
            if len(test_df) < 50:
                continue
            config = BacktestConfig(
                symbol=req.symbol,
                timeframe=req.timeframe,
                start_date=w["test_start"],
                end_date=w["test_end"],
                initial_capital=req.initial_capital,
                risk_per_trade=req.risk_per_trade,
                compound=req.compound,
            )
            result = backtester.run(config, test_df)
            stats = backtester.to_dict(result)["stats"]

            # Quality gate
            passed = (
                stats["sharpe_ratio"] >= 1.5 and
                stats["profit_factor"] >= 2.0 and
                stats["max_drawdown_pct"] <= 20.0 and
                stats["total_trades"] >= 5
            )
            window_results.append({
                "window": w,
                "stats": stats,
                "passed_quality_gate": passed,
                "equity_curve": backtester.to_dict(result)["equity_curve"],
            })
        except Exception as exc:
            window_results.append({"window": w, "stats": {}, "passed_quality_gate": False, "error": str(exc)})

    if not window_results:
        raise HTTPException(status_code=422, detail="لا توجد نتائج كافية")

    valid = [w for w in window_results if w.get("stats")]
    total_windows = len(valid)
    passed_windows = sum(1 for w in valid if w["passed_quality_gate"])

    # Aggregate metrics across windows
    def _avg(key):
        vals = [w["stats"].get(key, 0) for w in valid if w.get("stats")]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    aggregate = {
        "total_windows": total_windows,
        "passed_windows": passed_windows,
        "pass_rate_pct": round(passed_windows / total_windows * 100, 1) if total_windows else 0,
        "avg_win_rate": _avg("win_rate"),
        "avg_profit_factor": _avg("profit_factor"),
        "avg_sharpe": _avg("sharpe_ratio"),
        "avg_max_drawdown_pct": _avg("max_drawdown_pct"),
        "avg_total_pnl_pct": _avg("total_pnl_pct"),
        "recommendation": "DEPLOY" if passed_windows / max(total_windows, 1) >= 0.7 else (
            "CAUTION" if passed_windows / max(total_windows, 1) >= 0.5 else "REJECT"
        ),
    }

    return {
        "symbol": req.symbol,
        "timeframe": req.timeframe,
        "train_months": req.train_months,
        "test_months": req.test_months,
        "windows": window_results,
        "aggregate": aggregate,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── Monte Carlo Simulation ───────────────────────────────────────────────────

class MonteCarloRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "H1"
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    initial_capital: float = 10000
    risk_per_trade: float = 2.0
    simulations: int = 500


@bt_app.post("/backtest/monte-carlo")
async def monte_carlo_simulation(req: MonteCarloRequest):
    """Monte Carlo: shuffle trade sequence N times to estimate outcome distribution.
    Returns P10/P25/P50/P75/P90 equity outcomes + ruin probability.
    """
    config = BacktestConfig(
        symbol=req.symbol, timeframe=req.timeframe,
        start_date=req.start_date, end_date=req.end_date,
        initial_capital=req.initial_capital, risk_per_trade=req.risk_per_trade,
    )
    df = await backtester._load_data(req.symbol, req.timeframe, req.start_date, req.end_date)
    base_result = backtester.run(config, df)

    if not base_result.trades:
        raise HTTPException(status_code=422, detail="لا توجد صفقات للمحاكاة")

    pnls = [t.pnl_usd for t in base_result.trades]
    simulations = min(req.simulations, 2000)
    final_equities = []
    ruin_count = 0

    for _ in range(simulations):
        shuffled = np.random.choice(pnls, size=len(pnls), replace=True)
        equity = req.initial_capital
        ruined = False
        for pnl in shuffled:
            equity += pnl
            if equity <= req.initial_capital * 0.3:  # 70% drawdown = ruin
                ruined = True
                break
        if ruined:
            ruin_count += 1
        final_equities.append(equity)

    final_equities.sort()
    n = len(final_equities)
    percentiles = {
        "p10": round(final_equities[int(n * 0.10)], 2),
        "p25": round(final_equities[int(n * 0.25)], 2),
        "p50": round(final_equities[int(n * 0.50)], 2),
        "p75": round(final_equities[int(n * 0.75)], 2),
        "p90": round(final_equities[int(n * 0.90)], 2),
    }

    return {
        "symbol": req.symbol,
        "timeframe": req.timeframe,
        "simulations": simulations,
        "initial_capital": req.initial_capital,
        "base_result": backtester.to_dict(base_result)["stats"],
        "percentiles": percentiles,
        "ruin_probability_pct": round(ruin_count / simulations * 100, 2),
        "expected_final_equity": round(float(np.mean(final_equities)), 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@bt_app.get("/backtest/health")
async def health():
    return {"status": "healthy"}


@bt_app.get("/metrics")
async def metrics():
    return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("backtester:bt_app", host="0.0.0.0", port=8002, reload=True)
