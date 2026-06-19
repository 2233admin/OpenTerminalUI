from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.research import service

router = APIRouter(prefix="/api/research", tags=["research"])


class IngestRequest(BaseModel):
    query: str = "cat:q-fin.*"
    max_results: int = Field(25, ge=1, le=100)


@router.post("/ingest")
async def ingest(payload: IngestRequest) -> dict[str, Any]:
    return await service.ingest_arxiv(payload.query, max_results=payload.max_results)


@router.get("/search")
async def search(q: str, k: int = 10) -> dict[str, Any]:
    if not q.strip():
        raise HTTPException(status_code=400, detail="q is required")
    k = max(1, min(50, k))
    return {"query": q, "results": service.search(q, k=k)}


@router.get("/items")
async def items(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(200, limit))
    return {"items": service.list_items(limit=limit)}
