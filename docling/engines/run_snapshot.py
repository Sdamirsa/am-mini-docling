"""Per-PDF ``run.json`` snapshot: environment, timing, models, and config.

Written alongside ``document.json`` / ``nodes.jsonl`` so any downstream agent
or reviewer can reproduce *which* pipeline produced *this* output and on
which environment, without needing to re-read the source code.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_RUN_JSON_FILENAME = "run.json"
_SCHEMA_VERSION = "1"

_TRACKED_PACKAGES = (
    "docling",
    "docling-core",
    "docling-ibm-models",
    "docling-parse",
    "onnxruntime",
    "onnxruntime-gpu",
    "pypdfium2",
    "transformers",
)


def write_run_snapshot(
    pdf_dir: Path,
    *,
    source: str,
    source_kind: str,
    status: str,
    started_at: _dt.datetime,
    finished_at: _dt.datetime,
    engine_config: dict[str, Any],
    pipeline_options: dict[str, Any] | None,
    page_count: int,
    pictures_extracted: int,
    tables_extracted: int,
    errors: list[dict[str, Any]],
) -> Path:
    """Write ``<pdf_dir>/run.json`` and return its path."""
    pdf_dir.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "schema_version": _SCHEMA_VERSION,
        "source": _source_block(source, source_kind),
        "status": status,
        "timing": _timing_block(started_at, finished_at),
        "engine_config": engine_config,
        "pipeline_options": pipeline_options,
        "models": _models_summary(pipeline_options),
        "environment": _environment_block(),
        "output_summary": {
            "page_count": page_count,
            "pictures_extracted": pictures_extracted,
            "tables_extracted": tables_extracted,
            "error_count": len(errors),
        },
        "errors": errors,
    }

    target = pdf_dir / _RUN_JSON_FILENAME
    target.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    _log.info("Wrote run snapshot to %s", target)
    return target


def _source_block(source: str, source_kind: str) -> dict[str, Any]:
    block: dict[str, Any] = {"input": source, "source_kind": source_kind}
    if source_kind == "local_path":
        p = Path(source)
        block["file_name"] = p.name
        if p.exists():
            block["file_size_bytes"] = p.stat().st_size
    return block


def _timing_block(
    started_at: _dt.datetime, finished_at: _dt.datetime
) -> dict[str, Any]:
    duration = (finished_at - started_at).total_seconds()
    return {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round(duration, 3),
    }


def _models_summary(pipeline_options: dict[str, Any] | None) -> dict[str, Any]:
    """Flat per-stage summary for quick inspection — pipeline_options has the full data."""
    if not pipeline_options:
        return {}
    summary: dict[str, Any] = {}
    for key in (
        "layout_options",
        "ocr_options",
        "table_structure_options",
        "picture_description_options",
        "picture_classification_options",
        "code_formula_options",
        "chart_extraction_options",
        "accelerator_options",
    ):
        if key in pipeline_options:
            summary[key.removesuffix("_options")] = pipeline_options[key]
    summary["do_ocr"] = pipeline_options.get("do_ocr")
    summary["do_table_structure"] = pipeline_options.get("do_table_structure")
    summary["do_picture_classification"] = pipeline_options.get(
        "do_picture_classification"
    )
    summary["do_code_enrichment"] = pipeline_options.get("do_code_enrichment")
    summary["do_formula_enrichment"] = pipeline_options.get("do_formula_enrichment")
    summary["do_chart_extraction"] = pipeline_options.get("do_chart_extraction")
    return summary


def _environment_block() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "packages": _package_versions(),
    }


def _package_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for pkg in _TRACKED_PACKAGES:
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = None
    return out
