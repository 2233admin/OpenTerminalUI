from __future__ import annotations

from typing import Any

from backend.agent.tools.registry import ToolRegistry, ToolSpec
from backend.api.deps import get_unified_fetcher
from backend.screener.engine import RunConfig, ScreenerEngine
from backend.screener.router import _hydrate_missing_universe_rows

# Compact set of columns returned to the agent (the full screener row carries viz
# data, scores and sparklines that just bloat the LLM context).
_AGENT_SCREEN_FIELDS = (
    "ticker", "company", "sector", "industry", "price", "market_cap",
    "pe", "pb", "roe", "roce", "debt_equity", "revenue_growth", "dividend_yield",
)


async def screen_stocks(args: dict[str, Any]) -> dict[str, Any]:
    """Run the platform screener from a natural filter string.

    Always returns a structured result (never raises) so the agent can reason
    over it even when data is unavailable — a failed tool call would just abort
    the run. Errors/empties come back as ``count: 0`` with a ``note``.
    """
    query = str(args.get("query", ""))
    universe = str(args.get("universe", "nse_500"))
    market = str(args.get("market", "IN"))
    try:
        limit = max(1, min(100, int(args.get("limit", 25))))
    except (TypeError, ValueError):
        limit = 25

    def _empty(note: str, hydrated: int = 0) -> dict[str, Any]:
        return {
            "query": query, "market": market, "universe": universe,
            "count": 0, "hydrated_rows": hydrated, "results": [], "note": note,
        }

    # The screener reads a materialized store populated lazily. The HTTP route
    # hydrates before running; the agent tool must too, but bounded — a slow or
    # blocked data source must not hang or fail the run.
    hydrated = 0
    try:
        hydrated = await _hydrate_missing_universe_rows(universe, market)
    except Exception:  # noqa: BLE001 - hydration is best-effort
        hydrated = 0

    try:
        config = RunConfig(query=query, universe=universe, market=market, limit=limit)
        result = ScreenerEngine().run(config)
    except Exception as exc:  # noqa: BLE001 - never fail the agent tool
        return _empty(f"Screener could not run: {exc}", hydrated)

    rows = result.get("results", []) if isinstance(result, dict) else []
    trimmed = [{k: row.get(k) for k in _AGENT_SCREEN_FIELDS if k in row} for row in rows]
    count = int(result.get("total_results", len(trimmed))) if isinstance(result, dict) else len(trimmed)
    payload = {
        "query": result.get("query_parsed", query) if isinstance(result, dict) else query,
        "market": market,
        "universe": universe,
        "count": count,
        "hydrated_rows": hydrated,
        "results": trimmed,
    }
    if count == 0:
        payload["note"] = (
            "No matches. Data for this universe may be unavailable in this "
            "environment (e.g. NSE/India sources), or the filter is too strict. "
            "Try market='US', universe='sp_500', or relax the criteria."
        )
    return payload


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


async def search_research(args: dict[str, Any]) -> dict[str, Any]:
    """RAG over the local quant-research knowledge base (arXiv etc.)."""
    from backend.core.research import service as research_service

    query = str(args.get("query", "")).strip()
    if not query:
        return {"query": query, "count": 0, "results": [], "note": "query is required"}
    try:
        k = max(1, min(20, int(args.get("k", 6))))
    except (TypeError, ValueError):
        k = 6
    rows = research_service.search(query, k=k)
    trimmed = [
        {
            "title": r.get("title"),
            "authors": r.get("authors"),
            "url": r.get("url"),
            "published_at": r.get("published_at"),
            "score": r.get("score"),
            "abstract": (str(r.get("abstract") or "")[:600]),
        }
        for r in rows
    ]
    note = None if trimmed else "No indexed research yet — ingest via POST /api/research/ingest first."
    return {"query": query, "count": len(trimmed), "results": trimmed, **({"note": note} if note else {})}


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
    reg.register(ToolSpec(
        name="search_research",
        description="Search the local quant-research knowledge base (arXiv papers etc.) for relevant findings. "
                    "Returns titles, authors, abstract snippets and links.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic / question to search for."},
                "k": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
        },
        handler=search_research, read_only=True,
    ))
    return reg
