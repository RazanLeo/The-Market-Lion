"""Full 74-school technical analysis engine with vote system."""
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Add service path for relative imports
_SVC_DIR = os.path.join(os.path.dirname(__file__), "technical_analysis_service")
if _SVC_DIR not in sys.path:
    sys.path.insert(0, _SVC_DIR)

_VOTE_DIR = os.path.join(os.path.dirname(__file__), "vote_engine_service")
if _VOTE_DIR not in sys.path:
    sys.path.insert(0, _VOTE_DIR)


class TechnicalAnalysisService:
    """Run all 74 schools + vote engine on OHLCV candle data."""

    def analyze(self, symbol: str, timeframe: str, candles: list) -> dict:
        if not candles or len(candles) < 20:
            return self._insufficient_data(symbol, timeframe)

        df = self._to_dataframe(candles)
        price = float(df["close"].iloc[-1])

        # Run all 74 schools
        school_results = self._run_all_schools(df)

        # Run vote engine
        vote = self._run_vote_engine(school_results)

        # Map signal
        signal = vote["side"].lower() if vote["side"] in ("BUY", "SELL") else "wait"

        # Calculate indicators for display
        indicators = self._quick_indicators(df)

        # Levels
        entry, sl, tp1, tp2, tp3 = self._calc_levels(df, price, signal, indicators)
        supports, resistances = self._calc_sr(df)
        trend = self._detect_trend(indicators)
        killzone = self._get_killzone()

        # Build school breakdown for frontend
        schools_display = {}
        for item in vote.get("school_breakdown", []):
            key = item["school"].lower().replace(" ", "_").replace("%", "pct").replace("+", "plus").replace("/", "_")
            schools_display[key] = {
                "name": item["school"],
                "signal": item["vote"].lower() if item["vote"] in ("BUY", "SELL") else "neutral",
                "confidence": round(item["confidence"] * 100),
                "strength": round(item["strength"] * 100),
                "weight": round(item["weight"] * 100, 2),
            }

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price": round(price, 5),
            "trend": trend,
            "confluence_score": round(vote["confluence_score"], 1),
            "signal": signal,
            "should_trade": vote["should_trade"],
            "rejection_reasons": vote["rejection_reasons"],
            "entry": entry,
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "take_profit_3": tp3,
            "buy_votes": vote["buy_votes"],
            "sell_votes": vote["sell_votes"],
            "neutral_votes": vote["neutral_votes"],
            "total_schools": vote["total_votes"],
            "top_factors": vote["top_factors"],
            "indicators": indicators,
            "schools": schools_display,
            "support_levels": supports,
            "resistance_levels": resistances,
            "killzone": killzone,
        }

    # ── Data prep ─────────────────────────────────────────────────────────────

    @staticmethod
    def _to_dataframe(candles: list) -> pd.DataFrame:
        df = pd.DataFrame(candles)
        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "volume" not in df.columns:
            df["volume"] = 0.0
        df = df.dropna(subset=["close"]).reset_index(drop=True)
        return df

    # ── Run all 74 schools ────────────────────────────────────────────────────

    def _run_all_schools(self, df: pd.DataFrame) -> list:
        try:
            from indicators import analyze_all_schools
            return analyze_all_schools(df)
        except Exception as e:
            logger.warning(f"Full school analysis failed, using fallback: {e}")
            return self._fallback_schools(df)

    def _fallback_schools(self, df: pd.DataFrame) -> list:
        """Minimal fallback using direct ta library if import fails."""
        results = []
        try:
            from indicators import (
                analyze_moving_averages, analyze_rsi, analyze_macd,
                analyze_stochastic, analyze_bollinger_bands, analyze_adx,
                analyze_ichimoku, analyze_fibonacci, analyze_price_action,
                analyze_smc,
            )
            for fn in (
                analyze_moving_averages, analyze_rsi, analyze_macd,
                analyze_stochastic, analyze_bollinger_bands, analyze_adx,
                analyze_ichimoku, analyze_fibonacci, analyze_price_action,
                analyze_smc,
            ):
                try:
                    results.append(fn(df))
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Even fallback schools failed: {e}")
        return results

    # ── Vote engine ───────────────────────────────────────────────────────────

    def _run_vote_engine(self, school_results: list) -> dict:
        try:
            from engine import run_vote_engine
            hour = datetime.now(timezone.utc).hour
            killzone = (2 <= hour < 5) or (7 <= hour < 10) or (12 <= hour < 15)
            result = run_vote_engine(
                school_results=school_results,
                fundamental_score=50.0,
                fundamental_direction="NEUTRAL",
                mtf_aligned=True,
                killzone_active=killzone,
                news_shield=False,
                drawdown_pct=0.0,
                daily_loss_pct=0.0,
                consecutive_losses=0,
            )
            return {
                "side": result.side,
                "confluence_score": result.confluence_score,
                "buy_votes": result.buy_votes,
                "sell_votes": result.sell_votes,
                "neutral_votes": result.neutral_votes,
                "total_votes": result.total_votes,
                "should_trade": result.should_trade,
                "rejection_reasons": result.rejection_reasons,
                "school_breakdown": result.school_breakdown,
                "top_factors": result.top_factors,
            }
        except Exception as e:
            logger.warning(f"Vote engine failed: {e}")
            return self._simple_vote(school_results)

    def _simple_vote(self, school_results: list) -> dict:
        """Simple majority vote fallback."""
        from dataclasses import asdict
        buy = sell = neutral = 0
        breakdown = []
        for r in school_results:
            v = getattr(r, "vote", None)
            vote_val = v.value if hasattr(v, "value") else str(v)
            if vote_val == "BUY":
                buy += 1
            elif vote_val == "SELL":
                sell += 1
            else:
                neutral += 1
            breakdown.append({
                "school": r.name,
                "vote": vote_val,
                "strength": round(getattr(r, "strength", 0.5), 3),
                "confidence": round(getattr(r, "confidence", 0.5), 3),
                "weight": 0.014,
            })
        total = buy + sell + neutral or 1
        score = (buy - sell) / total * 100
        side = "BUY" if score > 15 else ("SELL" if score < -15 else "NEUTRAL")
        return {
            "side": side,
            "confluence_score": abs(score),
            "buy_votes": buy,
            "sell_votes": sell,
            "neutral_votes": neutral,
            "total_votes": total,
            "should_trade": abs(score) >= 60,
            "rejection_reasons": [],
            "school_breakdown": breakdown,
            "top_factors": sorted(breakdown, key=lambda x: x["strength"], reverse=True)[:5],
        }

    # ── Quick indicators for display ──────────────────────────────────────────

    def _quick_indicators(self, df: pd.DataFrame) -> dict:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df.get("volume", pd.Series([0.0] * len(df)))
        price = float(close.iloc[-1])
        result = {}

        # RSI
        try:
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi_val = float(100 - 100 / (1 + rs.iloc[-1]))
            result["rsi"] = {
                "value": round(rsi_val, 2),
                "signal": "oversold" if rsi_val < 30 else ("overbought" if rsi_val > 70 else "neutral"),
            }
        except Exception:
            result["rsi"] = {"value": 50.0, "signal": "neutral"}

        # MACD
        try:
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            result["macd"] = {
                "macd": round(float(macd_line.iloc[-1]), 5),
                "signal": round(float(signal_line.iloc[-1]), 5),
                "histogram": round(float(histogram.iloc[-1]), 5),
                "signal_type": "buy" if float(histogram.iloc[-1]) > 0 else "sell",
            }
        except Exception:
            result["macd"] = {"signal_type": "neutral"}

        # EMA 20/50/200
        for period in (20, 50, 200):
            try:
                ema_val = float(close.ewm(span=period).mean().iloc[-1])
                result[f"ema_{period}"] = {
                    "value": round(ema_val, 5),
                    "signal": "buy" if price > ema_val else "sell",
                }
            except Exception:
                result[f"ema_{period}"] = {"value": 0.0, "signal": "neutral"}

        # ATR
        try:
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs(),
            ], axis=1).max(axis=1)
            atr_val = float(tr.rolling(14).mean().iloc[-1])
            result["atr"] = {"value": round(atr_val, 5)}
        except Exception:
            result["atr"] = {"value": price * 0.005}

        # Bollinger Bands
        try:
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            upper = sma20 + 2 * std20
            lower = sma20 - 2 * std20
            mid = float(sma20.iloc[-1])
            up = float(upper.iloc[-1])
            lo = float(lower.iloc[-1])
            position = (price - lo) / (up - lo) if up != lo else 0.5
            result["bollinger"] = {
                "upper": round(up, 5),
                "middle": round(mid, 5),
                "lower": round(lo, 5),
                "position": round(position, 3),
                "signal": "oversold" if position < 0.2 else ("overbought" if position > 0.8 else "neutral"),
            }
        except Exception:
            result["bollinger"] = {"signal": "neutral"}

        # Stochastic
        try:
            low14 = low.rolling(14).min()
            high14 = high.rolling(14).max()
            k = 100 * (close - low14) / (high14 - low14).replace(0, np.nan)
            d = k.rolling(3).mean()
            k_val = float(k.iloc[-1])
            d_val = float(d.iloc[-1])
            result["stochastic"] = {
                "k": round(k_val, 2),
                "d": round(d_val, 2),
                "signal": "oversold" if k_val < 20 else ("overbought" if k_val > 80 else "neutral"),
            }
        except Exception:
            result["stochastic"] = {"signal": "neutral"}

        # ADX
        try:
            plus_dm = (high.diff()).clip(lower=0)
            minus_dm = (-low.diff()).clip(lower=0)
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr14 = tr.rolling(14).mean()
            plus_di = 100 * (plus_dm.rolling(14).mean() / atr14.replace(0, np.nan))
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14.replace(0, np.nan))
            dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
            adx_val = float(dx.rolling(14).mean().iloc[-1])
            result["adx"] = {
                "value": round(adx_val, 2),
                "signal": "strong_trend" if adx_val > 25 else "weak_trend",
            }
        except Exception:
            result["adx"] = {"value": 0.0, "signal": "neutral"}

        return result

    # ── Support / Resistance ──────────────────────────────────────────────────

    def _calc_sr(self, df: pd.DataFrame) -> tuple:
        recent = df.tail(100)
        supports = sorted(recent["low"].nsmallest(3).tolist())
        resistances = sorted(recent["high"].nlargest(3).tolist())
        return [round(x, 5) for x in supports], [round(x, 5) for x in resistances]

    # ── Trade levels ──────────────────────────────────────────────────────────

    def _calc_levels(self, df, price, signal, indicators):
        atr = indicators.get("atr", {}).get("value", price * 0.005)
        if not atr:
            atr = price * 0.005
        if signal == "buy":
            return (round(price, 5), round(price - 1.5 * atr, 5),
                    round(price + 1.5 * atr, 5), round(price + 3 * atr, 5), round(price + 5 * atr, 5))
        elif signal == "sell":
            return (round(price, 5), round(price + 1.5 * atr, 5),
                    round(price - 1.5 * atr, 5), round(price - 3 * atr, 5), round(price - 5 * atr, 5))
        else:
            return (round(price, 5), round(price - 1.5 * atr, 5),
                    round(price + 1.5 * atr, 5), round(price + 3 * atr, 5), round(price + 5 * atr, 5))

    # ── Trend ─────────────────────────────────────────────────────────────────

    def _detect_trend(self, indicators: dict) -> str:
        buy = sum(1 for k in ("ema_20", "ema_50", "ema_200") if indicators.get(k, {}).get("signal") == "buy")
        if buy >= 2:
            return "bullish"
        sell = sum(1 for k in ("ema_20", "ema_50", "ema_200") if indicators.get(k, {}).get("signal") == "sell")
        if sell >= 2:
            return "bearish"
        return "neutral"

    # ── Killzone ──────────────────────────────────────────────────────────────

    def _get_killzone(self) -> Optional[str]:
        hour = datetime.now(timezone.utc).hour
        if 2 <= hour < 5:
            return "asian"
        if 7 <= hour < 10:
            return "london_open"
        if 12 <= hour < 15:
            return "new_york_open"
        return None

    # ── Insufficient data ─────────────────────────────────────────────────────

    def _insufficient_data(self, symbol: str, timeframe: str) -> dict:
        return {
            "symbol": symbol, "timeframe": timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price": 0.0, "trend": "neutral", "confluence_score": 0.0,
            "signal": "wait", "should_trade": False, "rejection_reasons": ["INSUFFICIENT_DATA"],
            "entry": 0.0, "stop_loss": 0.0,
            "take_profit_1": 0.0, "take_profit_2": 0.0, "take_profit_3": 0.0,
            "buy_votes": 0, "sell_votes": 0, "neutral_votes": 0, "total_schools": 0,
            "top_factors": [], "indicators": {}, "schools": {},
            "support_levels": [], "resistance_levels": [], "killzone": None,
            "error": "Insufficient candle data",
        }


ta_service = TechnicalAnalysisService()
