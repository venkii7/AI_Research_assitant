"""Standard error shapes."""
from pydantic import BaseModel
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes across all endpoints."""

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    PLAN_LIMIT_REACHED = "plan_limit_reached"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    PROCESSING_FAILED = "processing_failed"
    AGENT_TIMEOUT = "agent_timeout"
    UPSTREAM_ERROR = "upstream_error"
    INTERNAL_ERROR = "internal_error"


class APIError(BaseModel):
    """Standard API error response shape."""

    error: str  # human-readable message
    code: ErrorCode
    details: dict = {}
