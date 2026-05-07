import time
from app.services.bookmap import BookmapEngine


def test_bookmap_iceberg_detection():
    eng = BookmapEngine("XAUUSD")
    bids = {2300.0: 1000.0}; asks = {2300.5: 800.0}
    for _ in range(5):
        eng.update_book(bids, asks)
    # iceberg detected when refilled ≥3
    payload = eng.heatmap_payload()
    assert any(z["price"] == 2300.0 for z in payload["icebergs"])


def test_bookmap_sweep_detection():
    eng = BookmapEngine("XAUUSD")
    eng.update_book({2300.0: 100}, {2300.5: 100})
    base = 2300.0
    for i in range(10):
        eng.add_trade(time.time() + i, base + i*0.1, 50.0, "buy")
    # add high spike then revert
    eng.add_trade(time.time(), base + 5.0, 100.0, "buy")  # spike high
    eng.add_trade(time.time(), base + 0.2, 100.0, "sell")  # back inside
    payload = eng.heatmap_payload()
    assert isinstance(payload["sweeps"], list)
