import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        request_id = str(uuid.uuid4())

        start = time.perf_counter()

        response = await call_next(request)

        duration = round(
            (time.perf_counter() - start) * 1000,
            2
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            (
                f"request_id={request_id} "
                f"method={request.method} "
                f"path={request.url.path} "
                f"status={response.status_code} "
                f"duration_ms={duration}"
            )
        )

        return response