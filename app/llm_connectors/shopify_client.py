from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from loguru import logger

from app.utils.redaction import redact_headers, truncate_text
from app.db.postgres import insert_shopify_call


class ShopifyClient:
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = "2023-10",
        timeout_seconds: float = 15.0,
        log_response_bodies: bool = True,
    ) -> None:
        self.base_url = f"https://{shop_domain}"
        self.api_version = api_version
        self.access_token = access_token
        self.timeout_seconds = timeout_seconds
        self.log_response_bodies = log_response_bodies
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=self.timeout_seconds)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = await self._ensure_client()
        corr_id = str(uuid.uuid4())
        url_path = path
        url_full = f"{self.base_url}{url_path}"

        # Prepare headers (merged)
        req_headers = dict(client.headers)
        if headers:
            req_headers.update(headers)

        request_ts = datetime.now(timezone.utc)
        error_text = None
        status_code = None
        response_headers: Dict[str, Any] = {}
        response_body_text: Optional[str] = None

        try:
            response = await client.request(method=method, url=url_path, params=params, json=json_body)
            status_code = response.status_code
            response_headers = dict(response.headers)
            if self.log_response_bodies:
                response_body_text = truncate_text(response.text)
            response.raise_for_status()
            return response
        except Exception as exc:
            error_text = str(exc)
            logger.warning(f"Shopify request failed ({corr_id}): {error_text}")
            raise
        finally:
            response_ts = datetime.now(timezone.utc)
            latency_ms = int((response_ts - request_ts).total_seconds() * 1000)
            masked_req_headers = redact_headers(req_headers)

            # Safe serialization of request body
            req_body_text = None
            if json_body is not None:
                try:
                    req_body_text = truncate_text(json.dumps(json_body, ensure_ascii=False))
                except Exception:
                    req_body_text = truncate_text(str(json_body))

            await insert_shopify_call(
                {
                    "request_ts": request_ts,
                    "response_ts": response_ts,
                    "latency_ms": latency_ms,
                    "method": method.upper(),
                    "url": url_full,
                    "path": url_path,
                    "status_code": status_code,
                    "request_headers": masked_req_headers,
                    "request_body": req_body_text,
                    "response_headers": response_headers,
                    "response_body": response_body_text,
                    "error": error_text,
                    "correlation_id": corr_id,
                }
            )

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None):
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        return await self.request("POST", path, json_body=json_body, headers=headers)

    async def put(
        self,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        return await self.request("PUT", path, json_body=json_body, headers=headers)

    async def delete(self, path: str, headers: Optional[Dict[str, Any]] = None):
        return await self.request("DELETE", path, headers=headers)


