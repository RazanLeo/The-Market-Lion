"""Asset model for The Market Lion."""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class AssetClass(str, Enum):
    FOREX = "FOREX"
    METALS = "METALS"
    OIL_ENERGY = "OIL_ENERGY"
    INDICES = "INDICES"
    STOCKS_US = "STOCKS_US"
    STOCKS_SAUDI = "STOCKS_SAUDI"
    STOCKS_GLOBAL = "STOCKS_GLOBAL"
    CRYPTO = "CRYPTO"
    BONDS = "BONDS"
    SOFT_COMMODITIES = "SOFT_COMMODITIES"


class Asset(BaseModel):
    symbol: str
    name_ar: str
    name_en: str
    asset_class: AssetClass
    base_currency: str
    quote_currency: str
    pip_value: float = 0.0001
    min_lot: float = 0.01
    max_lot: float = 1000.0
    leverage: float = 100.0
    spread_typical: float = 0.0
    swap_long: float = 0.0
    swap_short: float = 0.0
    trading_hours: str = "24/5"
    is_active: bool = True
    priority: int = 1


PHASE_1_ASSETS = [
    Asset(symbol="XAUUSD", name_ar="الذهب / الدولار", name_en="Gold / USD",
          asset_class=AssetClass.METALS, base_currency="XAU", quote_currency="USD",
          pip_value=0.01, spread_typical=0.3, priority=1),
    Asset(symbol="USOIL", name_ar="النفط الخام الأمريكي", name_en="WTI Crude Oil",
          asset_class=AssetClass.OIL_ENERGY, base_currency="WTI", quote_currency="USD",
          pip_value=0.01, spread_typical=0.03, priority=2),
    Asset(symbol="XBRUSD", name_ar="خام برنت", name_en="Brent Crude Oil",
          asset_class=AssetClass.OIL_ENERGY, base_currency="XBR", quote_currency="USD",
          pip_value=0.01, spread_typical=0.03, priority=3),
    Asset(symbol="EURUSD", name_ar="اليورو / الدولار", name_en="EUR/USD",
          asset_class=AssetClass.FOREX, base_currency="EUR", quote_currency="USD",
          pip_value=0.0001, spread_typical=0.8, priority=4),
    Asset(symbol="GBPUSD", name_ar="الجنيه / الدولار", name_en="GBP/USD",
          asset_class=AssetClass.FOREX, base_currency="GBP", quote_currency="USD",
          pip_value=0.0001, spread_typical=1.0, priority=5),
    Asset(symbol="USDJPY", name_ar="الدولار / الين", name_en="USD/JPY",
          asset_class=AssetClass.FOREX, base_currency="USD", quote_currency="JPY",
          pip_value=0.01, spread_typical=0.7, priority=6),
    Asset(symbol="AUDUSD", name_ar="الأسترالي / الدولار", name_en="AUD/USD",
          asset_class=AssetClass.FOREX, base_currency="AUD", quote_currency="USD",
          pip_value=0.0001, spread_typical=0.9, priority=7),
    Asset(symbol="USDCAD", name_ar="الدولار / الكندي", name_en="USD/CAD",
          asset_class=AssetClass.FOREX, base_currency="USD", quote_currency="CAD",
          pip_value=0.0001, spread_typical=1.1, priority=8),
    Asset(symbol="USDCHF", name_ar="الدولار / الفرنك", name_en="USD/CHF",
          asset_class=AssetClass.FOREX, base_currency="USD", quote_currency="CHF",
          pip_value=0.0001, spread_typical=0.9, priority=9),
    Asset(symbol="NZDUSD", name_ar="النيوزيلندي / الدولار", name_en="NZD/USD",
          asset_class=AssetClass.FOREX, base_currency="NZD", quote_currency="USD",
          pip_value=0.0001, spread_typical=1.3, priority=10),
]
