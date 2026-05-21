# Samples

Drop test PDFs in this folder (e.g. `samples/my-paper.pdf`). Files here are
gitignored except for this README.

## Convert (default — full artifact bundle)

```bash
uv run python -c "
from pathlib import Path
from docling.engines import PdfEngine

out = PdfEngine(images_scale=1.5).convert(
    Path('samples/my-paper.pdf'),
    output_dir=Path('samples/out'),
    make_html_preview=True,
)
print('status :', out.status)
print('pages  :', out.page_count)
print('saved  :', out.output_dir)
print('preview:', out.preview_html)
"
# then open the clickable viewer
xdg-open samples/out/my-paper/preview.html   # Linux
open samples/out/my-paper/preview.html       # macOS
```

## What lands in `samples/out/<pdf-stem>/`

| File | Content |
|---|---|
| `<pdf-stem>.md` | Markdown export. With `PdfEngine(embed_images=True)` images are inlined as base64 data URIs, producing a standalone `.md`. |
| `document.json` | Full `DoclingDocument` serialisation (canonical, round-trippable). |
| `nodes.jsonl` | One JSON object per node from `iterate_items()` — label, bbox/page (`prov`), text, captions, table cells, plus `_kind`, `_level`, and `image_path` for pictures/tables. |
| `run.json` | Reproducibility snapshot: schema version, source, status, timing, engine config, full `pipeline_options` (incl. model spec), per-stage models summary, environment (python, platform, machine, package versions), output summary, errors. |
| `images/page_NNNN.png` | Page renders. |
| `images/picture_NNN.png` | Extracted figures (`PictureItem.get_image()`). |
| `images/table_NNN.png` | Extracted tables (`TableItem.get_image()`). |
| `preview.html` | Bounding-box viewer — **click any box** to open a side panel with that node's full metadata (same data as `nodes.jsonl`). Press `Esc` to clear. |

## Useful flags

```python
PdfEngine(
    save_artifacts=True,   # default — writes document.json + nodes.jsonl + image crops + run.json
    embed_images=True,     # markdown becomes standalone (base64 data URIs)
    with_page_images=True, # explicit; redundant when save_artifacts=True
    images_scale=1.5,      # render scale for page / picture / table crops
)
```

## URL inputs (no local file needed)

```python
out = PdfEngine().convert("https://arxiv.org/pdf/2206.01062")
```
