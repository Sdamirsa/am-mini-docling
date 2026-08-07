# Amir Engine — Current Stage

Live tracker for the build defined in [AMIR_TODO.md](AMIR_TODO.md). Keep entries short; update when starting or finishing a task.

## Current phase

**PHASE 1 + 2 + 3 — Foundation + Chunking + VLM** — **COMPLETE.** 13 tests green; smoke-tested on `samples/test-pdf-ai-manuscript.pdf` (8 pages, 0 errors, 7 figures, 5 tables, 50 chunks, journal-logo correctly flagged as noise and stripped from both markdown files).

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
| Linked + standalone markdown | ✅ done | `link_images=True` (default): primary `<stem>.md` rewrites placeholders to `![](images/picture_NNN.png)` so markdown viewers render figures. `embed_images=True` (default): additionally writes `<stem>.embedded.md` with base64 data URIs for single-file sharing. |
| Per-PDF output folder | ✅ done | All artifacts land under `<output_dir>/<pdf-stem>/` (sanitised). |
| Persistent data nodes | ✅ done | `docling/engines/artifacts.py` — writes `document.json` (full `DoclingDocument`), `nodes.jsonl` (one line per node with bbox/text/captions/table data + `image_path` for pictures/tables), and `images/picture_NNN.png` / `table_NNN.png` via `PictureItem.get_image()` / `TableItem.get_image()`. |
| Run snapshot | ✅ done | `docling/engines/run_snapshot.py` — `<pdf-dir>/run.json` with schema_version, source, status, timing (started_at / finished_at / duration_seconds), engine_config, full pipeline_options (`serialize_as_any=True` so subclass fields like `layout_options.model_spec` survive), per-stage models summary, environment (python, platform, machine, system, tracked package versions), output_summary, errors. Hostname intentionally **not** captured. |

### Path deviations from the TODO

Two paths were quietly corrected during implementation:

- `docling/models/engine_output.py` → **`docling/engines/schemas.py`**
- `docling/utils/validation.py` → **`docling/engines/validation.py`**

Reason: `docling/models/` holds upstream's ML-model wrappers (layout, OCR, VLM); putting Pydantic data schemas there is a naming collision waiting to happen. Same logic for `docling/utils/`. Keeping all Amir Engine code under `docling/engines/` makes future upstream merges easier.

## Per-PDF output layout (Phase 1+2+3 deliverable)

```
out/<pdf-stem>/
├── <pdf-stem>.md            # primary markdown (noise stripped; ![](images/picture_NNN.png) refs)
├── <pdf-stem>.embedded.md   # standalone — base64-inlined images (when embed_images=True, default)
├── document.json            # full DoclingDocument (round-trippable)
├── nodes.jsonl              # one JSON object per node from iterate_items()
├── chunks.jsonl             # HybridChunker output: index, text, token_count, headings, page_nos, self_refs
├── tables.jsonl             # one TableItem per row: caption_text, markdown, html, flat cells (with spans), dims
├── figures.jsonl            # one PictureItem per row: caption_text, image_path, vlm_caption, classifier_label, is_noise/noise_reason
├── run.json                 # env + timing + engine_config + pipeline_options (incl. model_spec) + packages
├── images/
│   ├── page_NNNN.png        # page renders
│   ├── picture_NNN.png      # PictureItem.get_image() crops (ALL pictures kept; noise just tagged)
│   └── table_NNN.png        # TableItem.get_image() crops
└── preview.html             # bbox viewer — summary chips + clickable formatted side panel
```

For the optional full-page-VLM A/B run (``compare_pipelines.run_comparison``):

```
out/<pdf-stem>/
├── standard/                # full PdfEngine bundle as above
├── full_page_vlm/           # same shape, produced via VlmPipeline (default GraniteDocling)
└── comparison.md            # side-by-side stats + first lines of each markdown
```

`PdfEngine(save_artifacts=True)` (default) auto-enables `generate_page_images` + `generate_picture_images`; `filter_noise_pictures=True` (default) auto-enables `do_picture_classification` so journal logos / repeated banners are tagged.

## Next action

Phases 1–3 are done. Pipelines produce a clean, agent-readable bundle per PDF (text via chunks, structured tables, structured figures with optional VLM captions). Phase 4 (LLM context enrichment) was **dropped** by design; downstream consumers can run their own LLM over `chunks.jsonl` + `figures.jsonl` + `tables.jsonl` if they want summaries/topics/metadata.

Open items for future work (not active):
- Pull GraniteDocling table-structure and Qwen2.5-VL-3B picture description through a real GPU run end-to-end and pin numbers in `run.json`.
- Phase 5 (FastAPI + CLI exposing `PdfEngine.convert` and `run_comparison`) when batch-processing demand appears.
- Tokenizer/model swap to Qwen3-Embedding-4B + Qwen3-VL (see "Future considerations" in AMIR_TODO).

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
| 2026-05-21 | 1 | **Linked + standalone markdown** landed: primary `.md` rewrites `<!-- image -->` placeholders to `![](images/picture_NNN.png)` refs (matches `nodes.jsonl.image_path`); `embed_images=True` (now default) additionally writes `<stem>.embedded.md` with base64 images. Manuscript smoke: primary 55 KB / 0 placeholders, embedded 697 KB / 7 base64 figures. |
| 2026-05-21 | 2 | **HybridChunker integration** landed: `docling/engines/chunker.py` writes `chunks.jsonl` (50 chunks on manuscript). Tokenizer = `sentence-transformers/all-MiniLM-L6-v2`, max_tokens=512. Auto-on with `save_artifacts=True`. |
| 2026-05-21 | 2 | **Structured outputs** landed: `tables.jsonl` (caption_text + markdown + html + flat cells with row/col offsets/spans) and `figures.jsonl` (caption_text + image_path + vlm_caption + classifier_label) via `docling/engines/structured_outputs.py`. |
| 2026-05-21 | 3 | **Granite-Vision tables** flag landed (opt-in; downloads a 2B model on first use). |
| 2026-05-21 | 3 | **Picture description VLM** wired: `PdfEngine(picture_description="qwen25_vl_3b", picture_description_engine="vllm")` builds `PictureDescriptionVlmEngineOptions` + `VllmVlmEngineOptions` pointing at `Qwen/Qwen2.5-VL-3B-Instruct`. Captions land in `figures.jsonl[*].vlm_caption`. Custom Qwen spec lives in `docling/engines/vlm_specs.py` (Docling's bundled Qwen preset is MLX-only). |
| 2026-05-21 | 3 | **Picture noise filter** landed (default-on): `docling/engines/picture_filter.py` classifies logos / watermarks / repeated banners via classifier labels + bbox-repeat heuristic. Auto-enables `do_picture_classification`. On the manuscript, correctly tagged the *European Journal of Radiology* running logo as `classifier:logo` (1 of 7 pictures). Noise pictures are stripped from both `<stem>.md` and `<stem>.embedded.md` (replaced with `<!-- noise picture: reason -->`). |
| 2026-05-21 | 3 | **Full-page VLM comparison runner** landed: `docling/engines/compare_pipelines.py::run_comparison()` writes `out/<stem>/{standard,full_page_vlm,comparison.md}`. Default uses `GRANITEDOCLING_TRANSFORMERS` (DocTags → comparable bundles). |
| 2026-05-21 | 3 | **HTML preview extended**: summary chips (pages / figures / tables / chunks / noise), per-kind formatted side panel (picture: caption + VLM description + classifier + thumbnail; table: dims + rendered HTML; text: body text), noise pictures rendered dashed gray with badge. Raw JSON still available via collapsible toggle. |
| 2026-08-07 | — | `RUN.md` (repo root) + `docs/hand-off-notes/hand-off-note-for-citation.md` landed: batch-run guide (`amir-batch` has no skip-already-done logic — documented the manual workaround) and a spec for using the per-PDF bundle as extraction-citation evidence. |
| 2026-08-07 | 1 | **Citation deep-link** landed in `docling/engines/visualizer.py`: `preview.html?ref=self_ref[,self_ref...]` scrolls to and persistently highlights the matching bbox(es) and opens the side panel; the side panel now also shows a ready-made citation link for whatever node is selected. Page-only anchors (`#page-N`) already worked. |
| 2026-08-07 | 3 | **Fixed: Granite-Vision-4.1-4b defaults were broken since the "Granite-Vision defaults" commit** — every PDF failed with `EXCEPTION` at pipeline-init under default flags (`--granite-vision-tables` on, `--picture-description granite_vision_4b`, both on by default). Root cause: `ibm-granite/granite-vision-4.1-4b`'s connector is a Blip2-style Q-Former, which doesn't support `sdpa` attention (huggingface/transformers#28005); the picture-description path also loaded the model via plain `AutoModel` (no `.generate()`) instead of `AutoModelForImageTextToText`. Fixed in `docling/models/inference_engines/vlm/transformers_engine.py` (additive `attn_implementation` extra_config override, doesn't affect other models), `docling/engines/vlm_specs.py` (sets `eager` attention + `AUTOMODEL_IMAGETEXTTOTEXT` for this spec), and `docling/models/stages/table_structure/table_structure_model_granite_vision.py` (single-model file, `sdpa`→`eager` fallback directly). Verified end-to-end with default flags on real PDFs: picture description produces populated `vlm_caption`s, table structure produces 5 well-formed tables on `test-pdf-ai-manuscript.pdf`. `AMIR_TODO.md`'s "pull Granite-Vision through a real GPU run end-to-end" open item is now done. |

## Blockers

_None._

## Open questions

- Cache backend for VLM (Phase 3): in-memory only, or disk-backed? Decide before Phase 3 starts.
- For Phase 4 (LLM metadata) — confirm Anthropic API key is the only LLM credential needed, or also OpenAI / local model fallback?
- GPU-enabled Docker on this box (aarch64 + NVIDIA GB10) is being explored on a separate branch (not `dgx`) — see that branch for outcome/status note. The root `Dockerfile` here stays CPU-only/upstream-only by design.
