"""Analyzer registry."""
from .indicators_pack import (
    rsi_analyzer, ema_stack_analyzer, macd_analyzer, vwap_analyzer,
    bollinger_analyzer, atr_volatility_analyzer, adx_analyzer,
)
from .schools_pack import (
    smc_analyzer, wyckoff_analyzer, fib_retracement_analyzer,
    elliott_basic_analyzer, supply_demand_analyzer, killzone_analyzer,
    power_of_three_analyzer, ote_analyzer, pairs_zscore_analyzer,
)
from .flow_pack import (
    volume_profile_analyzer, order_flow_basic_analyzer, bookmap_basic_analyzer,
)
from .fundamental_pack import news_sentiment_analyzer, fomc_nfp_impact_analyzer

ALL_ANALYZERS = {
    # indicators
    "rsi": rsi_analyzer,
    "ema_stack": ema_stack_analyzer,
    "macd": macd_analyzer,
    "vwap": vwap_analyzer,
    "bollinger": bollinger_analyzer,
    "atr_vol": atr_volatility_analyzer,
    "adx": adx_analyzer,
    # schools
    "smc": smc_analyzer,
    "wyckoff": wyckoff_analyzer,
    "fib_retracement": fib_retracement_analyzer,
    "elliott": elliott_basic_analyzer,
    "supply_demand": supply_demand_analyzer,
    "killzone": killzone_analyzer,
    "power_of_three": power_of_three_analyzer,
    "ote_61_8": ote_analyzer,
    "pairs_zscore": pairs_zscore_analyzer,
    # flow
    "volume_profile": volume_profile_analyzer,
    "order_flow": order_flow_basic_analyzer,
    "bookmap": bookmap_basic_analyzer,
    # fundamental
    "news_sentiment": news_sentiment_analyzer,
    "fomc_nfp": fomc_nfp_impact_analyzer,
}
