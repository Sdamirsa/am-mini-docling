#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PostToolUse hook (Edit|Write matcher): warn when a deprecated/retired
Claude model ID is written into a file.

Non-blocking: this hook only prints a warning to stderr (exit 0). The
purpose is to surface stale model IDs early, not to block edits.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from payload import read_payload  # noqa: E402


# Update this list when models retire. The +llm-app pack's
# migrate-model-version skill helps refresh the project's usage.
DEPRECATED_MODELS: dict[str, str] = {
    "claude-3-opus-20240229": "claude-opus-4-7",
    "claude-3-sonnet-20240229": "claude-sonnet-4-6",
    "claude-3-haiku-20240307": "claude-haiku-4-5-20251001",
    "claude-3-5-sonnet-20240620": "claude-sonnet-4-6",
    "claude-3-5-sonnet-20241022": "claude-sonnet-4-6",
    "claude-3-5-haiku-20241022": "claude-haiku-4-5-20251001",
    "claude-3-7-sonnet-20250219": "claude-sonnet-4-6",
    "claude-sonnet-4-20250514": "claude-sonnet-4-6",
    "claude-opus-4-20250514": "claude-opus-4-7",
    "claude-opus-4-1-20250805": "claude-opus-4-7",
}


def main() -> int:
    payload = read_payload()
    tool = payload.get("tool_name")
    if tool not in {"Edit", "Write"}:
        return 0

    tinput = payload.get("tool_input") or {}
    # Inspect any string field for a deprecated model ID; surface a warning.
    content_fields = ["content", "new_string", "file_text"]
    blob = " ".join(str(tinput.get(k, "")) for k in content_fields)
    if not blob:
        return 0

    hits: list[tuple[str, str]] = []
    for old, new in DEPRECATED_MODELS.items():
        if old in blob:
            hits.append((old, new))

    if hits:
        sys.stderr.write("claude-folder-handler/+llm-app: stale model ID(s) in this edit:\n")
        for old, new in hits:
            sys.stderr.write(f"  - {old}  →  consider {new}\n")
        sys.stderr.write(
            "  Run the `migrate-model-version` skill to update across the project.\n"
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"15-warn-stale-model hook error (non-fatal): {e}\n")
        sys.exit(0)
