from __future__ import annotations

from typing import Any

from backend.agent.tools.registry import ToolRegistry, ToolSpec
from backend.api.deps import get_unified_fetcher
from backend.screener.engine import RunConfig, ScreenerEngine


async def screen_stocks(args: dict[str, Any]) -> dict[str, Any]:
    """Run the platform screener from a natural filter string."""
    config = RunConfig(
        query=str(args.get("query", "")),
        universe=str(args.get("universe", "nse_500")),
        market=str(args.get("market", "IN")),
        limit=int(args.get("limit", 25)),
    )
    engine = ScreenerEngine()
    return engine.run(config)


async def get_stock_snapshot(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch a full fundamentals/price snapshot for one ticker."""
    symbol = str(args.get("ticker", "")).strip().upper()
    fetcher = await get_unified_fetcher()
    return await fetcher.fetch_stock_snapshot(symbol)


async def compare_stocks(args: dict[str, Any]) -> dict[str, Any]:
    """Fetch snapshots for several tickers, projected to the requested metrics."""
    tickers = [str(t).strip().upper() for t in args.get("tickers", []) if str(t).strip()]
    metrics = [str(m) for m in args.get("metrics", [])]
    fetcher = await get_unified_fetcher()
    rows: list[dict[str, Any]] = []
    for sym in tickers:
        snap = await fetcher.fetch_stock_snapshot(sym)
        row = {"symbol": sym}
        if metrics:
            for m in metrics:
                row[m] = snap.get(m)
        else:
            row.update(snap)
        rows.append(row)
    return {"rows": rows}


def build_default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ToolSpec(
        name="screen_stocks",
        description="Find stocks matching filter expressions (e.g. 'pe_ratio < 20 and roe > 15'). "
                    "Returns matching rows with fundamentals.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filter expression."},
                "universe": {"type": "string", "enum": ["nse_500", "sp_500", "nasdaq_100", "us_all"]},
                "market": {"type": "string", "enum": ["IN", "US"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "required": ["query"],
        },
        handler=screen_stocks, read_only=True,
    ))
    reg.register(ToolSpec(
        name="get_stock_snapshot",
        description="Get a full price + fundamentals snapshot for a single ticker.",
        parameters={
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
        handler=get_stock_snapshot, read_only=True,
    ))
    reg.register(ToolSpec(
        name="compare_stocks",
        description="Compare several tickers across the requested metrics "
                    "(e.g. pe_ratio, roe, market_cap).",
        parameters={
            "type": "object",
            "properties": {
                "tickers": {"type": "array", "items": {"type": "string"}},
                "metrics": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["tickers"],
        },
        handler=compare_stocks, read_only=True,
    ))
    return reg
