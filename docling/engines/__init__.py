"""Amir Engine — high-level wrappers over Docling for PDF → structured pipelines.

This subpackage is project-local (not upstream Docling). Phase 1 ships
:class:`PdfEngine`, a thin facade around :class:`docling.document_converter.DocumentConverter`
that returns a validated :class:`PdfConversionOutput` Pydantic model.
"""

from docling.engines.pdf_engine import PdfEngine
from docling.engines.schemas import (
    PageSummary,
    PdfConversionOutput,
    PdfEngineError,
    SourceKind,
)
from docling.engines.visualizer import PreviewError, render_html_preview

__all__ = [
    "PageSummary",
    "PdfConversionOutput",
    "PdfEngine",
    "PdfEngineError",
    "PreviewError",
    "SourceKind",
    "render_html_preview",
]
