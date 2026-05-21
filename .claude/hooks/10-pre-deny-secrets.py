#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PreToolUse hook: block reads/writes of credential files.

Closes the bash-regex bypasses cataloged in the security review by:
  - canonicalizing all file paths (resolves env vars, ~, relative segments)
  - parsing Bash commands via shlex with leading-assignment substitution
  - matching tokens against tightened deny-globs and patterns

Matchers: Read, Edit, Write, Bash.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from bash_parse import collect_argv_with_inherited_env  # noqa: E402
from paths import (  # noqa: E402
    CRED_FILE_RE,
    ENV_TOKEN_RE,
    PEM_KEY_RE,
    PROC_ENVIRON_RE,
    canonicalize,
    matches_any_glob,
)
from payload import allow, deny, read_payload  # noqa: E402


# Globs evaluated against canonicalized absolute paths.
DENY_PATH_GLOBS = [
    "*/.env",
    "*/.env.*",
    "*/credentials*",
    "*/.git-credentials",
    "*/id_rsa*",
    "*/id_ed25519*",
    "*/id_ecdsa*",
    "*/*.pem",
    "*/*.key",
    "*/*.p12",
    "*/*.pfx",
    "*/.npmrc",
    "*/.netrc",
    "*/.pypirc",
    "~/.ssh/*",
    "~/.ssh/**",
    "~/.aws/*",
    "~/.aws/**",
    "~/.gnupg/*",
    "~/.gnupg/**",
    "~/.kube/config",
    "~/.docker/config.json",
    "/proc/*/environ",
    "/proc/self/environ",
]


def _cwd() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _check_file_arg(file_path: str, cwd: Path) -> str | None:
    """Return a reason-string if the path matches a deny glob, else None."""
    canon = canonicalize(file_path, cwd=cwd)
    hit = matches_any_glob(canon, DENY_PATH_GLOBS)
    if hit:
        return f"path {canon} matches credential deny-glob {hit!r}"
    return None


def _check_bash_command(cmd: str, cwd: Path) -> str | None:
    """Return a reason-string if the command would read a credential file, else None."""
    text = cmd
    if PROC_ENVIRON_RE.search(text):
        return f"command references /proc/<pid>/environ (env-var exfil): {text[:120]}"
    if CRED_FILE_RE.search(text):
        return f"command references a credential file: {text[:120]}"
    if PEM_KEY_RE.search(text):
        return f"command references a private-key file: {text[:120]}"

    # Expand env-var assignments and inspect each clause's argv for paths.
    for clause, argv in collect_argv_with_inherited_env(text):
        for tok in argv:
            if not tok or tok.startswith("-"):
                continue
            if "/" not in tok and "." not in tok and "~" not in tok:
                continue
            # Likely a path arg.
            if ENV_TOKEN_RE.search(" " + tok):
                return f"command argument refers to a .env file: {tok}"
            hit = matches_any_glob(canonicalize(tok, cwd=cwd), DENY_PATH_GLOBS)
            if hit:
                return f"command argument {tok} resolves to a denied path (matches {hit!r})"
    return None


def main() -> int:
    payload = read_payload()
    tool = payload.get("tool_name") or payload.get("tool")
    tinput = payload.get("tool_input") or payload.get("input") or {}
    cwd = _cwd()

    if tool in {"Read", "Edit", "Write"}:
        file_path = tinput.get("file_path") or tinput.get("path") or tinput.get("filePath")
        if isinstance(file_path, str):
            reason = _check_file_arg(file_path, cwd)
            if reason:
                deny(f"blocked by claude-folder-handler/10-pre-deny-secrets: {reason}")
    elif tool == "Bash":
        cmd = tinput.get("command") or tinput.get("cmd") or ""
        if isinstance(cmd, str) and cmd.strip():
            reason = _check_bash_command(cmd, cwd)
            if reason:
                deny(f"blocked by claude-folder-handler/10-pre-deny-secrets: {reason}")

    allow()
    return 0  # unreachable; allow() exits


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        # Fail-open on hook errors (we'd rather not deadlock the session).
        sys.stderr.write(f"10-pre-deny-secrets hook error (allowing): {e}\n")
        sys.exit(0)
