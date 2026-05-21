---
name: anthropic-sdk-bootstrap
description: |
  Scaffolds a Claude API / Anthropic SDK client in the current Python or Node project: adds the SDK dependency, creates a thin client wrapper with prompt caching enabled, .env-based key loading, sensible retry+timeout defaults, and a working hello-world example. Defaults to the latest stable Claude model unless the user specifies one. Use when the user says "set up anthropic client", "scaffold an agent", "init claude api", "bootstrap the SDK", "create a starter for the Anthropic SDK", "add Claude API to this project", or starts a new LLM-app project from scratch. NOT for editing existing LLM code — touch the SDK call site directly. NOT for non-Anthropic LLM SDKs (OpenAI, Vertex); this skill is Claude-specific.
---

# anthropic-sdk-bootstrap

Scaffold a Claude API client with caching, retries, env handling.

## Workflow

1. Detect project language: Python (`pyproject.toml`) or Node (`package.json`).
2. Install the SDK:
   - Python: `uv add anthropic` (or pip if no uv).
   - Node: `npm install @anthropic-ai/sdk`.
3. Read `reference/apis/anthropic-sdk.md` for current model IDs and patterns.
4. Create a thin wrapper at `src/llm/client.py` (Python) or `src/llm/client.ts` (Node):

   ```python
   # src/llm/client.py
   import os
   from anthropic import Anthropic

   _client: Anthropic | None = None

   def get_client() -> Anthropic:
       global _client
       if _client is None:
           api_key = os.environ.get("ANTHROPIC_API_KEY")
           if not api_key:
               raise RuntimeError("ANTHROPIC_API_KEY not set; see .env.example")
           _client = Anthropic(api_key=api_key, max_retries=3, timeout=60.0)
       return _client

   DEFAULT_MODEL = "claude-sonnet-4-6"  # update via /migrate-model-version
   ```

5. Add `.env.example` documenting `ANTHROPIC_API_KEY=`.
6. Verify `.env` is in `.gitignore` (the baseline manages this).
7. Add a hello-world example with prompt caching:

   ```python
   # examples/hello.py
   from src.llm.client import get_client, DEFAULT_MODEL

   client = get_client()
   resp = client.messages.create(
       model=DEFAULT_MODEL,
       max_tokens=1024,
       system=[{
           "type": "text",
           "text": "<long static instruction>",
           "cache_control": {"type": "ephemeral"},
       }],
       messages=[{"role": "user", "content": "hello"}],
   )
   print(resp.content[0].text)
   print(f"cache hits: {resp.usage.cache_read_input_tokens}")
   ```

8. Print next steps: how to set the env var, how to run the example, where to find more in `reference/apis/anthropic-sdk.md`.

## Constraints

- Always enables prompt caching by default — it's nearly free and a huge win on repeated system prompts.
- Never hard-codes API keys.
- Honors the project's existing layout (don't create `src/` if the project uses a different convention; surface and ask).
- Pins the SDK to a known-compatible version.
