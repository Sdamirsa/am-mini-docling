#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Stop hook: append a structured invocation record to a local JSONL log.

Local-only telemetry. Never network. Consumed by /audit to flag dead skills.

Log path: ${CLAUDE_PROJECT_DIR}/.claude/.cache/invocations.jsonl
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from payload import read_payload  # noqa: E402


def _project() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _log_path(project: Path) -> Path:
    return project / ".claude" / ".cache" / "invocations.jsonl"


def main() -> int:
    payload = read_payload()
    project = _project()

    record: dict[str, object] = {
        "ts": time.time(),
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": payload.get("hook_event_name", "Stop"),
        "session_id": payload.get("session_id"),
        "cwd": str(project),
    }
    # Best-effort: anything that looks like skill/agent metadata.
    for k in ("skill_invoked", "agent_invoked", "tool_name", "stop_reason"):
        if k in payload:
            record[k] = payload[k]

    log = _log_path(project)
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    except OSError:
        # Local-only — silently skip if we can't write.
        pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"90-stop-log-invocation hook error (non-fatal): {e}\n")
        sys.exit(0)
