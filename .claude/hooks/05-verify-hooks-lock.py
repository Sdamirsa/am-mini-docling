#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""SessionStart hook (runs FIRST due to 05- prefix): verify hooks.lock.

If the on-disk hook content disagrees with .claude/.meta/hooks.lock, emit
a warning into the SessionStart additionalContext alerting Claude (and
the user) that hook integrity has changed. Does NOT block — that would
freeze the session. Instead, the SessionStart context tells Claude to
refuse running other hooks until the user invokes `approve-hooks`.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


HOOKS_REL = Path(".claude/hooks")
LOCK_REL = Path(".claude/.meta/hooks.lock")


def _project() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _check(project: Path) -> dict | None:
    lock_path = project / LOCK_REL
    if not lock_path.exists():
        return {"reason": "hooks.lock is missing"}
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"reason": "hooks.lock is not valid JSON"}

    expected: dict[str, str] = lock.get("files", {})
    hooks_dir = project / HOOKS_REL
    if not hooks_dir.is_dir():
        return None
    current = {
        p.name: _sha256(p)
        for p in sorted(hooks_dir.iterdir())
        if p.is_file() and p.suffix == ".py"
    }

    mismatches = [n for n in expected if n in current and current[n] != expected[n]]
    missing = [n for n in expected if n not in current]
    extra = [n for n in current if n not in expected]
    if mismatches or missing or extra:
        return {
            "reason": "hooks.lock drift detected",
            "mismatches": mismatches,
            "missing": missing,
            "extra": extra,
        }
    return None


def main() -> int:
    project = _project()
    result = _check(project)
    if result is None:
        sys.exit(0)

    warning = (
        "# ⚠ Hook integrity warning\n\n"
        f"{result['reason']}.\n"
    )
    if result.get("mismatches"):
        warning += f"  Mismatched: {', '.join(result['mismatches'])}\n"
    if result.get("missing"):
        warning += f"  Missing (in lock, absent on disk): {', '.join(result['missing'])}\n"
    if result.get("extra"):
        warning += f"  Extra (on disk, absent in lock): {', '.join(result['extra'])}\n"
    warning += (
        "\nThe `+security-hardening` pack asks Claude: REFUSE to invoke any\n"
        "PreToolUse / PostToolUse logic until the user runs `approve-hooks`\n"
        "(or `claude-folder-handler approve-hooks`) to acknowledge these edits.\n"
    )

    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": warning,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"05-verify-hooks-lock error (non-fatal): {e}\n")
        sys.exit(0)
