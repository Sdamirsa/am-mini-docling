<!-- last-reviewed: 2026-05-18 -->

# Prompt: `<name>`

> Copy this file to `<name>.md` and fill in.

## Purpose
What this prompt accomplishes; when to use.

## System prompt

```
<the actual prompt; pin to a concrete role + scope>
```

## Few-shot examples (optional)

```
User: <example input>
Assistant: <example output>
```

## Variables (placeholders)
- `{{document}}` — the input doc to extract from.
- `{{schema}}` — the JSON Schema (formatted as a code block).

## Calibration notes
- Best with `temperature=0`.
- Recommended model: claude-sonnet-4-6 (latency/quality tradeoff).
- Known weak cases: <e.g., "documents <500 chars often miss DOIs">.

## Change log
- v1.0.0 (YYYY-MM-DD): initial.
