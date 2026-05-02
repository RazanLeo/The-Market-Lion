"""Technical analysis service using the `ta` library."""
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    logger.warning("ta library not available — technical analysis will use stubs")


class TechnicalAnalysisService:
    """
    Performs multi-school technical analysis on OHLCV candle data.
    All heavy computation is synchronous (CPU-bound); call via asyncio executor
    if needed from async context.
    """

    def analyze(self, symbol: str, timeframe: str, candles: list) -> dict:
        """
        Run full analysis on candle data.

        candles: list of dicts with keys: open, high, low, close, volume, time
        Returns a dict matching the API response schema.
        """
        if not candles or len(candles) < 20:
            return self._insufficient_data(symbol, timeframe)

        df = self._to_dataframe(candles)
        price = float(df["close"].iloc[-1])

        indicators = self._calculate_indicators(df)
        schools = self._analyze_schools(df, indicators, price)
        confluence_score = self._calc_confluence(schools)
        signal = self._overall_signal(confluence_score, schools)
        trend = self._detect_trend(indicators)
        entry, sl, tp1, tp2, tp3 = self._calc_levels(df, price, signal, indicators)
        supports, resistances = self._calc_sr_levels(df)
        killzone = self._get_killzone()

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price": round(price, 5),
            "trend": trend,
            "confluence_score": round(confluence_score, 4),
            "signal": signal,
            "entry": entry,
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "take_profit_3": tp3,
            "indicators": indicators,
            "schools": schools,
            "support_levels": supports,
            "resistance_levels": resistances,
            "killzone": killzone,
        }

    # ── DataFrame prep ────────────────────────────────────────────────────────

    @staticmethod
    def _to_dataframe(candles: list) -> pd.DataFrame:
        df = pd.DataFrame(candles)
        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["close"])
        df = df.reset_index(drop=True)
        return df

    # ── Indicator calculation ─────────────────────────────────────────────────

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df.get("volume", pd.Series([0] * len(df)))

        latest_close = float(close.iloc[-1])

        result: dict = {}

        # RSI
        try:
            rsi_series = ta.momentum.RSIIndicator(close, window=14).rsi()
            rsi_val = float(rsi_series.iloc[-1])
            result["rsi"] = {
                "value": round(rsi_val, 2),
                "signal": "oversold" if rsi_val < 30 else "overbought" if rsi_val > 70 else "neutral",
            }
        except Exception:
            result["rsi"] = {"value": 50.0, "signal": "neutral"}

        # MACD
        try:
            macd_ind = ta.trend.MACD(close)
            macd_val = float(macd_ind.macd().iloc[-1])
            signal_val = float(macd_ind.macd_signal().iloc[-1])
            hist = float(macd_ind.macd_diff().iloc[-1])
            result["macd"] = {
                "value": round(macd_val, 5),
                "signal_line": round(signal_val, 5),
                "histogram": round(hist, 5),
                "signal": "buy" if hist > 0 else "sell",
            }
        except Exception:
            result["macd"] = {"value": 0.0, "signal_line": 0.0, "histogram": 0.0, "signal": "neutral"}

        # EMAs
        for period in (20, 50, 200):
            try:
                ema = float(ta.trend.EMAIndicator(close, window=period).ema_indicator().iloc[-1])
                result[f"ema_{period}"] = {
                    "value": round(ema, 5),
                    "signal": "buy" if latest_close > ema else "sell",
                }
            except Exception:
                result[f"ema_{period}"] = {"value": latest_close, "signal": "neutral"}

        # Bollinger Bands
        try:
            bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
            upper = float(bb.bollinger_hband().iloc[-1])
            middle = float(bb.bollinger_mavg().iloc[-1])
            lower = float(bb.bollinger_lband().iloc[-1])
            if latest_close > upper:
                bb_signal = "sell"
            elif latest_close < lower:
                bb_signal = "buy"
            else:
                bb_signal = "neutral"
            result["bollinger"] = {
                "upper": round(upper, 5),
                "middle": round(middle, 5),
                "lower": round(lower, 5),
                "signal": bb_signal,
            }
        except Exception:
            result["bollinger"] = {"upper": 0.0, "middle": 0.0, "lower": 0.0, "signal": "neutral"}

        # ATR
        try:
            atr_val = float(ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1])
            result["atr"] = {"value": round(atr_val, 5)}
        except Exception:
            result["atr"] = {"value": 0.0}

        # Stochastic
        try:
            stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
            k = float(stoch.stoch().iloc[-1])
            d = float(stoch.stoch_signal().iloc[-1])
            stoch_signal = "oversold" if k < 20 else "overbought" if k > 80 else "neutral"
            result["stochastic"] = {"k": round(k, 2), "d": round(d, 2), "signal": stoch_signal}
        except Exception:
            result["stochastic"] = {"k": 50.0, "d": 50.0, "signal": "neutral"}

        # ADX
        try:
            adx_val = float(ta.trend.ADXIndicator(high, low, close, window=14).adx().iloc[-1])
            result["adx"] = {
                "value": round(adx_val, 2),
                "signal": "trending" if adx_val > 25 else "ranging",
            }
        except Exception:
            result["adx"] = {"value": 25.0, "signal": "ranging"}

        # Volume
        try:
            vol_current = float(volume.iloc[-1])
            vol_avg = float(volume.tail(20).mean())
            vol_signal = "above_average" if vol_current > vol_avg * 1.2 else (
                "below_average" if vol_current < vol_avg * 0.8 else "average"
            )
            result["volume"] = {
                "current": int(vol_current),
                "avg": int(vol_avg),
                "signal": vol_signal,
            }
        except Exception:
            result["volume"] = {"current": 0, "avg": 0, "signal": "average"}

        return result

    # ── Schools of analysis ───────────────────────────────────────────────────

    def _analyze_schools(self, df: pd.DataFrame, indicators: dict, price: float) -> dict:
        schools: dict = {}
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # 1. Price Action
        schools["price_action"] = self._school_price_action(df)

        # 2. Supply & Demand
        schools["supply_demand"] = self._school_supply_demand(df, price)

        # 3. Smart Money Concepts
        schools["smart_money"] = self._school_smart_money(df, price)

        # 4. Wyckoff
        schools["wyckoff"] = self._school_wyckoff(df)

        # 5. Elliott Wave (simplified)
        schools["elliott_wave"] = self._school_elliott_wave(df)

        # 6. Fibonacci
        schools["fibonacci"] = self._school_fibonacci(df, price)

        # 7. Ichimoku
        schools["ichimoku"] = self._school_ichimoku(df, price)

        # 8. Volume Profile
        schools["volume_profile"] = self._school_volume_profile(df, price)

        # 9. Candlestick Patterns
        schools["candlestick_patterns"] = self._school_candlestick_patterns(df)

        # 10. Trend Following
        schools["trend_following"] = self._school_trend_following(indicators, price)

        return schools

    def _school_price_action(self, df: pd.DataFrame) -> dict:
        """Detect basic candlestick reversal/continuation patterns."""
        if len(df) < 3:
            return {"signal": "neutral", "confidence": 0.5, "reason": "Insufficient data"}

        c0 = df.iloc[-1]  # latest
        c1 = df.iloc[-2]  # previous

        body0 = abs(c0["close"] - c0["open"])
        body1 = abs(c1["close"] - c1["open"])
        range0 = c0["high"] - c0["low"]

        # Bullish engulfing
        if (
            c1["close"] < c1["open"]
            and c0["close"] > c0["open"]
            and c0["open"] <= c1["close"]
            and c0["close"] >= c1["open"]
        ):
            return {"signal": "buy", "confidence": 0.75, "reason": "Bullish engulfing pattern"}

        # Bearish engulfing
        if (
            c1["close"] > c1["open"]
            and c0["close"] < c0["open"]
            and c0["open"] >= c1["close"]
            and c0["close"] <= c1["open"]
        ):
            return {"signal": "sell", "confidence": 0.75, "reason": "Bearish engulfing pattern"}

        # Hammer
        lower_wick = c0["open"] - c0["low"] if c0["close"] > c0["open"] else c0["close"] - c0["low"]
        upper_wick = c0["high"] - max(c0["open"], c0["close"])
        if lower_wick > 2 * body0 and upper_wick < body0 and range0 > 0:
            return {"signal": "buy", "confidence": 0.65, "reason": "Hammer pattern"}

        # Shooting star
        if upper_wick > 2 * body0 and lower_wick < body0 and range0 > 0:
            return {"signal": "sell", "confidence": 0.65, "reason": "Shooting star pattern"}

        # Momentum candle
        if c0["close"] > c0["open"] and body0 > 0.6 * range0:
            return {"signal": "buy", "confidence": 0.60, "reason": "Strong bullish momentum candle"}
        if c0["close"] < c0["open"] and body0 > 0.6 * range0:
            return {"signal": "sell", "confidence": 0.60, "reason": "Strong bearish momentum candle"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "No clear price action pattern"}

    def _school_supply_demand(self, df: pd.DataFrame, price: float) -> dict:
        """Identify supply/demand zones using swing highs/lows."""
        if len(df) < 30:
            return {"signal": "neutral", "confidence": 0.5, "reason": "Insufficient data"}

        recent = df.tail(50)
        recent_lows = recent["low"].nsmallest(5)
        recent_highs = recent["high"].nlargest(5)

        demand_zone_top = float(recent_lows.max())
        demand_zone_bottom = float(recent_lows.min())
        supply_zone_bottom = float(recent_highs.min())
        supply_zone_top = float(recent_highs.max())

        tolerance = (df["high"].tail(20).mean() - df["low"].tail(20).mean()) * 0.1

        if demand_zone_bottom <= price <= demand_zone_top + tolerance:
            return {"signal": "buy", "confidence": 0.78, "reason": f"Price in demand zone ({demand_zone_bottom:.2f}–{demand_zone_top:.2f})"}
        if supply_zone_bottom - tolerance <= price <= supply_zone_top:
            return {"signal": "sell", "confidence": 0.78, "reason": f"Price in supply zone ({supply_zone_bottom:.2f}–{supply_zone_top:.2f})"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "Price between supply and demand zones"}

    def _school_smart_money(self, df: pd.DataFrame, price: float) -> dict:
        """SMC: order blocks + break of structure."""
        if len(df) < 20:
            return {"signal": "neutral", "confidence": 0.5, "reason": "Insufficient data"}

        # Simplified: look for last bearish candle before a bullish impulse (bullish OB)
        # or last bullish candle before a bearish impulse (bearish OB)
        closes = df["close"].values
        opens = df["open"].values

        # Look for BOS (break of structure)
        recent_closes = closes[-20:]
        highest = float(np.max(recent_closes[-10:]))
        lowest = float(np.min(recent_closes[-10:]))
        prior_highest = float(np.max(recent_closes[:10]))
        prior_lowest = float(np.min(recent_closes[:10]))

        if highest > prior_highest:
            # Bullish BOS
            # Identify potential order block (last bearish candle before breakout)
            for i in range(len(df) - 5, max(len(df) - 20, 0), -1):
                if df["close"].iloc[i] < df["open"].iloc[i]:  # bearish candle
                    ob_low = float(df["low"].iloc[i])
                    ob_high = float(df["high"].iloc[i])
                    if ob_low <= price <= ob_high:
                        return {"signal": "buy", "confidence": 0.72, "reason": f"Bullish order block support ({ob_low:.2f}–{ob_high:.2f})"}
                    break
            return {"signal": "buy", "confidence": 0.65, "reason": "Bullish break of structure"}

        if lowest < prior_lowest:
            return {"signal": "sell", "confidence": 0.65, "reason": "Bearish break of structure"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "No clear structure break"}

    def _school_wyckoff(self, df: pd.DataFrame) -> dict:
        """Simplified Wyckoff phase detection."""
        if len(df) < 40:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Insufficient data"}

        close = df["close"]
        volume = df.get("volume", pd.Series([1] * len(df)))

        price_std = float(close.tail(20).std())
        price_range = float(close.tail(20).max() - close.tail(20).min())
        avg_range = float(close.std())

        # Tight range + declining volume → accumulation
        vol_trend = float(volume.tail(10).mean()) - float(volume.tail(20).head(10).mean())

        if price_range < avg_range * 0.5 and vol_trend < 0:
            return {"signal": "buy", "confidence": 0.60, "reason": "Wyckoff accumulation phase detected"}
        if price_range < avg_range * 0.5 and vol_trend > 0:
            return {"signal": "sell", "confidence": 0.55, "reason": "Wyckoff distribution phase detected"}

        # Trend
        slope = float(close.tail(20).iloc[-1] - close.tail(20).iloc[0])
        if slope > price_std:
            return {"signal": "buy", "confidence": 0.60, "reason": "Wyckoff markup phase (uptrend)"}
        if slope < -price_std:
            return {"signal": "sell", "confidence": 0.60, "reason": "Wyckoff markdown phase (downtrend)"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "Wyckoff: neutral / re-accumulation"}

    def _school_elliott_wave(self, df: pd.DataFrame) -> dict:
        """Very simplified Elliott Wave — pivot counting."""
        if len(df) < 30:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Insufficient data"}

        close = df["close"].values
        pivots = []
        for i in range(1, len(close) - 1):
            if close[i] > close[i - 1] and close[i] > close[i + 1]:
                pivots.append(("high", i, close[i]))
            elif close[i] < close[i - 1] and close[i] < close[i + 1]:
                pivots.append(("low", i, close[i]))

        if len(pivots) < 5:
            return {"signal": "neutral", "confidence": 0.50, "reason": "No clear wave structure"}

        last_pivots = pivots[-5:]
        types = [p[0] for p in last_pivots]

        # Pattern: low-high-low-high-low → potential wave 5 / C up
        if types == ["low", "high", "low", "high", "low"]:
            return {"signal": "buy", "confidence": 0.65, "reason": "Elliott Wave: potential wave 3 or 5 up"}
        if types == ["high", "low", "high", "low", "high"]:
            return {"signal": "sell", "confidence": 0.65, "reason": "Elliott Wave: potential corrective wave down"}

        # If last pivot is a low and prior was a high → impulse may resume
        if last_pivots[-1][0] == "low" and last_pivots[-2][0] == "high":
            return {"signal": "buy", "confidence": 0.60, "reason": "Elliott Wave: correction complete, impulse likely"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "Elliott Wave: wave count unclear"}

    def _school_fibonacci(self, df: pd.DataFrame, price: float) -> dict:
        """Fibonacci retracement levels."""
        if len(df) < 20:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Insufficient data"}

        recent = df.tail(60)
        swing_high = float(recent["high"].max())
        swing_low = float(recent["low"].min())
        diff = swing_high - swing_low

        if diff == 0:
            return {"signal": "neutral", "confidence": 0.50, "reason": "No price range"}

        fibs = {
            "0.236": swing_high - 0.236 * diff,
            "0.382": swing_high - 0.382 * diff,
            "0.500": swing_high - 0.500 * diff,
            "0.618": swing_high - 0.618 * diff,
            "0.786": swing_high - 0.786 * diff,
        }

        tolerance = diff * 0.02  # 2% tolerance
        for level_name, level_price in fibs.items():
            if abs(price - level_price) <= tolerance:
                # Determine direction by where price came from
                mid = (swing_high + swing_low) / 2
                direction = "buy" if price < mid else "sell"
                confidence = 0.80 if level_name == "0.618" else 0.70
                return {
                    "signal": direction,
                    "confidence": confidence,
                    "reason": f"Price at Fibonacci {level_name} retracement ({level_price:.2f})",
                }

        return {"signal": "neutral", "confidence": 0.50, "reason": "Price not at key Fibonacci level"}

    def _school_ichimoku(self, df: pd.DataFrame, price: float) -> dict:
        """Ichimoku cloud analysis."""
        if len(df) < 52:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Insufficient data for Ichimoku"}

        high = df["high"]
        low = df["low"]
        close = df["close"]

        def donchian(series_h, series_l, window):
            return (series_h.rolling(window).max() + series_l.rolling(window).min()) / 2

        tenkan = donchian(high, low, 9)
        kijun = donchian(high, low, 26)
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = donchian(high, low, 52).shift(26)

        t = float(tenkan.iloc[-1])
        k = float(kijun.iloc[-1])
        sa = float(senkou_a.iloc[-1]) if not pd.isna(senkou_a.iloc[-1]) else price
        sb = float(senkou_b.iloc[-1]) if not pd.isna(senkou_b.iloc[-1]) else price

        cloud_top = max(sa, sb)
        cloud_bottom = min(sa, sb)

        if price > cloud_top and t > k:
            return {"signal": "buy", "confidence": 0.72, "reason": "Price above Kumo cloud, Tenkan > Kijun (bullish)"}
        if price < cloud_bottom and t < k:
            return {"signal": "sell", "confidence": 0.72, "reason": "Price below Kumo cloud, Tenkan < Kijun (bearish)"}
        if cloud_bottom <= price <= cloud_top:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Price inside Kumo cloud (indecision)"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "Ichimoku: mixed signals"}

    def _school_volume_profile(self, df: pd.DataFrame, price: float) -> dict:
        """Simplified volume profile — identify high volume nodes."""
        if "volume" not in df.columns or len(df) < 20:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Volume data unavailable"}

        try:
            n_bins = 20
            price_min = float(df["low"].min())
            price_max = float(df["high"].max())
            bins = np.linspace(price_min, price_max, n_bins + 1)
            volume_by_bin = np.zeros(n_bins)

            for _, row in df.iterrows():
                for i in range(n_bins):
                    if bins[i] <= row["close"] < bins[i + 1]:
                        volume_by_bin[i] += row.get("volume", 0)
                        break

            hvn_idx = int(np.argmax(volume_by_bin))
            hvn_price = (bins[hvn_idx] + bins[hvn_idx + 1]) / 2
            tolerance = (price_max - price_min) / n_bins

            if abs(price - hvn_price) <= tolerance:
                return {"signal": "buy" if price > hvn_price else "neutral",
                        "confidence": 0.68,
                        "reason": f"Price at high volume node ({hvn_price:.2f}) — strong support/resistance"}

            if price > hvn_price:
                return {"signal": "buy", "confidence": 0.65, "reason": f"Price above HVN {hvn_price:.2f} — support below"}
            else:
                return {"signal": "sell", "confidence": 0.60, "reason": f"Price below HVN {hvn_price:.2f} — resistance above"}
        except Exception:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Volume profile calculation error"}

    def _school_candlestick_patterns(self, df: pd.DataFrame) -> dict:
        """Detect common candlestick patterns."""
        if len(df) < 3:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Insufficient data"}

        c = df.iloc[-1]
        p = df.iloc[-2]
        p2 = df.iloc[-3]

        body = abs(c["close"] - c["open"])
        upper_wick = c["high"] - max(c["open"], c["close"])
        lower_wick = min(c["open"], c["close"]) - c["low"]
        total_range = c["high"] - c["low"]

        if total_range == 0:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Doji — indecision"}

        # Doji
        if body / total_range < 0.1:
            return {"signal": "neutral", "confidence": 0.50, "reason": "Doji candle — indecision"}

        # Morning star
        if (p2["close"] < p2["open"]  # bearish
                and abs(p["close"] - p["open"]) < abs(p2["close"] - p2["open"]) * 0.3  # small body
                and c["close"] > c["open"]  # bullish
                and c["close"] > (p2["open"] + p2["close"]) / 2):
            return {"signal": "buy", "confidence": 0.80, "reason": "Morning star pattern"}

        # Evening star
        if (p2["close"] > p2["open"]
                and abs(p["close"] - p["open"]) < abs(p2["close"] - p2["open"]) * 0.3
                and c["close"] < c["open"]
                and c["close"] < (p2["open"] + p2["close"]) / 2):
            return {"signal": "sell", "confidence": 0.80, "reason": "Evening star pattern"}

        # Three white soldiers
        if (c["close"] > c["open"] > p["close"] > p["open"] > p2["close"] > p2["open"]):
            return {"signal": "buy", "confidence": 0.75, "reason": "Three white soldiers"}

        # Three black crows
        if (c["close"] < c["open"] < p["close"] < p["open"] < p2["close"] < p2["open"]):
            return {"signal": "sell", "confidence": 0.75, "reason": "Three black crows"}

        # Hammer
        if lower_wick > 2 * body and upper_wick < body * 0.5 and c["close"] > c["open"]:
            return {"signal": "buy", "confidence": 0.68, "reason": "Hammer candle"}

        # Inverted hammer / shooting star
        if upper_wick > 2 * body and lower_wick < body * 0.5:
            return {"signal": "sell", "confidence": 0.65, "reason": "Shooting star / inverted hammer"}

        direction = "buy" if c["close"] > c["open"] else "sell"
        return {"signal": direction, "confidence": 0.55, "reason": "Directional momentum candle"}

    def _school_trend_following(self, indicators: dict, price: float) -> dict:
        """Trend following based on EMA alignment."""
        ema20 = indicators.get("ema_20", {}).get("value", price)
        ema50 = indicators.get("ema_50", {}).get("value", price)
        ema200 = indicators.get("ema_200", {}).get("value", price)

        if price > ema20 > ema50 > ema200:
            return {"signal": "buy", "confidence": 0.85, "reason": "Price above all MAs — strong uptrend"}
        if price < ema20 < ema50 < ema200:
            return {"signal": "sell", "confidence": 0.85, "reason": "Price below all MAs — strong downtrend"}
        if price > ema20 > ema50:
            return {"signal": "buy", "confidence": 0.70, "reason": "Price above EMA20 & EMA50 — uptrend"}
        if price < ema20 < ema50:
            return {"signal": "sell", "confidence": 0.70, "reason": "Price below EMA20 & EMA50 — downtrend"}
        if price > ema20:
            return {"signal": "buy", "confidence": 0.55, "reason": "Price above EMA20 — mild bullish bias"}
        if price < ema20:
            return {"signal": "sell", "confidence": 0.55, "reason": "Price below EMA20 — mild bearish bias"}

        return {"signal": "neutral", "confidence": 0.50, "reason": "Price at moving averages — no clear trend"}

    # ── Aggregate logic ───────────────────────────────────────────────────────

    def _calc_confluence(self, schools: dict) -> float:
        """Weighted average of buy confidence - sell confidence."""
        buy_conf = 0.0
        sell_conf = 0.0
        count = 0
        for s in schools.values():
            sig = s.get("signal", "neutral")
            conf = s.get("confidence", 0.5)
            count += 1
            if sig == "buy":
                buy_conf += conf
            elif sig == "sell":
                sell_conf += conf

        if count == 0:
            return 0.5

        net = (buy_conf - sell_conf) / count
        # Map [-1, 1] to [0, 1]
        return round(0.5 + net * 0.5, 4)

    def _overall_signal(self, confluence_score: float, schools: dict) -> str:
        if confluence_score >= 0.65:
            return "buy"
        if confluence_score <= 0.35:
            return "sell"
        return "wait"

    def _detect_trend(self, indicators: dict) -> str:
        buy_count = sum(
            1 for k in ("ema_20", "ema_50", "ema_200")
            if indicators.get(k, {}).get("signal") == "buy"
        )
        if buy_count >= 2:
            return "bullish"
        if buy_count <= 1:
            sell_count = sum(
                1 for k in ("ema_20", "ema_50", "ema_200")
                if indicators.get(k, {}).get("signal") == "sell"
            )
            if sell_count >= 2:
                return "bearish"
        return "neutral"

    def _calc_levels(
        self, df: pd.DataFrame, price: float, signal: str, indicators: dict
    ) -> tuple:
        atr = indicators.get("atr", {}).get("value", price * 0.005)
        if atr == 0:
            atr = price * 0.005

        if signal == "buy":
            entry = round(price, 5)
            sl = round(price - 1.5 * atr, 5)
            tp1 = round(price + 1.5 * atr, 5)
            tp2 = round(price + 3.0 * atr, 5)
            tp3 = round(price + 5.0 * atr, 5)
        elif signal == "sell":
            entry = round(price, 5)
            sl = round(price + 1.5 * atr, 5)
            tp1 = round(price - 1.5 * atr, 5)
            tp2 = round(price - 3.0 * atr, 5)
            tp3 = round(price - 5.0 * atr, 5)
        else:
            entry = round(price, 5)
            sl = round(price - 1.5 * atr, 5)
            tp1 = round(price + 1.5 * atr, 5)
            tp2 = round(price + 3.0 * atr, 5)
            tp3 = round(price + 5.0 * atr, 5)

        return entry, sl, tp1, tp2, tp3

    def _calc_sr_levels(self, df: pd.DataFrame) -> tuple[list, list]:
        recent = df.tail(100)
        lows = sorted(recent["low"].nsmallest(3).tolist())
        highs = sorted(recent["high"].nlargest(3).tolist())
        return [round(x, 5) for x in lows], [round(x, 5) for x in highs]

    def _get_killzone(self) -> Optional[str]:
        """Return current forex killzone based on UTC hour."""
        hour = datetime.now(timezone.utc).hour
        if 2 <= hour < 5:
            return "asian"
        if 7 <= hour < 10:
            return "london_open"
        if 12 <= hour < 15:
            return "new_york_open"
        return None

    def _insufficient_data(self, symbol: str, timeframe: str) -> dict:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price": 0.0,
            "trend": "neutral",
            "confluence_score": 0.5,
            "signal": "wait",
            "entry": 0.0,
            "stop_loss": 0.0,
            "take_profit_1": 0.0,
            "take_profit_2": 0.0,
            "take_profit_3": 0.0,
            "indicators": {},
            "schools": {},
            "support_levels": [],
            "resistance_levels": [],
            "killzone": None,
            "error": "Insufficient candle data",
        }


# Module-level singleton
ta_service = TechnicalAnalysisService()
