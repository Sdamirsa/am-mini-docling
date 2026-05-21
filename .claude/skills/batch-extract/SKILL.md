---
name: batch-extract
description: |
  Runs an existing extractor across a large set of documents using either the Anthropic batch API (preferred for ≥50 docs; ~50% cheaper, 24h SLA) or async fan-out for smaller sets. Includes checkpointing so interrupted runs resume; logs per-document success/failure; aggregates results into a single output file (jsonl by default). Use when the user says "run this on all my files", "batch extract", "extract everything in this folder", "process all the PDFs", "run the extractor on the corpus", "extract from N documents at once", or names a directory of inputs. NOT for one-off interactive extraction — use extract-structured. NOT for streaming/realtime extraction; this skill is for offline batch processing.
---

# batch-extract

Run an extractor across a corpus with checkpointing.

## Workflow

1. Identify the extractor (`extractors/<name>/`) and the input corpus
   (directory or file list).
2. Count the input set:
   - <10 docs: synchronous loop with retry per doc.
   - 10-50 docs: async fan-out (concurrency=5 by default).
   - >=50 docs: prefer Anthropic batch API.
3. Build the run directory `extractors/<name>/runs/<timestamp>/`:
   - `inputs.jsonl` — one line per doc with id + content (or path).
   - `checkpoint.json` — written after each successful batch slice; lists doc IDs already completed.
   - `results.jsonl` — appended per successful extraction.
   - `failures.jsonl` — appended per failure with raw model output + validation error.
4. On resume (re-invocation with the same run dir), read `checkpoint.json` and skip completed IDs.
5. Validate each result against the schema as it lands; failures don't abort the run.
6. At the end, print: total / success / fail counts, sample of failures, eval link.
7. If +pr-flow installed, suggest committing the run dir's small summary file (not the heavy inputs).

## Constraints

- Always checkpointed; never lose work on interrupt.
- Never re-runs a successfully extracted doc unless `--force` is passed.
- For batch API, polls every 5 minutes (configurable); doesn't busy-wait.
- Never logs raw document content if it might contain PII; offers a redact flag.
