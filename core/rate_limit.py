import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        now = time.time()
        cutoff = now - self.window_seconds

        self.requests[client_id] = [t for t in self.requests[client_id] if t > cutoff]

        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        self.requests[client_id].append(now)
        return await call_next(request)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 5, window_seconds: int = 300):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/auth"):
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()
        cutoff = now - self.window_seconds

        self.requests[client_id] = [t for t in self.requests[client_id] if t > cutoff]

        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts. Please try again in 5 minutes.",
            )

        self.requests[client_id].append(now)
        return await call_next(request)
