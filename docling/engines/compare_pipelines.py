"""Side-by-side comparison: standard PdfEngine vs full-page VlmPipeline.

Runs the same PDF through two pipelines:

* ``standard/`` — the regular :class:`PdfEngine` (layout + OCR + tables +
  optional VLM picture description), producing the full artifact bundle
  (markdown, document.json, nodes.jsonl, chunks.jsonl, tables.jsonl,
  figures.jsonl, run.json, preview.html).
* ``full_page_vlm/`` — Docling's :class:`VlmPipeline` driven by a single
  full-page VLM. Default is **GraniteDocling** (DocTags response →
  produces a full :class:`DoclingDocument`, so all the downstream artifact
  writers run too). If you override to a markdown-only VLM (Qwen,
  Pixtral…), the resulting ``DoclingDocument`` is a single text node and
  ``nodes.jsonl`` / ``tables.jsonl`` / ``figures.jsonl`` will be sparse —
  this caveat is logged into the comparison summary.

Writes ``<output_dir>/<stem>/comparison.md`` with side-by-side stats so a
human (or another agent) can compare the two without re-running anything.
"""

from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.engines.pdf_engine import PdfEngine
from docling.engines.schemas import PdfConversionOutput
from docling.pipeline.vlm_pipeline import VlmPipeline

_log = logging.getLogger(__name__)

_DOCTAGS_PRESETS = frozenset({"granite_docling", "smoldocling"})


@dataclass
class ComparisonResult:
    """Paths and outputs from one comparison run."""

    pdf_dir: Path
    standard: PdfConversionOutput
    full_page_vlm: PdfConversionOutput
    standard_dir: Path
    full_page_vlm_dir: Path
    comparison_md: Path


def run_comparison(
    pdf_path: Path | str,
    output_dir: Path,
    *,
    vlm_preset: str = "granite_docling",
    standard_kwargs: dict[str, Any] | None = None,
    make_html_preview: bool = True,
) -> ComparisonResult:
    """Run both pipelines on *pdf_path* and write ``comparison.md``.

    Parameters
    ----------
    pdf_path
        Local PDF path or ``http(s)://`` URL.
    output_dir
        Parent directory; this function writes to
        ``<output_dir>/<pdf-stem>/{standard,full_page_vlm,comparison.md}``.
    vlm_preset
        Docling VlmConvert preset id for the full-page VLM. Defaults to
        ``"granite_docling"`` because its DocTags response yields a real
        DoclingDocument (so both subfolders produce comparable bundles).
        Other presets work but markdown-only VLMs produce only ``markdown``
        in the second folder.
    standard_kwargs
        Forwarded to :class:`PdfEngine` for the ``standard/`` run.
    make_html_preview
        Whether to render ``preview.html`` for each side. Default True.
    """
    pdf_path = (
        Path(pdf_path)
        if not str(pdf_path).startswith(("http://", "https://"))
        else pdf_path
    )
    stem = (pdf_path.stem if isinstance(pdf_path, Path) else "document").replace(
        " ", "_"
    )
    pdf_dir = output_dir / stem
    standard_dir = pdf_dir / "standard"
    full_page_dir = pdf_dir / "full_page_vlm"
    standard_dir.mkdir(parents=True, exist_ok=True)
    full_page_dir.mkdir(parents=True, exist_ok=True)

    # ---- Standard pipeline -------------------------------------------------
    _log.info("[comparison] running standard pipeline → %s", standard_dir)
    standard_t0 = _dt.datetime.now(_dt.timezone.utc)
    standard_engine = PdfEngine(**(standard_kwargs or {}))
    # PdfEngine writes into <output_dir>/<stem>/... so we point it at the
    # parent of standard_dir so the final folder name matches.
    standard_out = standard_engine.convert(
        pdf_path,
        output_dir=standard_dir.parent,
        make_html_preview=make_html_preview,
    )
    # PdfEngine creates a subfolder named after the PDF stem; rename to "standard".
    _rename_pdf_dir(standard_out, standard_dir)
    standard_t1 = _dt.datetime.now(_dt.timezone.utc)

    # ---- Full-page VLM pipeline -------------------------------------------
    _log.info("[comparison] running full-page VLM (%s) → %s", vlm_preset, full_page_dir)
    vlm_t0 = _dt.datetime.now(_dt.timezone.utc)
    vlm_converter = _build_vlm_converter(vlm_preset)
    vlm_engine = PdfEngine(
        converter=vlm_converter, save_artifacts=True, embed_images=False
    )
    vlm_out = vlm_engine.convert(
        pdf_path,
        output_dir=full_page_dir.parent,
        make_html_preview=make_html_preview,
    )
    _rename_pdf_dir(vlm_out, full_page_dir)
    vlm_t1 = _dt.datetime.now(_dt.timezone.utc)

    # ---- Summary ----------------------------------------------------------
    comparison_md = pdf_dir / "comparison.md"
    comparison_md.write_text(
        _render_comparison_md(
            pdf_path=pdf_path,
            standard=standard_out,
            full_page=vlm_out,
            vlm_preset=vlm_preset,
            standard_duration_s=(standard_t1 - standard_t0).total_seconds(),
            vlm_duration_s=(vlm_t1 - vlm_t0).total_seconds(),
        ),
        encoding="utf-8",
    )
    _log.info("[comparison] wrote %s", comparison_md)

    return ComparisonResult(
        pdf_dir=pdf_dir,
        standard=standard_out,
        full_page_vlm=vlm_out,
        standard_dir=standard_dir,
        full_page_vlm_dir=full_page_dir,
        comparison_md=comparison_md,
    )


def _build_vlm_converter(preset: str) -> DocumentConverter:
    vlm_options = VlmConvertOptions.from_preset(preset)
    pipeline_options = VlmPipelineOptions(vlm_options=vlm_options)
    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline, pipeline_options=pipeline_options
            )
        },
    )


def _rename_pdf_dir(output: PdfConversionOutput, target_dir: Path) -> None:
    """Move whatever ``PdfEngine`` wrote into the target subfolder name."""
    src = output.output_dir
    if src is None or src == target_dir:
        return
    if target_dir.exists():
        # Clean target so the rename is atomic-ish.
        import shutil

        shutil.rmtree(target_dir)
    src.rename(target_dir)
    output.output_dir = target_dir
    # Patch up other path fields so callers see the new location.
    for attr in (
        "document_json",
        "nodes_jsonl",
        "chunks_jsonl",
        "tables_jsonl",
        "figures_jsonl",
        "run_json",
        "preview_html",
        "markdown_embedded_path",
    ):
        old: Path | None = getattr(output, attr, None)
        if old is None:
            continue
        try:
            rel = old.relative_to(src)
        except ValueError:
            continue
        setattr(output, attr, target_dir / rel)
    output.picture_images = [
        target_dir / p.relative_to(src) for p in output.picture_images
    ]
    output.table_images = [target_dir / p.relative_to(src) for p in output.table_images]


def _render_comparison_md(
    *,
    pdf_path: Path | str,
    standard: PdfConversionOutput,
    full_page: PdfConversionOutput,
    vlm_preset: str,
    standard_duration_s: float,
    vlm_duration_s: float,
) -> str:
    def _md_size(path: Path | None) -> int:
        return path.stat().st_size if path is not None and path.exists() else 0

    def _first_lines(path: Path | None, n: int = 8) -> str:
        if path is None or not path.exists():
            return "_(no markdown produced)_"
        lines = path.read_text(encoding="utf-8").splitlines()[:n]
        return "\n".join(f"> {line}" for line in lines)

    standard_md = (
        standard.output_dir / f"{standard.output_dir.name}.md"
        if standard.output_dir
        else None
    )
    full_md = (
        full_page.output_dir / f"{full_page.output_dir.name}.md"
        if full_page.output_dir
        else None
    )

    caveat = ""
    if vlm_preset not in _DOCTAGS_PRESETS:
        caveat = (
            f"\n> ⚠ The full-page VLM preset `{vlm_preset}` emits markdown, not "
            "DocTags. The `full_page_vlm/` folder will have a markdown export "
            "but a sparse `nodes.jsonl` / `tables.jsonl` / `figures.jsonl` "
            "because the document graph couldn't be reconstructed from "
            "markdown.\n"
        )

    return f"""# Pipeline comparison — {Path(str(pdf_path)).name}

Two pipelines, same input. See `standard/` and `full_page_vlm/` for the full artifact bundles.
{caveat}
| Metric | standard | full_page_vlm ({vlm_preset}) |
|---|---|---|
| Status | `{standard.status}` | `{full_page.status}` |
| Duration | {standard_duration_s:.2f}s | {vlm_duration_s:.2f}s |
| Page count | {standard.page_count} | {full_page.page_count} |
| Pictures extracted | {len(standard.picture_images)} | {len(full_page.picture_images)} |
| Tables extracted | {len(standard.table_images)} | {len(full_page.table_images)} |
| Chunks | {_count_lines(standard.chunks_jsonl)} | {_count_lines(full_page.chunks_jsonl)} |
| Tables in JSONL | {_count_lines(standard.tables_jsonl)} | {_count_lines(full_page.tables_jsonl)} |
| Figures in JSONL | {_count_lines(standard.figures_jsonl)} | {_count_lines(full_page.figures_jsonl)} |
| Errors | {len(standard.errors)} | {len(full_page.errors)} |
| Markdown size | {_md_size(standard_md):,} bytes | {_md_size(full_md):,} bytes |
| HTML preview | `{_rel(standard.preview_html)}` | `{_rel(full_page.preview_html)}` |

## Standard — first lines of markdown

{_first_lines(standard_md)}

## Full-page VLM — first lines of markdown

{_first_lines(full_md)}
"""


def _count_lines(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    with path.open() as fh:
        return sum(1 for _ in fh)


def _rel(p: Path | None) -> str:
    return str(p) if p is not None else "(none)"
