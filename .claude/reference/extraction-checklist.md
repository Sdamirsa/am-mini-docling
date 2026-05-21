<!-- last-reviewed: 2026-05-18 -->

# Extractor design checklist

Run through before shipping a new extractor or accepting an extraction PR.

## Schema
- [ ] Pydantic/zod schema committed under `extractors/<name>/schema.py`.
- [ ] Mirror doc under `.claude/reference/schemas/<name>.md` with `last-reviewed`.
- [ ] Required vs optional fields chosen deliberately (don't over-require).
- [ ] Enums used for known small value spaces.
- [ ] Schema version recorded.

## Prompt
- [ ] System prompt under `extractors/<name>/prompt.md` (or `.claude/reference/prompts/`).
- [ ] Role + scope are precise (not "you are a helpful assistant").
- [ ] Output format constraint matches the schema exactly.
- [ ] Prompt cached if used across many docs.

## Call
- [ ] Tool-use mode with `tool_choice` forcing the extraction tool.
- [ ] `temperature=0`.
- [ ] Model version pinned (specific ID, not alias).
- [ ] Retries + timeout configured (max_retries=3, timeout=60s).

## Validation
- [ ] Output validated against the pydantic model.
- [ ] Validation failures log raw model output + error to `failures/<id>.json`.
- [ ] Optional retry-on-fail with the error appended to the user message.

## Eval
- [ ] `evals/<name>/cases.jsonl` exists with ≥5 cases per field.
- [ ] `evals/<name>/score.py` defines field-level scoring.
- [ ] `evals/<name>/run.py` runs the suite end-to-end.
- [ ] Baseline accuracy recorded under `.claude/reference/experiments/<YYYY-MM>-baseline.md`.

## Cost / scale
- [ ] For ≥50 docs, use the batch API.
- [ ] Sample 10 docs first; only scale after eval passes.
- [ ] Checkpointing in place for resumable runs.

## Privacy
- [ ] PII handling in failure logs decided (redact / encrypt / drop).
- [ ] No raw doc content logged in production unless explicitly opted in.
