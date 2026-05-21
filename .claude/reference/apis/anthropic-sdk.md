<!-- last-reviewed: 2026-05-18 -->

# Anthropic SDK quick reference

> Authoritative for *this* project. Consult before designing new SDK call
> sites or migrating model versions.

## Current model IDs (as of last-reviewed)

| Model | Use case | Approx. context |
|---|---|---|
| `claude-opus-4-7` | Complex reasoning, planning, hard problems | 1M (extended) |
| `claude-sonnet-4-6` | Default balanced (coding, agents, RAG) | 200k |
| `claude-haiku-4-5-20251001` | Fast, cheap, read-only / classification / tool routing | 200k |

`claude-opus-4-7[1m]` enables 1M-token context on Opus when explicit.

## Default for this project

Update this value with the migrate-model-version skill:
- **DEFAULT_MODEL = `claude-sonnet-4-6`**

## Prompt caching

```python
client.messages.create(
    model=DEFAULT_MODEL,
    max_tokens=1024,
    system=[{
        "type": "text",
        "text": LONG_STATIC_INSTRUCTION,
        "cache_control": {"type": "ephemeral"},
    }],
    messages=[...],
)
```

- Caches >=1024 tokens of content for ~5 minutes.
- Reads charged at ~10% of write price.
- Use for: long system prompts, large tool schemas, documents passed turn after turn.

## Streaming

```python
with client.messages.stream(model=DEFAULT_MODEL, max_tokens=1024, messages=msgs) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    final = stream.get_final_message()
```

## Tool use (function calling)

```python
client.messages.create(
    model=DEFAULT_MODEL,
    max_tokens=2048,
    tools=[{
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }],
    messages=[...],
)
```

Validate `response.content` for `tool_use` blocks before executing.

## Batch API

For >=50 independent requests, prefer the batch API: pay ~50% less, results
in 24h or less.

```python
batch = client.messages.batches.create(requests=[...])
# poll batch.id; retrieve when done.
```

## Common error patterns

| Error | Cause | Fix |
|---|---|---|
| `RateLimitError` | Tier limit | Exponential backoff via `max_retries` |
| `APIStatusError 400` | Malformed request | Log `request_id`; check message-list ordering |
| `APIStatusError 401` | Bad key | Verify `ANTHROPIC_API_KEY` |
| `APIStatusError 529` | Overloaded | Backoff; retry |

## Pitfalls

- A retry loop on top of the SDK's built-in retries creates retry storms.
- Disabling caching to "save tokens" — caching is a discount, not a cost.
- Mixing `messages` order between turns.
- Hard-coding model IDs across the codebase — centralize via `DEFAULT_MODEL`.
