"""5-Layer Risk Management Engine - The Market Lion."""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 2.0
    max_risk_per_trade_pct: float = 10.0
    min_rr_ratio: float = 3.0
    max_open_trades: int = 3
    max_correlation: float = 0.7
    max_heat_pct: float = 6.0
    max_daily_loss_pct: float = 3.0
    max_weekly_loss_pct: float = 10.0
    max_monthly_loss_pct: float = 20.0
    circuit_breaker_3_losses: bool = True
    news_pause_minutes_before: int = 30
    news_pause_minutes_after: int = 15
    min_rr_tp1: float = 1.0
    min_rr_tp2: float = 2.0
    min_rr_tp3: float = 3.0


@dataclass
class PositionSize:
    lot_size: float
    risk_amount: float
    risk_pct: float
    sl_pips: float
    pip_value: float
    margin_required: float
    leverage: float


@dataclass
class TradeValidation:
    is_valid: bool
    rejection_reasons: list
    sl_price: float
    tp1_price: float
    tp2_price: float
    tp3_price: float
    lot_size: float
    risk_pct: float
    rr_1: float
    rr_2: float
    rr_3: float
    margin_required: float
    commission_estimated: float
    swap_per_day: float
    circuit_breaker_level: int


class RiskManager:
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    def calculate_atr_sl(self, atr: float, side: str, entry: float, multiplier: float = 1.5) -> float:
        """Smart SL based on ATR - minimum 1.5x ATR from entry."""
        offset = atr * max(multiplier, 1.5)
        if side == "BUY":
            return round(entry - offset, 5)
        return round(entry + offset, 5)

    def calculate_structure_sl(self, swing_high: float, swing_low: float, side: str, buffer: float = 0.0001) -> float:
        """SL beyond last swing high/low for structure-based entry."""
        if side == "BUY":
            return round(swing_low - buffer, 5)
        return round(swing_high + buffer, 5)

    def smart_stop_loss(self, entry: float, side: str, atr: float,
                        swing_high: float, swing_low: float) -> float:
        atr_sl = self.calculate_atr_sl(atr, side, entry)
        struct_sl = self.calculate_structure_sl(swing_high, swing_low, side)
        if side == "BUY":
            return min(atr_sl, struct_sl)
        return max(atr_sl, struct_sl)

    def calculate_take_profits(self, entry: float, sl: float, side: str) -> Tuple[float, float, float]:
        risk = abs(entry - sl)
        if side == "BUY":
            tp1 = round(entry + risk * 1.0, 5)
            tp2 = round(entry + risk * 2.0, 5)
            tp3 = round(entry + risk * 3.0, 5)
        else:
            tp1 = round(entry - risk * 1.0, 5)
            tp2 = round(entry - risk * 2.0, 5)
            tp3 = round(entry - risk * 3.0, 5)
        return tp1, tp2, tp3

    def position_size(
        self,
        capital: float,
        entry: float,
        sl: float,
        pip_value: float,
        leverage: float = 100.0,
    ) -> PositionSize:
        risk_amount = capital * (self.config.risk_per_trade_pct / 100)
        sl_distance = abs(entry - sl)
        sl_pips = sl_distance / pip_value
        if sl_pips <= 0:
            sl_pips = 1

        lot_size = risk_amount / (sl_pips * pip_value * 10)
        lot_size = max(0.01, round(lot_size, 2))
        margin_required = (lot_size * 100_000 * entry) / leverage

        return PositionSize(
            lot_size=lot_size,
            risk_amount=round(risk_amount, 2),
            risk_pct=self.config.risk_per_trade_pct,
            sl_pips=round(sl_pips, 1),
            pip_value=pip_value,
            margin_required=round(margin_required, 2),
            leverage=leverage,
        )

    def check_circuit_breaker(
        self,
        daily_loss_pct: float,
        weekly_loss_pct: float,
        monthly_loss_pct: float,
        drawdown_pct: float,
        consecutive_losses: int,
    ) -> Tuple[int, list]:
        reasons = []
        level = 0
        if consecutive_losses >= 3:
            level = max(level, 1)
            reasons.append(f"3 consecutive losses - 2hr pause")
        if daily_loss_pct >= self.config.max_daily_loss_pct:
            level = max(level, 2)
            reasons.append(f"Daily loss {daily_loss_pct:.1f}% >= {self.config.max_daily_loss_pct}%")
        if drawdown_pct >= 10:
            level = max(level, 3)
            reasons.append(f"Drawdown {drawdown_pct:.1f}% >= 10% - reduced size")
        if drawdown_pct >= 20:
            level = max(level, 4)
            reasons.append(f"Drawdown {drawdown_pct:.1f}% >= 20% - FULL STOP")
        if drawdown_pct >= 30:
            level = max(level, 5)
            reasons.append(f"Drawdown {drawdown_pct:.1f}% >= 30% - PERMANENT STOP")
        return level, reasons

    def validate_trade(
        self,
        capital: float,
        entry: float,
        sl: float,
        side: str,
        atr: float,
        pip_value: float,
        swing_high: float,
        swing_low: float,
        open_trades_count: int,
        daily_loss_pct: float,
        drawdown_pct: float,
        consecutive_losses: int,
        news_shield_active: bool,
        leverage: float = 100.0,
        spread: float = 0.0,
        swap_per_day: float = 0.0,
        commission: float = 0.0,
    ) -> TradeValidation:
        rejection_reasons = []

        # Layer 1: Circuit breaker
        cb_level, cb_reasons = self.check_circuit_breaker(
            daily_loss_pct, 0, 0, drawdown_pct, consecutive_losses
        )
        if cb_level >= 2:
            rejection_reasons.extend(cb_reasons)

        # Layer 2: News shield
        if news_shield_active:
            rejection_reasons.append("NEWS_SHIELD_ACTIVE")

        # Layer 3: Max open trades
        if open_trades_count >= self.config.max_open_trades:
            rejection_reasons.append(f"MAX_TRADES_{self.config.max_open_trades}_REACHED")

        # Layer 4: SL must be >= 1.5x ATR
        sl_distance = abs(entry - sl)
        min_sl = atr * 1.5
        if sl_distance < min_sl:
            sl = self.calculate_atr_sl(atr, side, entry, 1.5)
            rejection_reasons.append("SL_ADJUSTED_TO_ATR_1_5X")

        # Layer 5: Position sizing
        pos = self.position_size(capital, entry, sl, pip_value, leverage)

        # Calculate TPs
        tp1, tp2, tp3 = self.calculate_take_profits(entry, sl, side)

        # Risk:Reward ratios
        risk = abs(entry - sl)
        reward1 = abs(tp1 - entry)
        reward2 = abs(tp2 - entry)
        reward3 = abs(tp3 - entry)
        rr1 = safe_div(reward1, risk)
        rr2 = safe_div(reward2, risk)
        rr3 = safe_div(reward3, risk)

        if rr3 < self.config.min_rr_ratio:
            rejection_reasons.append(f"RR_BELOW_MIN_{self.config.min_rr_ratio}")

        is_valid = len(rejection_reasons) == 0 or (
            len(rejection_reasons) == 1 and "SL_ADJUSTED" in rejection_reasons[0]
        )
        if "SL_ADJUSTED_TO_ATR_1_5X" in rejection_reasons:
            rejection_reasons.remove("SL_ADJUSTED_TO_ATR_1_5X")

        return TradeValidation(
            is_valid=is_valid,
            rejection_reasons=rejection_reasons,
            sl_price=round(sl, 5),
            tp1_price=round(tp1, 5),
            tp2_price=round(tp2, 5),
            tp3_price=round(tp3, 5),
            lot_size=pos.lot_size,
            risk_pct=pos.risk_pct,
            rr_1=round(rr1, 2),
            rr_2=round(rr2, 2),
            rr_3=round(rr3, 2),
            margin_required=pos.margin_required,
            commission_estimated=commission,
            swap_per_day=swap_per_day,
            circuit_breaker_level=cb_level,
        )

    def check_pyramiding_allowed(
        self,
        parent_pnl_pct: float,
        parent_at_breakeven: bool,
        new_confluence_score: float,
        pyramid_count: int,
        new_lot_fraction: float = 0.5,
    ) -> Tuple[bool, list]:
        reasons = []
        if not parent_at_breakeven:
            reasons.append("PARENT_NOT_AT_BREAKEVEN")
        if parent_pnl_pct <= 0:
            reasons.append("PARENT_NOT_PROFITABLE")
        if new_confluence_score < 85.0:
            reasons.append(f"PYRAMID_NEEDS_85_PCT_CONFLUENCE (got {new_confluence_score:.1f}%)")
        if pyramid_count >= 3:
            reasons.append("MAX_3_PYRAMIDS_REACHED")
        if new_lot_fraction > 0.5:
            reasons.append("PYRAMID_LOT_EXCEEDS_50PCT")
        return len(reasons) == 0, reasons


def safe_div(a, b, default=0.0):
    return a / b if b != 0 else default
