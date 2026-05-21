---
name: extract-structured
description: |
  Designs and runs a structured-output extraction from unstructured text (PDFs, emails, transcripts, HTML, free-text fields) into a typed JSON object validated against a schema. Reuses an existing schema from `reference/schemas/` when one fits; otherwise drafts a new one (and offers to save it). Uses Claude tool-use for reliable structured output, validates with pydantic/zod, logs the raw input + failures for debugging. Use when the user says "extract X from these documents", "parse this into JSON", "pull structured data from", "extract entities from", "turn this text into a record", "build an extractor for", or hands over an unstructured source. NOT for general text summarization — use a plain `messages.create`. NOT for already-structured data (use a parser like jsonschema or csv). NOT for building the eval — use build-extractor-eval after this skill produces results.
---

# extract-structured

Reliable structured extraction with schema validation.

## Workflow

1. Read the input: file path(s), inline text, or a question about a dataset.
2. Check `.claude/reference/schemas/` for an existing schema that fits the
   extraction target. If present, use it. If not, draft a schema:
   - List the fields the user needs.
   - Mark optional vs required.
   - Choose dtypes (string, int, list, enum).
   - Anticipate 3 edge cases per field (missing, ambiguous, multi-valued).
3. Save the schema as a JSON Schema and a pydantic model under
   `extractors/<name>/schema.py` (and a copy in
   `.claude/reference/schemas/<name>.md` with `<!-- last-reviewed: ... -->`).
4. Write the extraction call:
   - System prompt: precise role, schema, output format.
   - Cache the system prompt (it's repeated across documents).
   - Tool-use: define one tool `record_extraction` whose `input_schema` IS the
     pydantic model's JSON Schema.
   - Force the model to call the tool (`tool_choice={"type":"tool","name":"record_extraction"}`).
5. Validate the tool input against the pydantic model. On failure:
   - Log the raw model output + the validation error.
   - Retry once with the error appended to the user message.
6. Return: list of validated records, count of failures, failure log path.

## Constraints

- Schema-first. Never ad-hoc parse `messages.create` text output for JSON.
- Always log raw model output on validation fail (under `extractors/<name>/failures/`).
- Don't suppress validation errors silently; surface them with the record index.
- For >50 docs, hand off to `batch-extract` (uses batch API + checkpointing).
