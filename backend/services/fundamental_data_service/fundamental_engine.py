"""Fundamental Analysis Engine - The Market Lion."""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class NewsImpact(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FundamentalBias(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    NEUTRAL = "NEUTRAL"


@dataclass
class EconomicEvent:
    title: str
    currency: str
    impact: NewsImpact
    actual: Optional[float]
    forecast: Optional[float]
    previous: Optional[float]
    timestamp: datetime
    source: str
    affected_assets: List[str]
    sentiment_score: float  # -100 to +100
    bias: FundamentalBias
    detail: str = ""


@dataclass
class FundamentalReport:
    asset: str
    overall_score: float      # 0-100
    direction: FundamentalBias
    confidence: float          # 0-1
    events_today: List[EconomicEvent]
    market_regime: str
    risk_sentiment: str
    dxy_bias: FundamentalBias
    gold_specific_bias: FundamentalBias
    oil_specific_bias: FundamentalBias
    top_drivers: List[str]
    news_shield_active: bool
    next_high_impact: Optional[datetime]
    generated_at: datetime


class FundamentalEngine:
    """Pulls and scores fundamental data from free sources."""

    FOREX_FACTORY_CAL_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
    ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
    TRADING_ECON_BASE = "https://api.tradingeconomics.com"

    GOLD_DRIVERS = [
        "Real Yields (TIPS 10Y)", "DXY Direction", "Inflation (CPI/PCE)",
        "FOMC Policy", "Geopolitical Risk", "ETF Flows", "COT Positioning",
        "Central Bank Buying", "Risk Sentiment (VIX)", "Gold/Silver Ratio",
    ]

    OIL_DRIVERS = [
        "EIA Crude Inventories", "OPEC+ Production", "Baker Hughes Rig Count",
        "USD Direction", "Global Demand (PMI/GDP)", "Refinery Utilization",
        "Cushing Storage", "API Report", "Geopolitical Risk", "Seasonal Demand",
    ]

    FOREX_DRIVERS = [
        "Central Bank Policy Divergence", "Interest Rate Differential",
        "Inflation Differential", "GDP Growth Differential",
        "Trade Balance", "Current Account", "PMI Comparison",
        "Employment Reports", "Consumer Sentiment", "Political Stability",
    ]

    HIGH_IMPACT_KEYWORDS = [
        "NFP", "Non-Farm Payroll", "FOMC", "Fed Rate Decision",
        "CPI", "Consumer Price Index", "ECB Rate", "BOE Rate",
        "GDP", "Unemployment Rate", "Retail Sales",
    ]

    async def fetch_forex_factory_calendar(self) -> List[EconomicEvent]:
        events = []
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(self.FOREX_FACTORY_CAL_URL) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        for item in data:
                            impact = NewsImpact.HIGH if item.get("impact") == "High" else (
                                NewsImpact.MEDIUM if item.get("impact") == "Medium" else NewsImpact.LOW
                            )
                            actual_raw = item.get("actual", "")
                            forecast_raw = item.get("forecast", "")
                            previous_raw = item.get("previous", "")

                            def parse_num(val):
                                if not val:
                                    return None
                                try:
                                    return float(str(val).replace("%", "").replace("K", "000").replace("M", "000000").strip())
                                except:
                                    return None

                            actual = parse_num(actual_raw)
                            forecast = parse_num(forecast_raw)
                            previous = parse_num(previous_raw)

                            score = self._score_event(actual, forecast, previous, item.get("title", ""))
                            bias = FundamentalBias.BULL if score > 10 else (FundamentalBias.BEAR if score < -10 else FundamentalBias.NEUTRAL)

                            try:
                                ts = datetime.fromisoformat(item.get("date", "").replace("Z", "+00:00"))
                            except:
                                ts = datetime.now(timezone.utc)

                            events.append(EconomicEvent(
                                title=item.get("title", "Unknown"),
                                currency=item.get("currency", "USD"),
                                impact=impact,
                                actual=actual,
                                forecast=forecast,
                                previous=previous,
                                timestamp=ts,
                                source="ForexFactory",
                                affected_assets=self._map_currency_to_assets(item.get("currency", "USD")),
                                sentiment_score=score,
                                bias=bias,
                                detail=f"Previous: {previous_raw}, Forecast: {forecast_raw}, Actual: {actual_raw}",
                            ))
        except Exception as e:
            pass
        return events

    def _score_event(self, actual, forecast, previous, title: str) -> float:
        if actual is None:
            return 0.0
        score = 0.0
        if forecast is not None and forecast != 0:
            deviation_pct = ((actual - forecast) / abs(forecast)) * 100
            score += deviation_pct * 2
        if previous is not None and previous != 0:
            trend = ((actual - previous) / abs(previous)) * 100
            score += trend * 0.5

        title_lower = title.lower()
        if any(k.lower() in title_lower for k in ["unemployment", "jobless", "inflation", "cpi"]):
            # Inverse: lower unemployment is good
            if "unemployment" in title_lower or "jobless" in title_lower:
                score = -score
        return max(-100.0, min(100.0, score))

    def _map_currency_to_assets(self, currency: str) -> List[str]:
        mapping = {
            "USD": ["XAUUSD", "USOIL", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF"],
            "EUR": ["EURUSD", "EURGBP", "EURJPY"],
            "GBP": ["GBPUSD", "EURGBP", "GBPJPY"],
            "JPY": ["USDJPY", "EURJPY", "GBPJPY"],
            "CAD": ["USDCAD", "CADJPY"],
            "AUD": ["AUDUSD", "AUDCAD"],
            "NZD": ["NZDUSD", "AUDNZD"],
            "CHF": ["USDCHF", "EURCHF"],
        }
        return mapping.get(currency, ["XAUUSD"])

    def calculate_fundamental_score(
        self,
        events: List[EconomicEvent],
        asset: str,
        timeframe: str = "H1",
    ) -> FundamentalReport:
        relevant = [e for e in events if asset in e.affected_assets]
        if not relevant:
            return FundamentalReport(
                asset=asset, overall_score=50.0, direction=FundamentalBias.NEUTRAL,
                confidence=0.3, events_today=[], market_regime="NEUTRAL",
                risk_sentiment="NEUTRAL", dxy_bias=FundamentalBias.NEUTRAL,
                gold_specific_bias=FundamentalBias.NEUTRAL, oil_specific_bias=FundamentalBias.NEUTRAL,
                top_drivers=[], news_shield_active=False, next_high_impact=None,
                generated_at=datetime.now(timezone.utc),
            )

        weights = {NewsImpact.HIGH: 3.0, NewsImpact.MEDIUM: 1.5, NewsImpact.LOW: 0.5}
        weighted_score = 0.0
        total_weight = 0.0
        for event in relevant:
            w = weights[event.impact]
            weighted_score += event.sentiment_score * w
            total_weight += w

        avg_score = weighted_score / total_weight if total_weight > 0 else 0.0
        normalized_score = (avg_score + 100) / 2

        if avg_score > 15:
            direction = FundamentalBias.BULL
        elif avg_score < -15:
            direction = FundamentalBias.BEAR
        else:
            direction = FundamentalBias.NEUTRAL

        high_impact_soon = any(
            e.impact == NewsImpact.HIGH and
            0 <= (e.timestamp - datetime.now(timezone.utc)).total_seconds() <= 1800
            for e in relevant
        )

        next_hi = next((e.timestamp for e in sorted(relevant, key=lambda x: x.timestamp)
                        if e.impact == NewsImpact.HIGH and e.timestamp > datetime.now(timezone.utc)), None)

        confidence = min(1.0, len(relevant) / 10 + 0.3)

        top_drivers = list(set(e.title for e in sorted(relevant, key=lambda x: abs(x.sentiment_score), reverse=True)[:5]))

        return FundamentalReport(
            asset=asset,
            overall_score=round(normalized_score, 2),
            direction=direction,
            confidence=round(confidence, 3),
            events_today=relevant,
            market_regime="RISK_OFF" if direction == FundamentalBias.BEAR else "RISK_ON",
            risk_sentiment="BEARISH" if direction == FundamentalBias.BEAR else "BULLISH",
            dxy_bias=FundamentalBias.BULL if direction == FundamentalBias.BEAR else FundamentalBias.BEAR,
            gold_specific_bias=direction,
            oil_specific_bias=direction,
            top_drivers=top_drivers,
            news_shield_active=high_impact_soon,
            next_high_impact=next_hi,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_full_report(self, asset: str) -> FundamentalReport:
        events = await self.fetch_forex_factory_calendar()
        return self.calculate_fundamental_score(events, asset)
