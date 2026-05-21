# Amir Engine — Current Stage

Live tracker for the build defined in [AMIR_TODO.md](AMIR_TODO.md). Keep entries short; update when starting or finishing a task.

## Current phase

**PHASE 1 — Foundation (PDF→Structured Conversion)** — **COMPLETE.** All 9 tests green; smoke-tested on `samples/test-pdf-ai-manuscript.pdf` (8 pages, 0 errors, 7 figures + 5 tables extracted, `run.json` captures env + timing + models).

### Phase 1 status

| TODO item | State | Notes |
|---|---|---|
| `docling/engines/pdf_engine.py` wrapper | ✅ done | Thin facade over `DocumentConverter`. |
| Output schemas | ✅ done | Landed at `docling/engines/schemas.py` (not `docling/models/engine_output.py` — `docling/models/` is reserved for upstream ML model wrappers). |
| Input validation | ✅ done | Landed at `docling/engines/validation.py` (not `docling/utils/`) so all Amir code lives in one subtree. |
| `tests/test_engines/test_pdf_engine.py` | ✅ done | Real fixture: `tests/data/pdf/2305.03393v1-pg9.pdf`. 4 e2e tests + 5 unit tests. |
| Local paths + URLs | ✅ done | `classify_source()` + `validate_pdf_source()`. |
| Error handling + logging | ✅ done | Catches `ConversionError`; `_log = logging.getLogger(__name__)`. |
| HTML bbox visualiser (clickable) | ✅ done | `docling/engines/visualizer.py` — overlays are one-per-`DocItem` from `iterate_items()`, **click any bbox** to open a side panel with the node's full metadata; Esc to clear. |
| Standalone markdown | ✅ done | `PdfEngine(embed_images=True)` → base64 data URIs, no external image refs. |
| Per-PDF output folder | ✅ done | All artifacts land under `<output_dir>/<pdf-stem>/` (sanitised). |
| Persistent data nodes | ✅ done | `docling/engines/artifacts.py` — writes `document.json` (full `DoclingDocument`), `nodes.jsonl` (one line per node with bbox/text/captions/table data + `image_path` for pictures/tables), and `images/picture_NNN.png` / `table_NNN.png` via `PictureItem.get_image()` / `TableItem.get_image()`. |
| Run snapshot | ✅ done | `docling/engines/run_snapshot.py` — `<pdf-dir>/run.json` with schema_version, source, status, timing (started_at / finished_at / duration_seconds), engine_config, full pipeline_options (`serialize_as_any=True` so subclass fields like `layout_options.model_spec` survive), per-stage models summary, environment (python, platform, machine, system, tracked package versions), output_summary, errors. Hostname intentionally **not** captured. |

### Path deviations from the TODO

Two paths were quietly corrected during implementation:

- `docling/models/engine_output.py` → **`docling/engines/schemas.py`**
- `docling/utils/validation.py` → **`docling/engines/validation.py`**

Reason: `docling/models/` holds upstream's ML-model wrappers (layout, OCR, VLM); putting Pydantic data schemas there is a naming collision waiting to happen. Same logic for `docling/utils/`. Keeping all Amir Engine code under `docling/engines/` makes future upstream merges easier.

## Per-PDF output layout (Phase 1 deliverable)

```
out/<pdf-stem>/
├── <pdf-stem>.md            # markdown (standalone if PdfEngine(embed_images=True))
├── document.json            # full DoclingDocument (round-trippable)
├── nodes.jsonl              # one JSON object per node: label, prov/bbox, text,
│                            # captions, table data, _kind, _level, image_path
├── run.json                 # schema_version, source, status, timing,
│                            # engine_config, pipeline_options, models summary,
│                            # environment, output_summary, errors
├── images/
│   ├── page_NNNN.png        # page renders
│   ├── picture_NNN.png      # PictureItem.get_image() crops
│   └── table_NNN.png        # TableItem.get_image() crops
└── preview.html             # bbox viewer — click any box for full node metadata
```

`PdfEngine(save_artifacts=True)` (default) auto-enables `generate_page_images` + `generate_picture_images` so the figure/table crops are available.

## Next action

Move to **PHASE 2 — Content Extraction (Text / Image / Table)** per [AMIR_TODO.md](AMIR_TODO.md). Phase 1 already persists the raw node graph (`nodes.jsonl`) + extracted figure/table images — Phase 2's job is to *consume* those artifacts and emit a hierarchical text + image + table data product (sectioned text, captioned images with metadata, cell-level tables) ready for VLM (Phase 3) and LLM (Phase 4) layers.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-05-21 | — | `.claude/` workspace initialised. |
| 2026-05-21 | 1 | `.claude/` re-scaffolded via `claude-folder-handler` (packs: data-science, llm-app, llm-extraction, security-hardening, visualization). Amir files restored on top. |
| 2026-05-21 | 1 | Foundation code landed: `docling/engines/{__init__,schemas,validation,pdf_engine}.py` + `tests/test_engines/test_pdf_engine.py`. |
| 2026-05-21 | 1 | HTML bbox visualiser landed: `docling/engines/visualizer.py`, wired into `PdfEngine` via `make_html_preview=True`. 7/7 tests pass. Smoke-tested on `samples/test-pdf-ai-manuscript.pdf`. |
| 2026-05-21 | 1 | Dev env: `--all-extras` unusable on aarch64 (no `onnxruntime-gpu` wheel). Working install: `uv sync --frozen --group dev --no-group docs --no-group examples --extra standard`. See [REPO_CONTEXT.md](REPO_CONTEXT.md) for full notes. |
| 2026-05-21 | 1 | Per-PDF subfolder layout + `embed_images=True` standalone markdown landed in `PdfEngine`. |
| 2026-05-21 | 1 | Reading-order column-flip bug observed on mixed-layout pages — documented at [.claude/issues-with-docling/reading-order-mixed-layout-page.md](issues-with-docling/reading-order-mixed-layout-page.md), Phase 1 ships as-is. |
| 2026-05-21 | 1 | **Persistent data nodes** landed: `docling/engines/artifacts.py` (`document.json` + `nodes.jsonl` + figure/table crops). `PdfEngine(save_artifacts=True)` is the default. |
| 2026-05-21 | 1 | **Clickable preview** landed: viewer now draws one bbox per `DocItem`, click opens side panel with full node JSON. Esc clears selection. |
| 2026-05-21 | 1 | **Run snapshot** landed: `docling/engines/run_snapshot.py` writes `run.json` per PDF (env, timing, models, full pipeline_options). `tach.toml` gained a `docling.engines` module entry. 9/9 tests green; `make validate` clean. |

## Blockers

_None._

## Open questions

- Cache backend for VLM (Phase 3): in-memory only, or disk-backed? Decide before Phase 3 starts.
- For Phase 4 (LLM metadata) — confirm Anthropic API key is the only LLM credential needed, or also OpenAI / local model fallback?
