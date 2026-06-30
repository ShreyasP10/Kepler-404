"""Typed exception hierarchy.

Routes map each exception to a consistent JSON error + HTTP code via one
registered handler, instead of ad-hoc try/except blocks scattered in views.

    InvalidFileError  -> 415  (wrong extension / unsupported)
    EmptyFileError    -> 400  (zero-byte upload)
    FileTooLargeError -> 400  (exceeds max size)
    DecodingError     -> 500  (corrupt image / unreadable geotiff)
    ProcessingError   -> 500  (pipeline stage failure)
"""

from __future__ import annotations


class KeplerError(Exception):
    """Base class for all Kepler-404 errors. Carries an HTTP status code."""

    status_code: int = 500

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code

    @property
    def message(self) -> str:
        return self.args[0] if self.args else "Unknown error"


class InvalidFileError(KeplerError):
    status_code = 415


class EmptyFileError(KeplerError):
    status_code = 400


class FileTooLargeError(KeplerError):
    status_code = 400


class DecodingError(KeplerError):
    status_code = 500


class ProcessingError(KeplerError):
    status_code = 500
