from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            "NOT_FOUND",
            f"{resource} not found",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )


class ConflictError(AppError):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        super().__init__(code, message, status_code=409, details=details)


class DomainValidationError(AppError):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        super().__init__(code, message, status_code=422, details=details)


class SolarError(AppError):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        super().__init__(code, message, status_code=502, details=details)
