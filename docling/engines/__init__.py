"""Amir Engine — high-level wrappers over Docling for PDF → structured pipelines.

This subpackage is project-local (not upstream Docling). Phase 1 ships
:class:`PdfEngine`, a thin facade around :class:`docling.document_converter.DocumentConverter`
that returns a validated :class:`PdfConversionOutput` Pydantic model.
"""

from docling.engines.artifacts import ArtifactPaths, ArtifactsError, write_artifacts
from docling.engines.pdf_engine import PdfEngine
from docling.engines.run_snapshot import write_run_snapshot
from docling.engines.schemas import (
    PageSummary,
    PdfConversionOutput,
    PdfEngineError,
    SourceKind,
)
from docling.engines.visualizer import PreviewError, render_html_preview

__all__ = [
    "ArtifactPaths",
    "ArtifactsError",
    "PageSummary",
    "PdfConversionOutput",
    "PdfEngine",
    "PdfEngineError",
    "PreviewError",
    "SourceKind",
    "render_html_preview",
    "write_artifacts",
    "write_run_snapshot",
]
