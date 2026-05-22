# Amir Engine - Condensed TODO

## PHASE 1: Foundation (PDF→Structured Conversion) — COMPLETE

Landed paths differ from the original plan; see [AMIR_STAGE.md](AMIR_STAGE.md) for why.

- [X] `docling/engines/pdf_engine.py` — wrapper around `DocumentConverter`
- [X] `docling/engines/schemas.py` (was planned at `docling/models/engine_output.py`) — Pydantic output schemas
- [X] `docling/engines/validation.py` (was planned at `docling/utils/validation.py`) — input validation (local paths + URLs)
- [X] `tests/test_engines/test_pdf_engine.py` — 9 tests on real fixture
- [X] PDFs from local paths and `http(s)://` URLs
- [X] Error handling + structured logging (`PdfEngineError`, `_log`)
- [X] HTML bbox preview (`docling/engines/visualizer.py`) — **clickable**: one bbox per `DocItem`, click opens side panel with full node metadata (matches `nodes.jsonl`)
- [X] Per-PDF output subfolder (`<output_dir>/<pdf-stem>/`)
- [X] Linked primary markdown (`link_images=True`, default) — placeholders rewritten to `![](images/picture_NNN.png)` so viewers render figures
- [X] Standalone embedded companion (`embed_images=True`, default) — second `<stem>.embedded.md` with base64 images for single-file sharing
- [X] Persistent data nodes (`docling/engines/artifacts.py`) — writes `document.json` + `nodes.jsonl` + `images/picture_NNN.png` / `table_NNN.png` via `PictureItem.get_image()` / `TableItem.get_image()`
- [X] Per-PDF `run.json` (`docling/engines/run_snapshot.py`) — env, timing, engine_config, full `pipeline_options` (with model_spec), per-stage models summary, package versions

## PHASE 2: Chunking + Structured JSON outputs — COMPLETE

- [X] `docling/engines/chunker.py` — `write_chunks()` runs `HybridChunker`, writes `chunks.jsonl` (index, text, token_count, headings, captions, page_nos, self_refs). Tokenizer default: `sentence-transformers/all-MiniLM-L6-v2`, max_tokens=512.
- [X] `docling/engines/structured_outputs.py` — `write_structured_outputs()` writes `tables.jsonl` (caption_text + markdown + html + flat cells with offsets/spans + dims) and `figures.jsonl` (caption_text + image_path + vlm_caption + classifier_label + is_noise + noise_reason).
- [X] Wired into `PdfEngine.convert()` (auto-on when `save_artifacts=True`).
- [X] `PdfConversionOutput` extended: `chunks_jsonl`, `tables_jsonl`, `figures_jsonl`, `run_json`, etc.

## PHASE 3: VLM Integration — COMPLETE (opt-in heavy models, plus noise filter)

- [X] `docling/engines/vlm_specs.py` — `build_picture_description_options(preset, engine)` with Qwen2.5-VL-3B (vLLM) plus passthrough to Docling's bundled presets (`smolvlm`, `granite_vision`, `pixtral`).
- [X] `PdfEngine(picture_description="qwen25_vl_3b", picture_description_engine="vllm")` — wires `do_picture_description=True` + `PictureDescriptionVlmEngineOptions` + `VllmVlmEngineOptions`. Captions land in `figures.jsonl[*].vlm_caption`.
- [X] `PdfEngine(granite_vision_tables=True)` — swaps `table_structure_options` to `GraniteVisionTableStructureOptions()`.
- [X] `docling/engines/picture_filter.py` — `classify_pictures()` flags logos / watermarks / repeated banners using classifier labels + bbox-repeat heuristic. `PdfEngine(filter_noise_pictures=True)` is default-on; auto-enables `do_picture_classification`. Noise pictures get `is_noise=True` in `figures.jsonl` and their markdown refs are replaced with `<!-- noise picture: reason -->` in **both** the primary `.md` and the `.embedded.md`.
- [X] `docling/engines/compare_pipelines.py` — `run_comparison(pdf, output_dir, vlm_preset="granite_docling", ...)`:
  - Writes `out/<stem>/standard/` and `out/<stem>/full_page_vlm/` (each a full artifact bundle).
  - Writes `out/<stem>/comparison.md` with side-by-side status / duration / page / picture / table / chunk / markdown-size stats and the first lines of each markdown export.
  - Default uses `GRANITEDOCLING_TRANSFORMERS` (DocTags response → both folders comparable). Overriding to a markdown-only VLM logs a caveat banner.
- [X] HTML preview extended (`docling/engines/visualizer.py`): summary chips (pages / figures / tables / chunks / noise), per-kind formatted side panel (caption + VLM description + classifier + image thumbnail for pictures; caption + dims + rendered table HTML for tables; text for everything else), noise pictures rendered with dashed gray border and a "noise" badge. Raw JSON still available via a collapsible toggle.

## PHASE 4 (DROPPED): LLM Context Enrichment

~~Local-LLM summarisation / topic / metadata extraction.~~ Removed per design decision 2026-05-21: stay focused on clean structured JSON; LLM enrichment lives in a downstream consumer, not in this engine.

## Future considerations (not planned)

- Swap chunker tokenizer from `sentence-transformers/all-MiniLM-L6-v2` → `Qwen/Qwen3-Embedding-4B` when we want bigger chunks aligned to a modern embedding model (likely needs `max_tokens` bump to 1024–2048).
- Swap picture-description VLM from `Qwen/Qwen2.5-VL-3B-Instruct` → Qwen3-VL (e.g. `Qwen/Qwen3-VL-4B-Instruct` or 8B) once vLLM has stable support for it; Docling spec lives in `docling/engines/vlm_specs.py`, so it's a one-line change.

## PHASE 5: Output & API
- [ ] Create `docling/api/app.py` - FastAPI app
- [ ] Create `docling/api/routes.py` - API endpoints
- [ ] Create `docling/api/schemas.py` - Pydantic request/response
- [ ] Create `docling/models/output_schema.py` - unified output
- [ ] Create `docling/exporters/json_exporter.py`
- [ ] Create `docling/exporters/markdown_exporter.py`
- [ ] Create `docling/exporters/arrow_exporter.py`
- [ ] Create `config/api_config.yaml`
- [ ] REST API with async support
- [ ] Batch processing endpoints
- [ ] Webhooks for long-running jobs
- [ ] Create `tests/test_api/test_api_endpoints.py`

## PHASE 6: Polish & Deploy
- [ ] Create `docker/Dockerfile`
- [ ] Create `docker/docker-compose.yml`
- [ ] Create CLI interface in `cli/main.py` (`amir-engine` command)
- [ ] Create `scripts/build_engine.sh`
- [ ] Create `scripts/deploy.sh`
- [ ] Documentation: `docs/api_guide.md`, `deployment.md`, `troubleshooting.md`
- [ ] Create example notebooks in `docs/examples/`
- [ ] Integration tests in `tests/test_integration.py`
- [ ] Performance profiling
- [ ] Target coverage > 90%

## Quick Reference

**Key Dependencies**:
- Docling (existing) - PDF parsing
- GraniteDocling - VLM for tables/images
- Claude API - LLM for metadata
- FastAPI - REST API
- Pydantic v2 - Data validation

**Success Metrics**:
- Process 1000-page PDF in < 5 minutes
- Extract 99%+ of text with hierarchy
- VLM insights for 90%+ of images/tables
- Metadata extraction 85%+ accuracy
- API response < 100ms
- Zero external deps beyond models

**Current Status**: PHASE 1 + 2 + 3 — COMPLETE (2026-05-21). Output bundle per PDF: `<stem>.md`, `<stem>.embedded.md`, `document.json`, `nodes.jsonl`, `chunks.jsonl`, `tables.jsonl`, `figures.jsonl`, `run.json`, `images/`, `preview.html`. Plus `compare_pipelines.run_comparison()` for standard-vs-full-page-VLM A/B. Phase 4 (LLM enrichment) is DROPPED.
