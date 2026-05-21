#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""SessionStart hook: inject ROUTER + git context + drift warnings.

The injected text lands in Claude's context as `additionalContext` and
persists across `/compact`. Keep total payload under ~2 KB to be polite.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from payload import emit_session_start_context, read_payload  # noqa: E402


def _project_dir() -> Path:
    p = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(p) if p else Path.cwd()


def _read_router(project: Path) -> str:
    router = project / ".claude" / "ROUTER.md"
    if not router.exists():
        return ""
    try:
        return router.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _git(project: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if out.returncode != 0:
            return ""
        return out.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _git_context(project: Path) -> str:
    if not (project / ".git").exists():
        return ""
    branch = _git(project, "rev-parse", "--abbrev-ref", "HEAD")
    short = _git(project, "log", "-5", "--oneline", "--no-decorate")
    dirty = _git(project, "status", "--porcelain")
    lines = []
    if branch:
        lines.append(f"Branch: `{branch}`")
    if dirty:
        n = sum(1 for ln in dirty.splitlines() if ln.strip())
        lines.append(f"Working tree: {n} uncommitted change(s)")
    if short:
        lines.append("Recent commits:\n" + "\n".join(f"  {ln}" for ln in short.splitlines()))
    return "\n".join(lines)


def _sanitize(text: str, max_chars: int = 4000) -> str:
    """Strip control chars and cap length to defang prompt-injection vectors."""
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or 0x20 <= ord(ch) < 0x7F or ord(ch) > 0x9F)
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[truncated]"
    return cleaned


def main() -> int:
    _ = read_payload()  # informational; we don't gate on it
    project = _project_dir()

    parts: list[str] = []

    router = _read_router(project)
    if router:
        parts.append("# Claude Code Router (consult before acting)\n\n" + router)

    git = _git_context(project)
    if git:
        parts.append("# Repo state\n\n" + git)

    parts.append(
        "# Reminder\n\n"
        "Run `claude-folder-handler audit` (or ask Claude to \"audit my .claude folder\") "
        "if any `.claude/` files were recently edited."
    )

    text = _sanitize("\n\n---\n\n".join(parts))
    if text:
        emit_session_start_context(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never crash the session
        sys.stderr.write(f"session-start hook error (non-fatal): {e}\n")
        sys.exit(0)
