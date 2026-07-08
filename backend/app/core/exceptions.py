from fastapi import HTTPException, status


class AppException(HTTPException):
    """
    Base class for all application-specific HTTP exceptions.

    WHY custom exceptions?
    - Consistent error response format across the entire API
    - Raise domain-meaningful exceptions in services (e.g., NotFoundException)
      instead of remembering HTTP status codes
    - Easier to catch specific exception types in tests

    Usage:
        raise NotFoundException(resource="Document", identifier=str(doc_id))

    FastAPI automatically converts HTTPException subclasses to JSON:
        {"detail": "Document 'abc-123' not found"}
    """
    pass


class NotFoundException(AppException):
    """HTTP 404 — Resource does not exist."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} '{identifier}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(AppException):
    """
    HTTP 401 — Not authenticated.

    Includes WWW-Authenticate header as required by RFC 6750 (Bearer token spec).
    This header tells the client how to authenticate.
    """

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    """HTTP 403 — Authenticated but not authorized (wrong role)."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(AppException):
    """HTTP 409 — Resource already exists (e.g., email already registered)."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} already exists",
        )


class BadRequestException(AppException):
    """HTTP 400 — Client sent an invalid request."""

    def __init__(self, detail: str = "Invalid request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnprocessableEntityException(AppException):
    """HTTP 422 — Request is well-formed but semantically invalid."""

    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class ServiceUnavailableException(AppException):
    """HTTP 503 — A downstream service (DB, Qdrant, OpenAI) is unavailable."""

    def __init__(self, service: str = "Service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} is temporarily unavailable. Please try again later.",
        )


class FileTooLargeException(AppException):
    """HTTP 413 — Uploaded file exceeds the allowed size limit."""

    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum allowed size of {max_mb} MB",
        )


class UnsupportedFileTypeException(AppException):
    """HTTP 415 — Uploaded file type is not supported."""

    def __init__(self, allowed_types: list[str]):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_types)}",
        )
