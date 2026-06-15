import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.logging import get_logger

logger = get_logger("middleware.logging")

"""
This middleware tracks every request,
measures how long it takes,
logs the status code with colored indicators,
and records any errors that occur 
before passing them back to FastAPI.
"""


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time() # when request comes is stores the current time 
        # We don't want to log the health check endpoint repeatedly
        is_health = request.url.path == "/api/health"
        if not is_health:
            logger.info(f"--> {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            if not is_health:
                status_color = (
                    "🐲"
                    if 200 <= response.status_code < 300
                    else ("🦊" if 300 <= response.status_code < 400 else "💥")
                )
                logger.info(
                    f"<-- {status_color} {request.method} {request.url.path} [{response.status_code}] - {process_time:.2f}ms"
                )
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            if not is_health:
                logger.error(
                    f"<-- 💥 {request.method} {request.url.path} [500] - {process_time:.2f}ms - Error: {str(e)}"
                )
            raise e
