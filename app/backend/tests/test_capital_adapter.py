"""Capital.com adapter tests — mocks httpx so we can verify request shape.

Validates that the adapter:
  • Uses direct Capital.com REST endpoints (no MetaAPI middleware)
  • Builds correct auth headers (X-CAP-API-KEY, CST, X-SECURITY-TOKEN)
  • Posts /api/v1/session and parses CST + X-SECURITY-TOKEN headers
  • Accepts open_market with correct body keys (epic, direction, size, stopLevel, profitLevel)
"""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


def test_no_metaapi_dependency():
    """Verify adapter file uses only direct Capital.com — no MetaAPI."""
    from app.services.brokers import capital
    src = open(capital.__file__).read().lower()
    assert "metaapi" not in src
    assert "metatrader" not in src
    assert "api-capital.backend-capital" in (src + open(capital.__file__.replace("brokers/capital.py", "../core/config.py")).read().lower())


def _patched_adapter():
    """Build an adapter with httpx.AsyncClient swapped for a MagicMock to avoid network."""
    with patch("app.services.brokers.capital.httpx.AsyncClient", return_value=MagicMock()):
        from app.services.brokers.capital import CapitalAdapter
        return CapitalAdapter(demo=True)


@pytest.mark.asyncio
async def test_create_session_parses_tokens_from_headers():
    a = _patched_adapter()
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.headers = {"CST": "cst-token-abc", "X-SECURITY-TOKEN": "sec-token-xyz"}
    fake_resp.json.return_value = {"accounts": [{"accountId": "ACC001", "preferred": True}]}
    fake_resp.raise_for_status = MagicMock()
    a._client.post = AsyncMock(return_value=fake_resp)

    body = await a.create_session(api_key="k", identifier="u@x.com", password="p")
    assert a._cst == "cst-token-abc"
    assert a._x_sec == "sec-token-xyz"
    assert a._account_id == "ACC001"
    # request was made to /api/v1/session
    args, kwargs = a._client.post.call_args
    assert args[0] == "/api/v1/session"
    assert kwargs["headers"]["X-CAP-API-KEY"] == "k"


@pytest.mark.asyncio
async def test_headers_include_auth_tokens():
    a = _patched_adapter()
    a._cst = "abc"; a._x_sec = "xyz"; a._api_key = "key1"
    h = a._headers()
    assert h["CST"] == "abc"
    assert h["X-SECURITY-TOKEN"] == "xyz"
    assert h["X-CAP-API-KEY"] == "key1"
    assert h["Content-Type"] == "application/json"


def test_symbol_to_epic_returns_string():
    from app.services.brokers.capital import CapitalAdapter
    epic = CapitalAdapter._symbol_to_epic("XAUUSD")
    assert isinstance(epic, str) and len(epic) > 0


@pytest.mark.asyncio
async def test_open_market_posts_correct_body():
    a = _patched_adapter()
    a._cst = "x"; a._x_sec = "y"; a._api_key = "k"
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"dealReference": "DR123"}
    fake_resp.raise_for_status = MagicMock()
    a._client.post = AsyncMock(return_value=fake_resp)

    res = await a.open_market(symbol="XAUUSD", side="buy", lot=0.01, sl=2300, tp=2400)
    args, kwargs = a._client.post.call_args
    assert args[0] == "/api/v1/positions"
    body = kwargs["json"]
    assert body["direction"] == "BUY"
    assert body["size"] == 0.01
    assert "epic" in body
    assert body["stopLevel"] == 2300
    assert body["profitLevel"] == 2400


@pytest.mark.asyncio
async def test_account_info_parses_balance():
    a = _patched_adapter()
    a._account_id = "ACC001"; a._cst = "x"; a._x_sec = "y"; a._api_key = "k"
    fake_resp = MagicMock()
    fake_resp.json.return_value = {"accounts": [{
        "accountId": "ACC001", "currency": "USD",
        "balance": {"balance": 10000.0, "available": 9500.0, "deposit": 10000.0, "profitLoss": -500.0},
        "accountType": "CFD"
    }]}
    fake_resp.raise_for_status = MagicMock()
    a._client.get = AsyncMock(return_value=fake_resp)
    info = await a.account_info()
    assert info["account_id"] == "ACC001"
    assert info["balance"] == 10000.0
    assert info["available"] == 9500.0
    assert info["currency"] == "USD"
