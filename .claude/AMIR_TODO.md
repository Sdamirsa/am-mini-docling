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
- [X] Standalone markdown via `PdfEngine(embed_images=True)` (base64 data URIs)
- [X] Persistent data nodes (`docling/engines/artifacts.py`) — writes `document.json` + `nodes.jsonl` + `images/picture_NNN.png` / `table_NNN.png` via `PictureItem.get_image()` / `TableItem.get_image()`
- [X] Per-PDF `run.json` (`docling/engines/run_snapshot.py`) — env, timing, engine_config, full `pipeline_options` (with model_spec), per-stage models summary, package versions

## PHASE 2: Content Extraction (Text/Image/Table)

Phase 1 already persists the raw node graph (`nodes.jsonl`) + figure/table crops. Phase 2 consumes that and emits structured, hierarchical content ready for VLM/LLM layers.

- [ ] `docling/engines/content_extractor.py` — main extractor (consumes `PdfConversionOutput` or a `nodes.jsonl` path)
- [ ] `docling/engines/table_extractor.py` — table normalisation (cell-level structure + caption + page)
- [ ] `docling/engines/schemas.py` — extend with `Section`, `Paragraph`, `ImageRecord`, `TableRecord` models (do **not** create a new `docling/models/content_models.py` — keep Amir schemas in one file)
- [ ] Extract text with hierarchy (sections, paragraphs) — workaround the [reading-order bug](issues-with-docling/reading-order-mixed-layout-page.md) here, e.g. column-bin re-sort
- [ ] Extract images with metadata (caption, page, bbox, `image_path` pointing at the Phase-1 crop)
- [ ] Extract tables with cell-level structure (from `TableItem.data` already in `nodes.jsonl`)
- [ ] `tests/test_engines/test_content_extractor.py`

## PHASE 3: VLM Integration (Table & Image Analysis)
- [ ] Create `docling/engines/vlm_analyzer.py` - VLM coordination
- [ ] Create `docling/engines/table_vlm_extractor.py` - table VLM logic
- [ ] Create `docling/engines/image_vlm_analyzer.py` - image VLM logic
- [ ] Create `docling/models/vlm_models.py` - VLM schemas
- [ ] Create `docling/utils/vlm_cache.py` - caching layer
- [ ] Integrate GraniteDocling for table/image understanding
- [ ] Parallel processing for tables/images
- [ ] Create `tests/test_engines/test_vlm_analyzer.py`

## PHASE 4: LLM Metadata Layer
- [ ] Create `docling/providers/abstract_llm.py` - LLM interface
- [ ] Create `docling/providers/claude_provider.py` - Claude integration
- [ ] Create `docling/engines/llm_extractor.py` - LLM coordination
- [ ] Create `docling/engines/metadata_extractor.py` - metadata logic
- [ ] Create `docling/models/llm_models.py` - LLM schemas
- [ ] Create `docling/models/metadata_models.py` - metadata schemas
- [ ] Extract: title, authors, language, date, type, keywords, summary
- [ ] Structured output validation
- [ ] Create `tests/test_engines/test_llm_extractor.py`

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

**Current Status**: PHASE 1 — COMPLETE (2026-05-21). Next: Phase 2, kicked off after the LLM/VLM config discussion.
