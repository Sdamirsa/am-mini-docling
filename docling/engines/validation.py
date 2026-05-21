"""Input validation for the Amir Engine wrappers."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from docling.engines.schemas import SourceKind

_URL_SCHEMES: frozenset[str] = frozenset({"http", "https"})


class InvalidPdfSourceError(ValueError):
    """Raised when a PDF source cannot be resolved to a local file or URL."""


def classify_source(source: str | Path) -> SourceKind:
    """Classify *source* as a local path or a URL.

    Does not touch the filesystem unless the input is unambiguously a path.
    """
    if isinstance(source, Path):
        return SourceKind.LOCAL_PATH

    parsed = urlparse(source)
    if parsed.scheme in _URL_SCHEMES and parsed.netloc:
        return SourceKind.URL
    return SourceKind.LOCAL_PATH


def validate_pdf_source(source: str | Path) -> tuple[SourceKind, str]:
    """Validate *source* and return ``(kind, normalised)``.

    - Local paths must exist, be files, and have a ``.pdf`` suffix
      (case-insensitive).
    - URLs are accepted by scheme + netloc only; the network is not contacted.

    Raises
    ------
    InvalidPdfSourceError
        If *source* is neither a usable local PDF nor a well-formed URL.
    """
    kind = classify_source(source)

    if kind is SourceKind.URL:
        return kind, str(source)

    path = Path(source)
    if not path.exists():
        raise InvalidPdfSourceError(f"PDF source does not exist: {path}")
    if not path.is_file():
        raise InvalidPdfSourceError(f"PDF source is not a file: {path}")
    if path.suffix.lower() != ".pdf":
        raise InvalidPdfSourceError(
            f"PDF source must have a .pdf suffix, got: {path.suffix or '<none>'}"
        )
    return kind, str(path)
