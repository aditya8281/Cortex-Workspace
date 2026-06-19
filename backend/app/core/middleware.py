import time
import uuid

from backend.app.api.metrics import record_request
from backend.app.core.logging import RequestIdFilter, get_logger

logger = get_logger(__name__)

# Security headers added to every response.
_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"x-xss-protection", b"1; mode=block"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    # script-src: no unsafe-inline or unsafe-eval
    # style-src: nonce-based — nonce added at the app level by Next.js
    (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' http://localhost:*"),
]


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        RequestIdFilter.set(request_id)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                headers.extend(_SECURITY_HEADERS)
                message["headers"] = headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = round((time.perf_counter() - start) * 1000, 2)
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")
            record_request(status_code, duration)
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id, method, path, status_code, duration,
            )
