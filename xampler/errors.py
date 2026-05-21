from __future__ import annotations

from typing import Literal

XamplerErrorCode = Literal[
    "not_found",
    "unauthorized",
    "conflict",
    "bad_request",
    "unsupported",
    "provider",
]


class XamplerError(Exception):
    """Normalized Xampler error with a stable code and original cause.

    These errors are for exceptional failures: auth, conflicts, unsupported
    operations, invalid user input, and provider/runtime failures. Expected
    absence can still be modeled as ``None`` or ``False`` by high-level Pythonic
    APIs where that is the documented contract.
    """

    code: XamplerErrorCode
    cause: object | None

    def __init__(self, code: XamplerErrorCode, message: str, *, cause: object | None = None):
        super().__init__(message)
        self.code = code
        self.cause = cause

    @classmethod
    def wrap(
        cls,
        error: object,
        *,
        fallback_code: XamplerErrorCode = "provider",
        message: str | None = None,
    ) -> XamplerError:
        if isinstance(error, XamplerError):
            return error
        resolved = message if message is not None else str(error)
        return cls(fallback_code, resolved, cause=error)

    def to_payload(self, *, status: int) -> dict[str, object]:
        return {"error": {"code": self.code, "message": str(self), "status": status}}


def bad_request(message: str, *, cause: object | None = None) -> XamplerError:
    return XamplerError("bad_request", message, cause=cause)


def unsupported(message: str, *, cause: object | None = None) -> XamplerError:
    return XamplerError("unsupported", message, cause=cause)


def provider_error(message: str, *, cause: object | None = None) -> XamplerError:
    return XamplerError("provider", message, cause=cause)


def ensure_supported_runtime(condition: bool, message: str, *, cause: object | None = None) -> None:
    if not condition:
        raise unsupported(message, cause=cause)


def wrap_provider_call(error: object, *, message: str | None = None) -> XamplerError:
    return XamplerError.wrap(error, fallback_code="provider", message=message)


__all__ = [
    "XamplerError",
    "XamplerErrorCode",
    "bad_request",
    "ensure_supported_runtime",
    "provider_error",
    "unsupported",
    "wrap_provider_call",
]
