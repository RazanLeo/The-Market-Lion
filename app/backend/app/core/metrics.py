"""Prometheus metrics — exposed at /metrics."""
from prometheus_client import Counter, Histogram, Gauge

http_requests_total = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
http_request_duration_seconds = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "path"])

marketlion_confluence_updates_total = Counter("marketlion_confluence_updates_total", "Confluence recompute count")
marketlion_trades_opened_total = Counter("marketlion_trades_opened_total", "Trades opened")
marketlion_trades_closed_total = Counter("marketlion_trades_closed_total", "Trades closed")
marketlion_active_users = Gauge("marketlion_active_users", "Currently active users (last 5min)")
marketlion_win_rate_50 = Gauge("marketlion_win_rate_50", "Win-rate of last 50 closed trades (%)")
