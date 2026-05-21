"""High-level PDF conversion engine (Phase 1 of the Amir Engine build)."""

from __future__ import annotations

import datetime as _dt
import logging
import re
from pathlib import Path
from typing import Optional

from docling_core.types.doc import ImageRefMode

from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.engines.artifacts import ArtifactsError, write_artifacts
from docling.engines.run_snapshot import write_run_snapshot
from docling.engines.schemas import (
    PageSummary,
    PdfConversionOutput,
    PdfEngineError,
    SourceKind,
)
from docling.engines.validation import validate_pdf_source
from docling.engines.visualizer import PreviewError, render_html_preview
from docling.exceptions import ConversionError

_log = logging.getLogger(__name__)

_PLACEHOLDER = "<!-- image -->"


class PdfEngine:
    """Thin facade over :class:`DocumentConverter` for PDF inputs.

    Returns a :class:`PdfConversionOutput` with normalised status, page
    summaries, error list, and the markdown export. The raw upstream
    :class:`ConversionResult` is preserved on the output for callers that
    need to drop down to lower-level APIs.
    """

    def __init__(
        self,
        converter: Optional[DocumentConverter] = None,
        *,
        with_page_images: bool = False,
        embed_images: bool = True,
        link_images: bool = True,
        images_scale: float = 1.5,
        save_artifacts: bool = True,
    ) -> None:
        """Initialise the engine.

        Parameters
        ----------
        converter
            Optional pre-built :class:`DocumentConverter` (advanced use).
            When provided, the other image flags are ignored.
        with_page_images
            When True, retain rendered page images so the HTML viewer
            (``make_html_preview=True``) can be built later. Redundant when
            ``save_artifacts=True`` (which forces this on internally).
        embed_images
            When True (default), additionally writes a second
            ``<stem>.embedded.md`` next to the primary markdown, with image
            placeholders replaced by base64 data URIs — a standalone file you
            can share without the surrounding ``images/`` folder.
        link_images
            When True (default), the primary ``<stem>.md`` swaps each image
            placeholder for a relative ``![](images/picture_NNN.png)``
            reference so markdown viewers render the figures inline.
            Requires ``save_artifacts=True`` for the image files to exist.
        images_scale
            Scale factor applied when generating page or picture images.
        save_artifacts
            When True (default) and ``output_dir`` is given to :meth:`convert`,
            writes ``document.json``, ``nodes.jsonl``, ``run.json`` and
            extracted figure/table images under the per-PDF output folder.
            Implicitly enables page + picture image generation.
        """
        self._image_scale = images_scale
        self._embed_images = embed_images
        self._link_images = link_images
        self._save_artifacts = save_artifacts
        self._engine_config = {
            "with_page_images": with_page_images,
            "embed_images": embed_images,
            "link_images": link_images,
            "images_scale": images_scale,
            "save_artifacts": save_artifacts,
            "converter_supplied": converter is not None,
        }
        if converter is not None:
            self._converter = converter
            self._pipeline_options: PdfPipelineOptions | None = None
            return

        need_page_images = with_page_images or save_artifacts
        need_picture_images = embed_images or save_artifacts
        if need_page_images or need_picture_images:
            self._pipeline_options = PdfPipelineOptions(
                generate_page_images=need_page_images,
                generate_picture_images=need_picture_images,
                images_scale=images_scale,
            )
            self._converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=self._pipeline_options
                    )
                },
            )
        else:
            self._pipeline_options = PdfPipelineOptions()
            self._converter = DocumentConverter(allowed_formats=[InputFormat.PDF])

    def convert(
        self,
        source: str | Path,
        *,
        output_dir: Path | None = None,
        max_num_pages: int | None = None,
        make_html_preview: bool = False,
    ) -> PdfConversionOutput:
        """Convert a single PDF from a local path or URL.

        Parameters
        ----------
        source
            Path to a local ``.pdf`` file or an ``http(s)://`` URL.
        output_dir
            If given, writes the markdown export(s) to
            ``<output_dir>/<stem>/<stem>.md`` (and ``<stem>.embedded.md`` when
            ``embed_images=True``).
        max_num_pages
            Optional cap on the number of pages to convert.
        """
        kind, normalised = validate_pdf_source(source)
        _log.info("PdfEngine: converting %s (%s)", normalised, kind.value)

        convert_kwargs: dict[str, object] = {"raises_on_error": False}
        if max_num_pages is not None:
            convert_kwargs["max_num_pages"] = max_num_pages

        started_at = _dt.datetime.now(_dt.timezone.utc)
        try:
            result: ConversionResult = self._converter.convert(
                normalised,
                **convert_kwargs,  # type: ignore[arg-type]
            )
        except ConversionError as exc:
            _log.exception("PdfEngine: conversion raised ConversionError")
            return PdfConversionOutput(
                status=ConversionStatus.FAILURE,
                source=normalised,
                source_kind=kind,
                errors=[
                    PdfEngineError(component="DocumentConverter", message=str(exc))
                ],
            )
        finished_at = _dt.datetime.now(_dt.timezone.utc)

        output = self._build_output(result, kind=kind, normalised=normalised)

        if output.succeeded and output_dir is not None:
            pdf_dir = _resolve_pdf_dir(output_dir, normalised, result)
            pdf_dir.mkdir(parents=True, exist_ok=True)
            output.output_dir = pdf_dir

            if self._save_artifacts:
                try:
                    artifacts = write_artifacts(result, pdf_dir)
                    output.document_json = artifacts.document_json
                    output.nodes_jsonl = artifacts.nodes_jsonl
                    output.picture_images = artifacts.picture_images
                    output.table_images = artifacts.table_images
                except ArtifactsError as exc:
                    _log.warning("PdfEngine: artifacts not written: %s", exc)
                    output.errors.append(
                        PdfEngineError(component="artifacts", message=str(exc))
                    )

            if self._link_images and output.markdown and output.picture_images:
                rel_paths = [
                    p.relative_to(pdf_dir).as_posix() for p in output.picture_images
                ]
                output.markdown = _link_picture_placeholders(output.markdown, rel_paths)

            self._write_primary_markdown(output, pdf_dir)

            if self._embed_images:
                output.markdown_embedded_path = self._write_embedded_markdown(
                    result, pdf_dir, output.errors
                )

            if self._save_artifacts:
                output.run_json = write_run_snapshot(
                    pdf_dir,
                    source=normalised,
                    source_kind=kind.value,
                    status=str(output.status),
                    started_at=started_at,
                    finished_at=finished_at,
                    engine_config=self._engine_config,
                    pipeline_options=(
                        self._pipeline_options.model_dump(
                            mode="json", serialize_as_any=True
                        )
                        if self._pipeline_options is not None
                        else None
                    ),
                    page_count=output.page_count,
                    pictures_extracted=len(output.picture_images),
                    tables_extracted=len(output.table_images),
                    errors=[e.model_dump() for e in output.errors],
                )

            if make_html_preview:
                try:
                    output.preview_html = render_html_preview(
                        result, pdf_dir, image_scale=self._image_scale
                    )
                except PreviewError as exc:
                    _log.warning("PdfEngine: HTML preview skipped: %s", exc)
                    output.errors.append(
                        PdfEngineError(component="visualizer", message=str(exc))
                    )
        elif make_html_preview and output_dir is None:
            raise ValueError("make_html_preview=True requires output_dir to be set.")

        return output

    @staticmethod
    def _build_output(
        result: ConversionResult,
        *,
        kind: SourceKind,
        normalised: str,
    ) -> PdfConversionOutput:
        pages: list[PageSummary] = []
        for page in result.pages:
            size = page.size
            layout = page.predictions.layout if page.predictions else None
            cluster_count = len(layout.clusters) if layout is not None else 0
            pages.append(
                PageSummary(
                    page_no=page.page_no,
                    width=size.width if size is not None else None,
                    height=size.height if size is not None else None,
                    cluster_count=cluster_count,
                )
            )

        errors = [
            PdfEngineError(component=str(err.component_type), message=err.error_message)
            for err in result.errors
        ]

        markdown: str | None = None
        if result.status in {
            ConversionStatus.SUCCESS,
            ConversionStatus.PARTIAL_SUCCESS,
        }:
            try:
                markdown = result.document.export_to_markdown(
                    image_mode=ImageRefMode.PLACEHOLDER
                )
            except Exception as exc:  # pragma: no cover - defensive
                _log.warning("PdfEngine: markdown export failed: %s", exc)
                errors.append(
                    PdfEngineError(component="export_to_markdown", message=str(exc))
                )

        return PdfConversionOutput(
            status=result.status,
            source=normalised,
            source_kind=kind,
            page_count=result.input.page_count
            if result.input is not None
            else len(pages),
            pages=pages,
            errors=errors,
            markdown=markdown,
            raw=result,
        )

    @staticmethod
    def _write_primary_markdown(output: PdfConversionOutput, pdf_dir: Path) -> None:
        if output.markdown is None:
            return
        target = pdf_dir / f"{pdf_dir.name}.md"
        target.write_text(output.markdown, encoding="utf-8")
        _log.info("PdfEngine: wrote markdown to %s", target)

    @staticmethod
    def _write_embedded_markdown(
        result: ConversionResult,
        pdf_dir: Path,
        errors: list[PdfEngineError],
    ) -> Path | None:
        try:
            embedded = result.document.export_to_markdown(
                image_mode=ImageRefMode.EMBEDDED
            )
        except Exception as exc:
            _log.warning("PdfEngine: embedded markdown export failed: %s", exc)
            errors.append(
                PdfEngineError(
                    component="export_to_markdown_embedded", message=str(exc)
                )
            )
            return None
        target = pdf_dir / f"{pdf_dir.name}.embedded.md"
        target.write_text(embedded, encoding="utf-8")
        _log.info("PdfEngine: wrote embedded markdown to %s", target)
        return target


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _link_picture_placeholders(markdown: str, picture_paths: list[str]) -> str:
    """Replace ``<!-- image -->`` placeholders with ``![](path)`` refs in order."""
    paths = iter(picture_paths)

    def _swap(_match: re.Match[str]) -> str:
        try:
            return f"![]({next(paths)})"
        except StopIteration:
            return _PLACEHOLDER

    return re.sub(re.escape(_PLACEHOLDER), _swap, markdown)


def _resolve_pdf_dir(
    output_dir: Path, normalised: str, result: ConversionResult
) -> Path:
    """Return ``output_dir / <safe-stem>`` for this PDF.

    Prefers the upstream-reported input filename (which works for URL inputs
    too) and falls back to the source's stem; sanitised for filesystem
    safety.
    """
    raw_name: str | None = None
    if result.input is not None:
        try:
            raw_name = result.input.file.name
        except Exception:  # pragma: no cover - defensive
            raw_name = None
    candidate = Path(raw_name or normalised).stem or "document"
    safe = _SAFE_NAME.sub("_", candidate).strip("._-") or "document"
    return output_dir / safe
