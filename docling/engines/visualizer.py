"""HTML bounding-box viewer for :class:`PdfEngine` results.

Produces a single ``preview.html`` (plus one PNG per page) showing the
rendered page image with absolutely-positioned overlays for each layout
cluster. Hover surfaces the cluster metadata (label, confidence, cell
count, text preview) so a non-technical reviewer can see what the pipeline
captured at a glance.

The viewer reads from the live :class:`docling.datamodel.document.ConversionResult`
referenced by :attr:`PdfConversionOutput.raw` because page images and cluster
geometry are not part of the serialisable schema.
"""

from __future__ import annotations

import html
import json
import logging
from collections.abc import Iterable
from pathlib import Path

from docling.datamodel.base_models import Cluster, ConversionStatus, Page
from docling.datamodel.document import ConversionResult

_log = logging.getLogger(__name__)

# DocItemLabel → CSS colour. Anything not listed falls back to LABEL_DEFAULT.
LABEL_COLOURS: dict[str, str] = {
    "title": "#d62728",
    "section_header": "#ff7f0e",
    "text": "#1f77b4",
    "paragraph": "#1f77b4",
    "list_item": "#17becf",
    "caption": "#9467bd",
    "footnote": "#8c564b",
    "page_header": "#7f7f7f",
    "page_footer": "#7f7f7f",
    "table": "#2ca02c",
    "picture": "#e377c2",
    "chart": "#bcbd22",
    "formula": "#bcbd22",
    "code": "#e377c2",
    "reference": "#17becf",
}
LABEL_DEFAULT = "#888888"


class PreviewError(RuntimeError):
    """Raised when the viewer cannot produce a preview."""


def render_html_preview(
    result: ConversionResult,
    target_dir: Path,
    *,
    image_scale: float = 1.5,
    page_image_subdir: str = "images",
) -> Path:
    """Render an HTML viewer for *result* into *target_dir*.

    Writes ``preview.html`` and one PNG per page under
    ``target_dir/<page_image_subdir>/``. Returns the path to ``preview.html``.

    Raises
    ------
    PreviewError
        If the conversion has no pages or images were not generated (the
        engine must have been built with ``with_page_images=True``).
    """
    if result.status not in {
        ConversionStatus.SUCCESS,
        ConversionStatus.PARTIAL_SUCCESS,
    }:
        raise PreviewError(
            f"Cannot render preview from conversion with status {result.status}"
        )
    if not result.pages:
        raise PreviewError("Cannot render preview: result has no pages.")

    target_dir.mkdir(parents=True, exist_ok=True)
    images_dir = target_dir / page_image_subdir
    images_dir.mkdir(exist_ok=True)

    page_blocks: list[str] = []
    for page in result.pages:
        page_block = _render_page_block(page, images_dir, image_scale=image_scale)
        if page_block is not None:
            page_blocks.append(page_block)

    if not page_blocks:
        raise PreviewError(
            "No page images were rendered. Build PdfEngine with with_page_images=True."
        )

    html_doc = _HTML_TEMPLATE.format(
        title=html.escape(result.input.file.name if result.input else "preview"),
        legend=_render_legend(),
        pages="\n".join(page_blocks),
    )

    target = target_dir / "preview.html"
    target.write_text(html_doc, encoding="utf-8")
    _log.info("Wrote HTML preview to %s", target)
    return target


def _render_page_block(
    page: Page, images_dir: Path, *, image_scale: float
) -> str | None:
    image = page.get_image(scale=image_scale)
    if image is None or page.size is None:
        _log.warning(
            "Skipping page %s: no rendered image (set generate_page_images=True).",
            page.page_no,
        )
        return None

    image_path = images_dir / f"page_{page.page_no:04d}.png"
    image.save(image_path, format="PNG")

    layout = page.predictions.layout if page.predictions else None
    clusters: list[Cluster] = list(layout.clusters) if layout is not None else []

    overlays = "\n".join(
        _render_overlay(c, page_height=page.size.height, image_scale=image_scale)
        for c in _flatten(clusters)
    )

    rel_image = image_path.relative_to(images_dir.parent).as_posix()
    img_w = int(page.size.width * image_scale)
    img_h = int(page.size.height * image_scale)

    return _PAGE_TEMPLATE.format(
        page_no=page.page_no,
        cluster_count=sum(1 for _ in _flatten(clusters)),
        image_src=html.escape(rel_image),
        img_w=img_w,
        img_h=img_h,
        overlays=overlays,
    )


def _flatten(clusters: Iterable[Cluster]) -> Iterable[Cluster]:
    for c in clusters:
        yield c
        yield from _flatten(c.children)


def _render_overlay(cluster: Cluster, *, page_height: float, image_scale: float) -> str:
    tl = cluster.bbox.to_top_left_origin(page_height=page_height)
    left = tl.l * image_scale
    top = tl.t * image_scale
    width = (tl.r - tl.l) * image_scale
    height = (tl.b - tl.t) * image_scale

    label_value = (
        cluster.label.value if hasattr(cluster.label, "value") else str(cluster.label)
    )
    colour = LABEL_COLOURS.get(label_value, LABEL_DEFAULT)
    text_preview = " ".join(
        c.text for c in cluster.cells[:6] if getattr(c, "text", None)
    ).strip()
    if len(text_preview) > 240:
        text_preview = text_preview[:240] + "…"

    metadata = {
        "id": cluster.id,
        "label": label_value,
        "confidence": round(cluster.confidence, 3),
        "cells": len(cluster.cells),
        "bbox_pdf": [round(v, 1) for v in cluster.bbox.as_tuple()],
        "text": text_preview,
    }
    tooltip = html.escape(json.dumps(metadata, ensure_ascii=False, indent=2))

    return (
        f'<div class="bbox" data-label="{html.escape(label_value)}" '
        f'style="left:{left:.1f}px; top:{top:.1f}px; '
        f"width:{width:.1f}px; height:{height:.1f}px; "
        f'border-color:{colour}; background-color:{colour}22;" '
        f'title="{tooltip}">'
        f'<span class="bbox-tag" style="background:{colour};">{html.escape(label_value)}</span>'
        f"</div>"
    )


def _render_legend() -> str:
    items = "".join(
        f'<span class="legend-item"><span class="legend-swatch" '
        f'style="background:{colour};"></span>{html.escape(label)}</span>'
        for label, colour in LABEL_COLOURS.items()
    )
    return f'<div class="legend">{items}</div>'


_PAGE_TEMPLATE = """
<section class="page" id="page-{page_no}">
  <h2>Page {page_no} <small>({cluster_count} clusters)</small></h2>
  <div class="page-canvas" style="width:{img_w}px; height:{img_h}px;">
    <img src="{image_src}" width="{img_w}" height="{img_h}" alt="page {page_no}"/>
    {overlays}
  </div>
</section>
""".strip()


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Docling preview — {title}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0; padding: 0; background: #f3f3f4; color: #222;
  }}
  header {{
    position: sticky; top: 0; background: #fff; border-bottom: 1px solid #ddd;
    padding: 12px 20px; z-index: 10;
  }}
  header h1 {{ margin: 0; font-size: 16px; font-weight: 600; }}
  .legend {{ margin-top: 8px; font-size: 12px; display: flex; flex-wrap: wrap; gap: 12px; }}
  .legend-item {{ display: inline-flex; align-items: center; gap: 4px; }}
  .legend-swatch {{
    display: inline-block; width: 12px; height: 12px; border-radius: 2px;
  }}
  main {{ padding: 20px; }}
  section.page {{
    background: #fff; margin: 0 auto 32px; padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-radius: 4px; width: max-content;
  }}
  section.page h2 {{
    margin: 0 0 12px; font-size: 14px; font-weight: 600; color: #444;
  }}
  section.page h2 small {{ font-weight: 400; color: #888; margin-left: 8px; }}
  .page-canvas {{ position: relative; }}
  .page-canvas img {{ display: block; user-select: none; }}
  .bbox {{
    position: absolute; border: 2px solid; box-sizing: border-box;
    pointer-events: auto; cursor: help; transition: background-color 0.1s;
  }}
  .bbox:hover {{ background-color: rgba(255, 230, 0, 0.35) !important; z-index: 5; }}
  .bbox-tag {{
    position: absolute; top: -16px; left: -2px; padding: 1px 4px;
    color: #fff; font-size: 9px; font-weight: 600;
    border-radius: 2px 2px 0 0; white-space: nowrap; opacity: 0.85;
  }}
</style>
</head>
<body>
<header>
  <h1>Docling preview — {title}</h1>
  {legend}
</header>
<main>
{pages}
</main>
</body>
</html>
"""
