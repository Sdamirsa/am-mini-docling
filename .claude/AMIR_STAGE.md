# Amir Engine — Current Stage

Live tracker for the build defined in [AMIR_TODO.md](AMIR_TODO.md). Keep entries short; update when starting or finishing a task.

## Current phase

**PHASE 1 — Foundation (PDF→Structured Conversion)** — **COMPLETE.** All 7 tests green; smoke-tested on `samples/test-pdf-ai-manuscript.pdf` (8 pages, 0 errors).

### Phase 1 status

| TODO item | State | Notes |
|---|---|---|
| `docling/engines/pdf_engine.py` wrapper | ✅ done | Thin facade over `DocumentConverter`. |
| Output schemas | ✅ done | Landed at `docling/engines/schemas.py` (not `docling/models/engine_output.py` — `docling/models/` is reserved for upstream ML model wrappers). |
| Input validation | ✅ done | Landed at `docling/engines/validation.py` (not `docling/utils/`) so all Amir code lives in one subtree. |
| `tests/test_engines/test_pdf_engine.py` | ✅ done | Real fixture: `tests/data/pdf/2305.03393v1-pg9.pdf`. |
| Local paths + URLs | ✅ done | `classify_source()` + `validate_pdf_source()`. |
| Error handling + logging | ✅ done | Catches `ConversionError`; `_log = logging.getLogger(__name__)`. |
| HTML bbox visualiser | ✅ done | `docling/engines/visualizer.py` — page PNG + abs-positioned overlays, hover surfaces JSON metadata, label-coloured legend. Wired via `PdfEngine(with_page_images=True).convert(..., make_html_preview=True)`. |

### Path deviations from the TODO

Two paths were quietly corrected during implementation:

- `docling/models/engine_output.py` → **`docling/engines/schemas.py`**
- `docling/utils/validation.py` → **`docling/engines/validation.py`**

Reason: `docling/models/` holds upstream's ML-model wrappers (layout, OCR, VLM); putting Pydantic data schemas there is a naming collision waiting to happen. Same logic for `docling/utils/`. Keeping all Amir Engine code under `docling/engines/` makes future upstream merges easier.

## Next action

Move to **PHASE 2 — Content Extraction (Text / Image / Table)** per [AMIR_TODO.md](AMIR_TODO.md). Start with `docling/engines/content_extractor.py` that consumes a `PdfConversionOutput` and yields hierarchical text + image + table records.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-05-21 | — | `.claude/` workspace initialised. |
| 2026-05-21 | 1 | `.claude/` re-scaffolded via `claude-folder-handler` (packs: data-science, llm-app, llm-extraction, security-hardening, visualization). Amir files restored on top. |
| 2026-05-21 | 1 | Foundation code landed: `docling/engines/{__init__,schemas,validation,pdf_engine}.py` + `tests/test_engines/test_pdf_engine.py`. |
| 2026-05-21 | 1 | HTML bbox visualiser landed: `docling/engines/visualizer.py`, wired into `PdfEngine` via `make_html_preview=True`. 7/7 tests pass. Smoke-tested on `samples/test-pdf-ai-manuscript.pdf` → preview at `samples/out/preview.html`. |
| 2026-05-21 | 1 | Dev env: `--all-extras` unusable on aarch64 (no `onnxruntime-gpu` wheel). Working install: `uv sync --frozen --group dev --no-group docs --no-group examples --extra standard`. See [REPO_CONTEXT.md](REPO_CONTEXT.md) for full notes. |

## Blockers

_None._

## Open questions

- Cache backend for VLM (Phase 3): in-memory only, or disk-backed? Decide before Phase 3 starts.
- For Phase 4 (LLM metadata) — confirm Anthropic API key is the only LLM credential needed, or also OpenAI / local model fallback?
