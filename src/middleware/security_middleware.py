"""
Security middleware for FastAPI application.

Provides:
- Request validation and sanitization
- Prompt injection detection for API inputs
- Security headers
- Audit logging of security events
"""

import json
import time
from typing import Callable, Optional, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

from ..core.security import (
    SecurityManager,
    get_security_manager,
    ValidationResult,
    ThreatLevel,
    SecurityAction,
)
from ..core.logger import setup_logger, get_request_id


logger = setup_logger("middleware.security")


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for FastAPI.

    Features:
    - Validates request body for injection attacks
    - Adds security headers to responses
    - Logs security events
    - Configurable blocking behavior
    """

    # Paths to skip security validation (health checks, static files)
    SKIP_PATHS: Set[str] = {"/health", "/health/detailed", "/metrics", "/docs", "/openapi.json", "/redoc"}

    # Content types that should be validated
    VALIDATE_CONTENT_TYPES: Set[str] = {"application/json"}

    # Security headers to add to responses
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }

    def __init__(
        self,
        app: ASGIApp,
        security_manager: SecurityManager = None,
        block_on_threat: bool = True,
        min_block_level: ThreatLevel = ThreatLevel.MEDIUM,
        add_security_headers: bool = True,
    ):
        super().__init__(app)
        self.security = security_manager or get_security_manager()
        self.block_on_threat = block_on_threat
        self.min_block_level = min_block_level
        self.add_security_headers = add_security_headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through security checks."""
        start_time = time.time()
        request_id = get_request_id() or "unknown"
        client_ip = request.client.host if request.client else "unknown"

        # Skip validation for certain paths
        if request.url.path in self.SKIP_PATHS:
            response = await call_next(request)
            return self._add_headers(response)

        # Validate request body for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")

            if any(ct in content_type for ct in self.VALIDATE_CONTENT_TYPES):
                validation_result = await self._validate_request_body(
                    request, client_ip, request_id
                )

                if validation_result and not validation_result.is_safe:
                    logger.warning(
                        f"Request blocked by security middleware: {validation_result.reason}",
                        extra={
                            "request_id": request_id,
                            "client_ip": client_ip,
                            "path": request.url.path,
                            "threat_level": validation_result.threat_level.value,
                        }
                    )

                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": "Request blocked due to security policy",
                            "error_code": "SECURITY_VALIDATION_FAILED",
                            "request_id": request_id,
                        },
                        headers=self.SECURITY_HEADERS if self.add_security_headers else {},
                    )

        # Process request
        response = await call_next(request)

        # Add security headers
        response = self._add_headers(response)

        # Log request completion
        duration = time.time() - start_time
        logger.debug(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "duration_ms": round(duration * 1000, 2),
                "status_code": response.status_code,
            }
        )

        return response

    async def _validate_request_body(
        self,
        request: Request,
        client_ip: str,
        request_id: str,
    ) -> Optional[ValidationResult]:
        """Validate the request body for security threats."""
        try:
            # Read and cache body for downstream handlers
            body = await request.body()
            if not body:
                return None

            # Parse JSON body
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Let FastAPI handle JSON parsing errors
                return None

            # Validate fields that might be used in prompts
            fields_to_check = ["company_name", "query", "prompt", "message", "content"]

            for field in fields_to_check:
                if field in data and isinstance(data[field], str):
                    result = self.security.validate_prompt_input(
                        text=data[field],
                        source=client_ip,
                        request_id=request_id,
                    )

                    if not result.is_safe and self._should_block(result):
                        return result

                    # Log warnings for non-blocking threats
                    if result.threat_level != ThreatLevel.NONE:
                        logger.info(
                            f"Security warning for field '{field}': {result.reason}",
                            extra={
                                "request_id": request_id,
                                "field": field,
                                "threat_level": result.threat_level.value,
                                "patterns": result.matched_patterns,
                            }
                        )

            return ValidationResult.safe()

        except Exception as e:
            logger.error(f"Error in security validation: {e}", exc_info=True)
            # Don't block on validation errors - fail open but log
            return None

    def _should_block(self, result: ValidationResult) -> bool:
        """Determine if a validation result should block the request."""
        if not self.block_on_threat:
            return False

        threat_values = {
            ThreatLevel.NONE: 0,
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4,
        }

        return (
            result.action == SecurityAction.BLOCK and
            threat_values[result.threat_level] >= threat_values[self.min_block_level]
        )

    def _add_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        if self.add_security_headers:
            for header, value in self.SECURITY_HEADERS.items():
                response.headers[header] = value
        return response


# Factory function for creating middleware
def get_security_middleware(
    app: ASGIApp,
    block_on_threat: bool = True,
    min_block_level: ThreatLevel = ThreatLevel.MEDIUM,
) -> SecurityMiddleware:
    """Create a security middleware instance."""
    return SecurityMiddleware(
        app=app,
        block_on_threat=block_on_threat,
        min_block_level=min_block_level,
    )
