"""Smoke tests for school analyzers (both packs)."""
from app.workers.analyzers import schools_pack as s1, schools_pack_2 as s2


def test_schools_pack_1(ohlcv):
    fns = [
        s1.smc_analyzer, s1.wyckoff_analyzer, s1.fib_retracement_analyzer,
        s1.elliott_basic_analyzer, s1.supply_demand_analyzer, s1.killzone_analyzer,
        s1.power_of_three_analyzer, s1.ote_analyzer, s1.pairs_zscore_analyzer,
    ]
    for fn in fns:
        r = fn(ohlcv); assert r.result in ("buy", "sell", "neutral")


def test_schools_pack_2(ohlcv):
    fns = [
        s2.candlestick_aggregator, s2.dow_theory, s2.naked_trading, s2.vsa,
        s2.wyckoff_full, s2.elliott_full, s2.harmonic_patterns, s2.andrews_pitchfork,
        s2.point_and_figure, s2.darvas_box, s2.weinstein_stage, s2.williams_chaos,
        s2.turtle_trading, s2.hurst_cycles, s2.demark_sequential, s2.kondratiev,
        s2.market_profile, s2.gann_angles, s2.sacred_geometry, s2.renko_signal,
        s2.heikin_ashi, s2.kagi_signal, s2.three_line_break, s2.range_bars,
        s2.tick_chart, s2.quant_stat_arb, s2.mean_reversion, s2.mansfield_rs,
        s2.canslim, s2.momentum_driehaus, s2.lion_smart_money_flow,
        s2.lion_overflow, s2.lion_hyperwave, s2.lion_reversal_signals,
        s2.lion_arc_breakout, s2.lion_whale_tracker, s2.lion_cloud_rsi,
        s2.lion_confluence_meter, s2.lion_inertial_stoch, s2.lion_bsl_ssl_map,
        s2.fib_time_zones,
    ]
    for fn in fns:
        r = fn(ohlcv); assert r.result in ("buy", "sell", "neutral")
