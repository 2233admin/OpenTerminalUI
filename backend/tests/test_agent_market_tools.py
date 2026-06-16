import pytest
import backend.agent.tools.market_tools as mt
from backend.agent.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_screen_stocks_calls_engine(monkeypatch):
    captured = {}

    class FakeEngine:
        def run(self, config):
            captured["query"] = config.query
            captured["limit"] = config.limit
            return {"rows": [{"ticker": "AAPL", "pe_ratio": 18}], "total": 1}

    monkeypatch.setattr(mt, "ScreenerEngine", lambda: FakeEngine())
    out = await mt.screen_stocks({"query": "pe_ratio < 20", "limit": 5})
    assert captured["query"] == "pe_ratio < 20"
    assert captured["limit"] == 5
    assert out["rows"][0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_get_stock_snapshot(monkeypatch):
    async def fake_fetcher():
        class F:
            async def fetch_stock_snapshot(self, sym):
                return {"company_name": "Apple", "last_price": 200.0, "symbol": sym}
        return F()

    monkeypatch.setattr(mt, "get_unified_fetcher", fake_fetcher)
    out = await mt.get_stock_snapshot({"ticker": "aapl"})
    assert out["symbol"] == "AAPL"
    assert out["last_price"] == 200.0


@pytest.mark.asyncio
async def test_compare_stocks(monkeypatch):
    async def fake_fetcher():
        class F:
            async def fetch_stock_snapshot(self, sym):
                return {"symbol": sym, "pe_ratio": 10 if sym == "A" else 20}
        return F()

    monkeypatch.setattr(mt, "get_unified_fetcher", fake_fetcher)
    out = await mt.compare_stocks({"tickers": ["A", "B"], "metrics": ["pe_ratio"]})
    assert len(out["rows"]) == 2
    assert out["rows"][0]["pe_ratio"] == 10


def test_build_default_registry_has_read_tools():
    reg = mt.build_default_registry()
    names = {d.name for d in reg.tool_defs()}
    assert {"screen_stocks", "get_stock_snapshot", "compare_stocks"} <= names
    for d in reg.tool_defs():
        assert reg.get(d.name).read_only is True
