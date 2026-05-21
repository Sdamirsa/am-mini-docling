"""Tests for :class:`docling.engines.PdfEngine` (Phase 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docling.datamodel.base_models import ConversionStatus
from docling.engines import PdfConversionOutput, PdfEngine, SourceKind
from docling.engines.validation import (
    InvalidPdfSourceError,
    classify_source,
    validate_pdf_source,
)

FIXTURE_PDF = Path("tests/data/pdf/2305.03393v1-pg9.pdf")


def test_classify_source_url() -> None:
    assert classify_source("https://example.com/x.pdf") is SourceKind.URL
    assert classify_source("http://example.com/x.pdf") is SourceKind.URL


def test_classify_source_local_path() -> None:
    assert classify_source("relative/path.pdf") is SourceKind.LOCAL_PATH
    assert classify_source(Path("/tmp/x.pdf")) is SourceKind.LOCAL_PATH
    # `file://` is not treated as URL by the engine — local paths only.
    assert classify_source("file:///tmp/x.pdf") is SourceKind.LOCAL_PATH


def test_validate_pdf_source_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.pdf"
    with pytest.raises(InvalidPdfSourceError, match="does not exist"):
        validate_pdf_source(missing)


def test_validate_pdf_source_rejects_non_pdf_suffix(tmp_path: Path) -> None:
    not_pdf = tmp_path / "doc.txt"
    not_pdf.write_text("hello")
    with pytest.raises(InvalidPdfSourceError, match=r"\.pdf suffix"):
        validate_pdf_source(not_pdf)


def test_validate_pdf_source_accepts_url() -> None:
    kind, normalised = validate_pdf_source("https://arxiv.org/pdf/2206.01062")
    assert kind is SourceKind.URL
    assert normalised == "https://arxiv.org/pdf/2206.01062"


@pytest.mark.skipif(
    not FIXTURE_PDF.exists(),
    reason=f"fixture {FIXTURE_PDF} not available",
)
def test_pdf_engine_converts_local_fixture(tmp_path: Path) -> None:
    """End-to-end conversion of a small bundled PDF.

    Verifies the wrapper's contract: status, source classification, page
    summaries, and markdown export are populated and internally consistent.
    """
    engine = PdfEngine(save_artifacts=False)
    output: PdfConversionOutput = engine.convert(FIXTURE_PDF, output_dir=tmp_path)

    assert output.succeeded, f"conversion failed: {output.errors}"
    assert output.status in {
        ConversionStatus.SUCCESS,
        ConversionStatus.PARTIAL_SUCCESS,
    }
    assert output.source_kind is SourceKind.LOCAL_PATH
    assert output.source.endswith(FIXTURE_PDF.name)

    # At least one page must have been processed with a layout summary.
    assert output.page_count >= 1
    assert len(output.pages) >= 1
    first = output.pages[0]
    assert first.page_no >= 1
    assert first.cluster_count >= 0  # may be 0 on tiny/empty pages

    # Markdown export landed on disk in a per-PDF subfolder.
    assert output.markdown is not None and output.markdown.strip()
    pdf_dir = tmp_path / FIXTURE_PDF.stem
    assert output.output_dir == pdf_dir
    written = pdf_dir / f"{FIXTURE_PDF.stem}.md"
    assert written.exists()
    assert written.read_text(encoding="utf-8") == output.markdown

    # The schema must serialise without leaking the raw ConversionResult.
    dumped = output.model_dump()
    assert "raw" not in dumped


@pytest.mark.skipif(
    not FIXTURE_PDF.exists(),
    reason=f"fixture {FIXTURE_PDF} not available",
)
def test_pdf_engine_renders_html_preview(tmp_path: Path) -> None:
    """End-to-end: page images are retained and an HTML preview is written."""
    engine = PdfEngine(with_page_images=True, images_scale=1.0, save_artifacts=False)
    output = engine.convert(FIXTURE_PDF, output_dir=tmp_path, make_html_preview=True)

    assert output.succeeded, f"conversion failed: {output.errors}"
    assert output.preview_html is not None
    assert output.preview_html.exists()
    assert output.preview_html.name == "preview.html"

    html_text = output.preview_html.read_text(encoding="utf-8")
    # Structural smoke checks rather than mock-driven assertions:
    assert "<!doctype html>" in html_text
    assert "Docling preview" in html_text
    assert 'class="bbox"' in html_text
    assert 'class="legend"' in html_text

    # Page images landed under the per-PDF subdir.
    pdf_dir = tmp_path / FIXTURE_PDF.stem
    assert output.preview_html == pdf_dir / "preview.html"
    pngs = sorted((pdf_dir / "images").glob("page_*.png"))
    assert pngs, "no page images were written"
    assert all(p.stat().st_size > 0 for p in pngs)


@pytest.mark.skipif(
    not FIXTURE_PDF.exists(),
    reason=f"fixture {FIXTURE_PDF} not available",
)
def test_pdf_engine_embeds_images_in_markdown(tmp_path: Path) -> None:
    """``embed_images=True`` produces a self-contained markdown file."""
    engine = PdfEngine(embed_images=True, images_scale=1.0, save_artifacts=False)
    output = engine.convert(FIXTURE_PDF, output_dir=tmp_path)

    assert output.succeeded, f"conversion failed: {output.errors}"
    assert output.markdown is not None
    # No bare placeholders should remain when images are embedded.
    assert "<!-- image -->" not in output.markdown
    # If the document contains any pictures, they appear as base64 data URIs.
    # (Some fixtures may have no pictures at all — accept that case too.)
    if "![" in output.markdown:
        assert "data:image" in output.markdown


@pytest.mark.skipif(
    not FIXTURE_PDF.exists(),
    reason=f"fixture {FIXTURE_PDF} not available",
)
def test_pdf_engine_writes_artifacts(tmp_path: Path) -> None:
    """``save_artifacts=True`` writes document.json, nodes.jsonl, and images."""
    engine = PdfEngine(images_scale=1.0, save_artifacts=True)
    output = engine.convert(FIXTURE_PDF, output_dir=tmp_path)

    assert output.succeeded, f"conversion failed: {output.errors}"
    pdf_dir = tmp_path / FIXTURE_PDF.stem

    assert output.document_json == pdf_dir / "document.json"
    assert output.document_json.exists()
    doc = json.loads(output.document_json.read_text(encoding="utf-8"))
    assert isinstance(doc, dict) and doc  # non-empty JSON object

    assert output.nodes_jsonl == pdf_dir / "nodes.jsonl"
    assert output.nodes_jsonl.exists()
    lines = output.nodes_jsonl.read_text(encoding="utf-8").splitlines()
    assert lines, "nodes.jsonl should not be empty"
    sample = json.loads(lines[0])
    # Every node carries our kind/level annotations and a label.
    assert "_kind" in sample and "_level" in sample and "label" in sample

    # All referenced images actually exist on disk.
    for img_path in output.picture_images + output.table_images:
        assert img_path.exists()
        assert img_path.stat().st_size > 0
        assert img_path.parent == pdf_dir / "images"

    # run.json captures the per-conversion snapshot for reproducibility.
    assert output.run_json == pdf_dir / "run.json"
    assert output.run_json.exists()
    run = json.loads(output.run_json.read_text(encoding="utf-8"))
    for key in (
        "schema_version",
        "source",
        "status",
        "timing",
        "engine_config",
        "pipeline_options",
        "models",
        "environment",
        "output_summary",
    ):
        assert key in run, f"run.json missing '{key}'"
    assert run["timing"]["duration_seconds"] > 0
    assert run["environment"]["python"]
    assert run["engine_config"]["save_artifacts"] is True
