"""CORS, logging, error handling middleware."""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import get_settings
import logging
import json
import time
import uuid

settings = get_settings()
logger = logging.getLogger("lens.api")


def add_middleware(app: FastAPI):
    """Register all middleware on the app. Call this in main.py."""

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration, 1),
                }
            )
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # Global error handler — converts unhandled exceptions to consistent JSON
    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled error on {request.url.path}: {exc}", exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "An internal error occurred",
                "code": "internal_error",
                "details": {},
            },
        )
