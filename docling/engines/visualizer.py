"""HTML bounding-box viewer for :class:`PdfEngine` results.

Produces a single ``preview.html`` (plus one PNG per page) showing each page
image with absolutely-positioned overlays — one per :class:`DocItem` from
:meth:`DoclingDocument.iterate_items`. Hover surfaces a short label tag;
clicking a box opens a side panel with the node's full metadata
(self_ref, label, level, prov/bbox, text, captions, table data, …) — the
same data that's persisted to ``nodes.jsonl``.
"""

from __future__ import annotations

import html
import json
import logging
from pathlib import Path

from docling.datamodel.base_models import ConversionStatus, Page
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
    """Render an HTML viewer for *result* into *target_dir*."""
    if result.status not in {
        ConversionStatus.SUCCESS,
        ConversionStatus.PARTIAL_SUCCESS,
    }:
        raise PreviewError(
            f"Cannot render preview from conversion with status {result.status}"
        )
    if not result.pages:
        raise PreviewError("Cannot render preview: result has no pages.")
    if result.document is None:
        raise PreviewError("Cannot render preview: result has no document.")

    target_dir.mkdir(parents=True, exist_ok=True)
    images_dir = target_dir / page_image_subdir
    images_dir.mkdir(exist_ok=True)

    items_by_page = _index_items_by_page(result)

    page_blocks: list[str] = []
    for page in result.pages:
        page_block = _render_page_block(
            page,
            items_by_page.get(page.page_no, []),
            images_dir,
            image_scale=image_scale,
        )
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


def _index_items_by_page(result: ConversionResult) -> dict[int, list[tuple]]:
    """Group ``iterate_items()`` output by page (one entry per prov)."""
    by_page: dict[int, list[tuple]] = {}
    for item, level in result.document.iterate_items():
        prov_list = getattr(item, "prov", None) or []
        for prov_idx, prov in enumerate(prov_list):
            by_page.setdefault(prov.page_no, []).append((item, level, prov_idx, prov))
    return by_page


def _render_page_block(
    page: Page,
    page_items: list[tuple],
    images_dir: Path,
    *,
    image_scale: float,
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

    overlays = "\n".join(
        _render_overlay(
            item,
            level,
            prov_idx,
            prov,
            page_height=page.size.height,
            image_scale=image_scale,
        )
        for (item, level, prov_idx, prov) in page_items
    )

    rel_image = image_path.relative_to(images_dir.parent).as_posix()
    img_w = int(page.size.width * image_scale)
    img_h = int(page.size.height * image_scale)

    return _PAGE_TEMPLATE.format(
        page_no=page.page_no,
        item_count=len(page_items),
        image_src=html.escape(rel_image),
        img_w=img_w,
        img_h=img_h,
        overlays=overlays,
    )


def _render_overlay(
    item,
    level: int,
    prov_idx: int,
    prov,
    *,
    page_height: float,
    image_scale: float,
) -> str:
    tl = prov.bbox.to_top_left_origin(page_height=page_height)
    left = tl.l * image_scale
    top = tl.t * image_scale
    width = (tl.r - tl.l) * image_scale
    height = (tl.b - tl.t) * image_scale

    label_value = item.label.value if hasattr(item.label, "value") else str(item.label)
    colour = LABEL_COLOURS.get(label_value, LABEL_DEFAULT)

    node = _node_to_dict(item, level)
    node["_prov_index"] = prov_idx
    node_json = html.escape(json.dumps(node, ensure_ascii=False, indent=2))

    self_ref = getattr(item, "self_ref", "") or ""
    tag_label = label_value

    return (
        f'<div class="bbox" data-label="{html.escape(label_value)}" '
        f'data-self-ref="{html.escape(self_ref)}" '
        f'data-meta="{node_json}" '
        f'style="left:{left:.1f}px; top:{top:.1f}px; '
        f"width:{width:.1f}px; height:{height:.1f}px; "
        f'border-color:{colour}; background-color:{colour}22;">'
        f'<span class="bbox-tag" style="background:{colour};">{html.escape(tag_label)}</span>'
        f"</div>"
    )


def _node_to_dict(item, level: int) -> dict:
    """Serialise a document item to a JSON-friendly dict (matches artifacts.py)."""
    dumped = item.model_dump(mode="json", exclude={"image"})
    dumped["_kind"] = type(item).__name__
    dumped["_level"] = level
    return dumped


def _render_legend() -> str:
    items = "".join(
        f'<span class="legend-item"><span class="legend-swatch" '
        f'style="background:{colour};"></span>{html.escape(label)}</span>'
        for label, colour in LABEL_COLOURS.items()
    )
    return f'<div class="legend">{items}</div>'


_PAGE_TEMPLATE = """
<section class="page" id="page-{page_no}">
  <h2>Page {page_no} <small>({item_count} nodes)</small></h2>
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
  header .hint {{ color: #777; font-size: 12px; margin-top: 4px; }}
  .legend {{ margin-top: 8px; font-size: 12px; display: flex; flex-wrap: wrap; gap: 12px; }}
  .legend-item {{ display: inline-flex; align-items: center; gap: 4px; }}
  .legend-swatch {{
    display: inline-block; width: 12px; height: 12px; border-radius: 2px;
  }}
  main {{ padding: 20px; padding-right: 440px; }}
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
    pointer-events: auto; cursor: pointer; transition: background-color 0.1s;
  }}
  .bbox:hover {{ background-color: rgba(255, 230, 0, 0.35) !important; z-index: 5; }}
  .bbox.selected {{
    background-color: rgba(255, 200, 0, 0.55) !important;
    z-index: 6; outline: 2px solid #000;
  }}
  .bbox-tag {{
    position: absolute; top: -16px; left: -2px; padding: 1px 4px;
    color: #fff; font-size: 9px; font-weight: 600;
    border-radius: 2px 2px 0 0; white-space: nowrap; opacity: 0.85;
    pointer-events: none;
  }}
  #panel {{
    position: fixed; top: 0; right: 0; width: 420px; height: 100vh;
    background: #fff; border-left: 1px solid #ddd; box-shadow: -2px 0 6px rgba(0,0,0,0.05);
    display: flex; flex-direction: column; z-index: 20;
  }}
  #panel header {{
    position: static; padding: 12px 16px; background: #fafafa;
    border-bottom: 1px solid #eee; flex-shrink: 0;
  }}
  #panel header h2 {{ margin: 0; font-size: 14px; font-weight: 600; color: #333; }}
  #panel header .self-ref {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 11px; color: #666; margin-top: 2px;
  }}
  #panel-body {{
    flex: 1; overflow: auto; padding: 12px 16px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12px; line-height: 1.5; white-space: pre-wrap; word-break: break-word;
  }}
  #panel-empty {{ color: #888; font-style: italic; }}
  #panel-close {{
    float: right; border: 0; background: transparent; cursor: pointer;
    color: #888; font-size: 16px; padding: 0; margin-left: 8px;
  }}
  #panel-close:hover {{ color: #222; }}
</style>
</head>
<body>
<header>
  <h1>Docling preview — {title}</h1>
  <div class="hint">Click any bounding box to inspect the full node metadata.</div>
  {legend}
</header>
<main>
{pages}
</main>
<aside id="panel">
  <header>
    <button id="panel-close" title="Clear selection">&times;</button>
    <h2 id="panel-title">Node inspector</h2>
    <div class="self-ref" id="panel-self-ref"></div>
  </header>
  <div id="panel-body">
    <span id="panel-empty">Click a bounding box to see its full metadata here.</span>
  </div>
</aside>
<script>
(function() {{
  const panelTitle = document.getElementById('panel-title');
  const panelSelfRef = document.getElementById('panel-self-ref');
  const panelBody = document.getElementById('panel-body');
  const panelClose = document.getElementById('panel-close');
  let selected = null;

  function clearSelection() {{
    if (selected) selected.classList.remove('selected');
    selected = null;
    panelTitle.textContent = 'Node inspector';
    panelSelfRef.textContent = '';
    panelBody.innerHTML = '<span id="panel-empty">Click a bounding box to see its full metadata here.</span>';
  }}

  function showNode(box) {{
    if (selected) selected.classList.remove('selected');
    box.classList.add('selected');
    selected = box;
    const label = box.dataset.label || '(unlabelled)';
    const selfRef = box.dataset.selfRef || '';
    const meta = box.dataset.meta || '{{}}';
    panelTitle.textContent = label;
    panelSelfRef.textContent = selfRef;
    try {{
      const obj = JSON.parse(meta);
      panelBody.textContent = JSON.stringify(obj, null, 2);
    }} catch (e) {{
      panelBody.textContent = meta;
    }}
  }}

  document.querySelectorAll('.bbox').forEach(function(box) {{
    box.addEventListener('click', function(e) {{
      e.stopPropagation();
      showNode(box);
    }});
  }});

  panelClose.addEventListener('click', clearSelection);
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') clearSelection();
  }});
}})();
</script>
</body>
</html>
"""
