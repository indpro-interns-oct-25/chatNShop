# app/monitoring/http_middleware.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import REQUEST_COUNT, REQUEST_IN_PROGRESS, REQUEST_LATENCY


class PrometheusFastAPIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        REQUEST_IN_PROGRESS.inc()
        start = time.time()

        try:
            response = await call_next(request)
            elapsed = time.time() - start
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(elapsed)
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                http_status=str(response.status_code)
            ).inc()
            return response

        except Exception:
            elapsed = time.time() - start
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(elapsed)
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                http_status="500"
            ).inc()
            raise

        finally:
            REQUEST_IN_PROGRESS.dec()
