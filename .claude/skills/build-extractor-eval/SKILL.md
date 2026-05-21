---
name: build-extractor-eval
description: |
  Scaffolds an evaluation harness for an existing extractor: a small labeled dataset of inputs + expected outputs (in `evals/<extractor>/cases.jsonl`), a scoring function that compares the extractor's output against expected (exact match, set-overlap for lists, fuzzy match for strings), and a CLI runner that produces a per-field accuracy report. Uses the same schema as the extractor. Use when the user says "evaluate the extractor", "score this extraction", "build an eval for extraction", "how good is my extractor", "measure extractor accuracy", "create test cases for the extractor", or asks how to know if extraction quality is regressing. NOT for general unit testing — use the test-writer agent. NOT for running the eval against new model versions (that's iteration; this skill just builds the harness once).
---

# build-extractor-eval

Stand up a reproducible eval harness for an extractor.

## Workflow

1. Identify the target extractor (its dir under `extractors/`).
2. Read its schema (pydantic model + JSON Schema) and its example failures
   under `failures/` if any exist.
3. Build the test-case file `evals/<name>/cases.jsonl`:
   - Seed 5-10 hand-curated cases covering each field (happy path, edge,
     ambiguous, missing field, multiple values).
   - Each line: `{"id": ..., "input": ..., "expected": <schema-valid object>}`.
   - If existing labeled data is available, ingest it.
4. Build the scoring function `evals/<name>/score.py`:
   - Per-field:
     - Required string: exact match (lower, strip).
     - Optional string: exact match or both-null = pass.
     - List: Jaccard overlap; threshold configurable.
     - Enum: exact match.
     - Number: tolerance configurable.
   - Return per-field accuracy + total record-level accuracy.
5. Build the CLI runner `evals/<name>/run.py`:
   - Loads cases, runs the extractor, scores each, writes per-case results
     under `evals/<name>/runs/<timestamp>.jsonl`, prints a summary.
6. Add a README at `evals/<name>/README.md` explaining the cases + scoring.
7. Suggest: rerun the eval after every change to the extractor's prompt,
   schema, or model version.

## Constraints

- Eval cases live with the code (committed). Failure transcripts live under
  `.gitignore`'d output.
- Don't auto-generate cases from the extractor's own output (circular).
- Be explicit about which match types are exact vs fuzzy.
- Surface ambiguous expected outputs (where >1 answer is reasonable) as
  comments in `cases.jsonl`.
