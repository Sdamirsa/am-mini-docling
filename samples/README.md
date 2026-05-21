# Samples

Drop test PDFs in this folder (e.g. `samples/my-paper.pdf`). Files here are
gitignored except for this README.

## Convert + write markdown

```bash
uv run python -c "
from pathlib import Path
from docling.engines import PdfEngine

out = PdfEngine().convert(
    Path('samples/my-paper.pdf'),
    output_dir=Path('samples/out'),
)
print('status :', out.status)
print('pages  :', out.page_count)
print('md     :', (out.markdown or '')[:200], '...')
print('saved  :', out.output_dir)
"
```

## Convert + open HTML bounding-box viewer

```bash
uv run python -c "
from pathlib import Path
from docling.engines import PdfEngine

out = PdfEngine(with_page_images=True, images_scale=1.5).convert(
    Path('samples/my-paper.pdf'),
    output_dir=Path('samples/out'),
    make_html_preview=True,
)
print('preview:', out.preview_html)
"
# then:
xdg-open samples/out/preview.html       # Linux
open samples/out/preview.html           # macOS
```

The viewer shows each rendered page with overlay rectangles for every detected
layout cluster. Hover any rectangle to see its metadata (label, confidence,
cell count, PDF-coord bbox, text preview). Colours encode the cluster label —
see the legend in the page header.

## URL inputs (no local file needed)

```python
out = PdfEngine().convert("https://arxiv.org/pdf/2206.01062")
```
