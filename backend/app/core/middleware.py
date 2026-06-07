import time
import uuid

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
                try:
                    method = scope.get('method')
                    path = scope.get('path')
                    print(f"[MIDDLEWARE] response start: method={method} path={path} status={status_code}")
                except Exception:
                    pass

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = round((time.perf_counter() - start) * 1000, 2)
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")

            logger.info(
                (
                    f"request_id={request_id} "
                    f"method={method} "
                    f"path={path} "
                    f"status={status_code} "
                    f"duration_ms={duration}"
                )
            )
