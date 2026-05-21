---
paths:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
applies_when: "file imports 'anthropic' or '@anthropic-ai/sdk'"
---

# Anthropic SDK conventions

## Always
- Load API key from `os.environ["ANTHROPIC_API_KEY"]` (Python) or
  `process.env.ANTHROPIC_API_KEY` (Node). Never hard-code.
- Enable prompt caching for any static system prompt or repeated tool
  schema: wrap content in `cache_control: {"type": "ephemeral"}`.
- Configure retries (`max_retries=3`) and timeout (`60s` default).
- Use streaming for user-facing UIs (>5s expected latency).

## Model IDs
- Pin to a specific model version (`claude-sonnet-4-6`) — don't use a
  floating alias.
- Centralize the default in one constant (`DEFAULT_MODEL`) so the
  migrate-model-version skill can find every call site.
- Consult `.claude/reference/apis/anthropic-sdk.md` for the current
  recommended models per use case.

## Patterns
- Tool use: serialize tool schemas to JSON Schema; validate model output via
  pydantic / zod before acting.
- Long-running tools: use the batch API (`/v1/messages/batches`) when you
  have >50 independent requests.
- Conversation state: track the full message list; don't try to "summarize
  and continue" without an explicit memory mechanism.

## Errors
- `RateLimitError` → exponential backoff (the SDK does this for you with
  `max_retries`; just configure it).
- `APIStatusError` 400 — log the request_id and the failing message.
- Never log full message contents on error in production — strip user PII.

## Antipatterns
- Building your own retry loop on top of the SDK's (double-retry storms).
- Disabling prompt caching to "save tokens" — caching is a discount, not a cost.
- Mixing message lists between turns without preserving order/roles.
- Using a deprecated model alias.
