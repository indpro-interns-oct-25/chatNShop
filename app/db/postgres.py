import asyncio
import json
import os
import uuid
from typing import Any, Dict, Optional

import asyncpg
from loguru import logger

_pool: Optional[asyncpg.pool.Pool] = None


async def init_pool(dsn: str) -> None:
    global _pool
    if _pool is not None:
        return
    try:
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
        await ensure_tables()
        logger.info("PostgreSQL pool initialized")
    except Exception as exc:
        logger.warning(f"PostgreSQL init failed, will use file fallback. Error: {exc}")
        _pool = None


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
        finally:
            _pool = None


async def ensure_tables() -> None:
    if _pool is None:
        return
    create_sql = """
    CREATE TABLE IF NOT EXISTS shopify_api_calls (
        id UUID PRIMARY KEY,
        request_ts TIMESTAMPTZ,
        response_ts TIMESTAMPTZ,
        latency_ms INTEGER,
        method TEXT,
        url TEXT,
        path TEXT,
        status_code INTEGER,
        request_headers JSONB,
        request_body TEXT,
        response_headers JSONB,
        response_body TEXT,
        error TEXT,
        correlation_id UUID
    );
    """
    async with _pool.acquire() as conn:
        await conn.execute(create_sql)


async def insert_shopify_call(log: Dict[str, Any]) -> None:
    """
    Inserts a Shopify call log into Postgres or falls back to JSONL file if PG is unavailable.
    """
    global _pool
    # Make sure we always have an id
    log = dict(log)
    log["id"] = log.get("id") or str(uuid.uuid4())

    if _pool is None:
        _append_jsonl_fallback(log)
        return

    insert_sql = """
    INSERT INTO shopify_api_calls (
        id, request_ts, response_ts, latency_ms, method, url, path, status_code,
        request_headers, request_body, response_headers, response_body, error, correlation_id
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11::jsonb, $12, $13, $14
    );
    """
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                insert_sql,
                log.get("id"),
                log.get("request_ts"),
                log.get("response_ts"),
                log.get("latency_ms"),
                log.get("method"),
                log.get("url"),
                log.get("path"),
                log.get("status_code"),
                json.dumps(log.get("request_headers") or {}),
                log.get("request_body"),
                json.dumps(log.get("response_headers") or {}),
                log.get("response_body"),
                log.get("error"),
                log.get("correlation_id"),
            )
    except Exception as exc:
        logger.warning(f"Failed to insert Shopify log into PG, using file fallback. Error: {exc}")
        _append_jsonl_fallback(log)


def _append_jsonl_fallback(record: Dict[str, Any]) -> None:
    try:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "shopify_api_fallback.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.error(f"Failed to write Shopify log to JSONL fallback: {exc}")


