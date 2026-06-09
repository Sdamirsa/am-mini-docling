"""``amir-batch`` CLI — run :class:`PdfEngine` over one or more PDFs.

Usage:

    uv run amir-batch samples/              # every *.pdf in samples/
    uv run amir-batch samples/foo.pdf bar.pdf
    uv run amir-batch samples/ -o out/      # custom output root
    uv run amir-batch samples/ --compare    # full-page VLM A/B per PDF

The terminal report shows one row per PDF: status, duration, page count,
extracted figures (with noise count), tables, chunks, errors, and the path
to the per-PDF output folder.
"""

from __future__ import annotations

import datetime as _dt
import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from docling.engines.compare_pipelines import run_comparison
from docling.engines.pdf_engine import PdfEngine
from docling.engines.schemas import PdfConversionOutput

app = typer.Typer(
    add_completion=False,
    help="Batch-process PDFs through PdfEngine (Amir Engine).",
    rich_markup_mode="rich",
)

_log = logging.getLogger(__name__)


@app.command()
def main(
    inputs: Annotated[
        list[Path],
        typer.Argument(
            help=(
                "One or more PDF paths or directories. Directories are "
                "scanned (non-recursive) for ``*.pdf`` files."
            )
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Root output directory."),
    ] = Path("samples/out"),
    compare: Annotated[
        bool,
        typer.Option(
            "--compare/--no-compare",
            "-c",
            help="Run the standard-vs-full-page-VLM comparison per PDF.",
        ),
    ] = False,
    preview: Annotated[
        bool,
        typer.Option(
            "--preview/--no-preview",
            help="Render the clickable HTML bbox viewer per PDF.",
        ),
    ] = True,
    vlm_preset: Annotated[
        str,
        typer.Option(
            "--vlm-preset",
            help=(
                "Full-page VLM preset for the comparison mode (default "
                "``granite_docling`` — DocTags response yields a comparable "
                "DoclingDocument)."
            ),
        ),
    ] = "granite_docling",
    images_scale: Annotated[
        float,
        typer.Option(
            "--images-scale", help="Scale factor for rendered page / crop images."
        ),
    ] = 1.5,
    granite_vision_tables: Annotated[
        bool,
        typer.Option(
            "--granite-vision-tables/--no-granite-vision-tables",
            help=(
                "Use Granite-Vision VLM (3.2-2b) for table structure. "
                "Default on; turn off for plain TableFormer."
            ),
        ),
    ] = True,
    picture_description: Annotated[
        str,
        typer.Option(
            "--picture-description",
            help=(
                "VLM preset for figure captions. Default 'granite_vision_4b' "
                "(Granite-Vision 4.1-4b). Other values: 'granite_vision' "
                "(3.3-2b), 'smolvlm', 'pixtral', 'qwen25_vl_3b', or 'off'."
            ),
        ),
    ] = "granite_vision_4b",
) -> None:
    """Run ``PdfEngine`` (or the comparison runner) on every PDF found."""
    console = Console()
    pdf_paths = _collect_pdfs(inputs, console)
    if not pdf_paths:
        console.print("[red]No PDF files found.[/red]")
        raise typer.Exit(code=2)

    output_dir.mkdir(parents=True, exist_ok=True)

    mode = "compare" if compare else "single"
    console.rule(
        f"[bold]amir-batch[/bold] · mode=[cyan]{mode}[/cyan] · "
        f"{len(pdf_paths)} PDF{'s' if len(pdf_paths) != 1 else ''} → "
        f"[green]{output_dir}[/green]"
    )

    rows: list[dict] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task("processing", total=len(pdf_paths))
        for pdf_path in pdf_paths:
            progress.update(task_id, description=f"[cyan]{pdf_path.name}[/cyan]")
            try:
                row = (
                    _run_compare(
                        pdf_path,
                        output_dir,
                        vlm_preset=vlm_preset,
                        preview=preview,
                        images_scale=images_scale,
                        granite_vision_tables=granite_vision_tables,
                        picture_description=picture_description,
                    )
                    if compare
                    else _run_single(
                        pdf_path,
                        output_dir,
                        preview=preview,
                        images_scale=images_scale,
                        granite_vision_tables=granite_vision_tables,
                        picture_description=picture_description,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive
                _log.exception("processing %s failed", pdf_path.name)
                row = {
                    "name": pdf_path.name,
                    "status": "EXCEPTION",
                    "duration": "—",
                    "pages": "—",
                    "figures": "—",
                    "tables": "—",
                    "chunks": "—",
                    "errors": str(exc)[:60],
                    "output": "—",
                }
            rows.append(row)
            progress.advance(task_id)

    _render_summary(console, rows, mode=mode)
    if any(r.get("status", "").startswith(("FAILURE", "EXCEPTION")) for r in rows):
        raise typer.Exit(code=1)


def _collect_pdfs(inputs: list[Path], console: Console) -> list[Path]:
    paths: list[Path] = []
    for entry in inputs:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("*.pdf")))
        elif entry.is_file() and entry.suffix.lower() == ".pdf":
            paths.append(entry)
        else:
            console.print(f"[yellow]skipping[/yellow] {entry} (not a PDF or dir)")
    # Stable, deduplicated.
    return sorted({p.resolve() for p in paths})


def _run_single(
    pdf_path: Path,
    output_dir: Path,
    *,
    preview: bool,
    images_scale: float,
    granite_vision_tables: bool,
    picture_description: str,
) -> dict:
    engine = PdfEngine(
        images_scale=images_scale,
        granite_vision_tables=granite_vision_tables,
        picture_description=(
            picture_description if picture_description != "off" else None  # type: ignore[arg-type]
        ),
    )
    t0 = _dt.datetime.now(_dt.timezone.utc)
    out = engine.convert(pdf_path, output_dir=output_dir, make_html_preview=preview)
    duration_s = (_dt.datetime.now(_dt.timezone.utc) - t0).total_seconds()
    return _row_from_output(pdf_path, out, duration_s)


def _run_compare(
    pdf_path: Path,
    output_dir: Path,
    *,
    vlm_preset: str,
    preview: bool,
    images_scale: float,
    granite_vision_tables: bool,
    picture_description: str,
) -> dict:
    t0 = _dt.datetime.now(_dt.timezone.utc)
    res = run_comparison(
        pdf_path,
        output_dir,
        vlm_preset=vlm_preset,
        make_html_preview=preview,
        standard_kwargs={
            "images_scale": images_scale,
            "granite_vision_tables": granite_vision_tables,
            "picture_description": (
                picture_description if picture_description != "off" else None
            ),
        },
    )
    duration_s = (_dt.datetime.now(_dt.timezone.utc) - t0).total_seconds()
    row = _row_from_output(pdf_path, res.standard, duration_s)
    row["name"] = f"{pdf_path.name} · cmp"
    row["output"] = str(res.pdf_dir)
    return row


def _row_from_output(
    pdf_path: Path, out: PdfConversionOutput, duration_s: float
) -> dict:
    noise_count = 0
    if out.figures_jsonl is not None and out.figures_jsonl.exists():
        import json

        with out.figures_jsonl.open() as fh:
            noise_count = sum(1 for line in fh if json.loads(line).get("is_noise"))
    chunks_count = 0
    if out.chunks_jsonl is not None and out.chunks_jsonl.exists():
        with out.chunks_jsonl.open() as fh:
            chunks_count = sum(1 for _ in fh)
    figures_label = f"{len(out.picture_images)} ({noise_count} noise)"
    return {
        "name": pdf_path.name,
        "status": str(out.status).split(".")[-1],
        "duration": f"{duration_s:.1f}s",
        "pages": str(out.page_count),
        "figures": figures_label,
        "tables": str(len(out.table_images)),
        "chunks": str(chunks_count),
        "errors": str(len(out.errors)),
        "output": str(out.output_dir) if out.output_dir is not None else "—",
    }


def _render_summary(console: Console, rows: list[dict], *, mode: str) -> None:
    table = Table(
        title=f"amir-batch summary ({mode})",
        show_lines=False,
        header_style="bold",
    )
    table.add_column("PDF", overflow="fold")
    table.add_column("status")
    table.add_column("dur", justify="right")
    table.add_column("pages", justify="right")
    table.add_column("figures")
    table.add_column("tables", justify="right")
    table.add_column("chunks", justify="right")
    table.add_column("errs", justify="right")
    table.add_column("output", overflow="fold")
    for row in rows:
        status_style = (
            "green"
            if row["status"].startswith("SUCCESS")
            else "yellow"
            if row["status"].startswith("PARTIAL")
            else "red"
        )
        table.add_row(
            row["name"],
            f"[{status_style}]{row['status']}[/{status_style}]",
            row["duration"],
            row["pages"],
            row["figures"],
            row["tables"],
            row["chunks"],
            row["errors"],
            row["output"],
        )
    console.print(table)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(app())
