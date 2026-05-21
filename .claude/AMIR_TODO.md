# Amir Engine - Condensed TODO

## PHASE 1: Foundation (PDF→Structured Conversion)
- [ ] Create `docling/engines/pdf_engine.py` - wrapper around DocumentConverter
- [ ] Create `docling/models/engine_output.py` - output schemas
- [ ] Create `docling/utils/validation.py` - input validation
- [ ] Create `tests/test_engines/test_pdf_engine.py` - unit tests
- [ ] Handle PDFs from local paths and URLs
- [ ] Error handling and logging
- [ ] created html output of the bounding boxes of the grabbed stuff to show what has been done to non-technical person

## PHASE 2: Content Extraction (Text/Image/Table)
- [ ] Create `docling/engines/content_extractor.py` - main extractor
- [ ] Create `docling/engines/table_extractor.py` - table handling
- [ ] Create `docling/models/content_models.py` - schemas
- [ ] Create `docling/utils/content_utils.py` - parsing helpers
- [ ] Extract text with hierarchy (sections, paragraphs)
- [ ] Extract images with metadata (caption, page, bbox)
- [ ] Extract tables with cell-level structure
- [ ] Create `tests/test_engines/test_content_extractor.py`

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

**Current Status**: PHASE 1 - NOT STARTED
