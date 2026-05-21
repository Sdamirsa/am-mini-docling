---
paths:
  - "extractors/**"
  - "pipelines/**"
applies_when: "always within these paths"
---

# Extraction conventions

## Schema-first
- Every extractor has a typed schema (pydantic / zod), committed under
  `extractors/<name>/schema.py`.
- The same schema is mirrored as a doc under
  `.claude/reference/schemas/<name>.md` with a `<!-- last-reviewed: ... -->`
  header.
- Never parse free-text model output for JSON — use tool-use with the schema
  as the tool's `input_schema`.

## Failure logging
- On validation failure, log the raw model output AND the validation error
  under `extractors/<name>/failures/<id>.json`.
- Don't suppress validation errors silently.
- For sensitive inputs, redact PII in the failure log (configurable flag).

## Version the schema
- When the schema changes, bump `schema_version` (semver) in the schema
  file's `meta` field.
- Run the eval (`evals/<name>/run.py`) after every schema change.

## Prompts as first-class artifacts
- System prompts live under `extractors/<name>/prompt.md` (one file = one
  prompt; readable, versionable).
- Cross-extractor reusable prompts live in `.claude/reference/prompts/`.
- Don't inline long prompts as Python f-strings.

## Determinism
- Set `temperature=0` for extraction.
- Pin the model version explicitly; don't use a floating alias.
- Cache the system prompt (it's static across documents).

## Cost
- For >=50 docs, use the batch API.
- For repeated runs with the same input, checkpoint and skip completed IDs.
- Sample-then-scale: validate quality on 10 docs before kicking off a 10k-doc run.
