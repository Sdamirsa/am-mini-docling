#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PreToolUse hook (Bash matcher): block destructive operations.

Covers the bypasses cataloged in the security review:
  - rm -rf variants (-rf, -fr, -r -f, --recursive --force)
  - rm targets resolving to /, /root, ~, $HOME, /home/$USER
  - find ... -delete and find ... -exec rm ...
  - git push --force / -f / --force-with-lease / +ref to protected branches
  - git reset --hard origin/<protected>
  - sudo, su, sudo-anything
  - curl|sh, wget|bash, base64-decode-to-shell
  - SSRF: curl/wget to link-local, cloud metadata IPs
  - shred, truncate -s0, : > FILE on protected paths
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from bash_parse import collect_argv_with_inherited_env, has_flag  # noqa: E402
from paths import canonicalize  # noqa: E402
from payload import allow, deny, read_payload  # noqa: E402


PROTECTED_BRANCHES_DEFAULT = ["main", "master", "develop"]
PROTECTED_PREFIXES_DEFAULT = ["release/"]


def _load_protected(project: Path) -> tuple[list[str], list[str]]:
    cfg = project / ".claude" / ".meta" / "protected-branches.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            entries = data.get("protected", PROTECTED_BRANCHES_DEFAULT)
            exact = [e for e in entries if isinstance(e, str) and not e.endswith("*")]
            prefixes = [e.rstrip("*") for e in entries if isinstance(e, str) and e.endswith("*")]
            return exact, prefixes
        except (json.JSONDecodeError, OSError):
            pass
    return PROTECTED_BRANCHES_DEFAULT, PROTECTED_PREFIXES_DEFAULT


def _is_protected_branch(ref: str, exact: list[str], prefixes: list[str]) -> bool:
    ref = ref.lstrip("+").strip()
    if ":" in ref:
        ref = ref.split(":", 1)[1]
    if ref in exact:
        return True
    return any(ref.startswith(p) for p in prefixes)


METADATA_HOSTS = ("169.254.169.254", "metadata.google.internal", "fd00:ec2::254")


def _check(cmd: str, project: Path) -> str | None:
    exact, prefixes = _load_protected(project)
    home = str(Path.home())
    cwd_str = str(project)

    base64_decode = re.search(r"base64\s+(?:-d|--decode)\b", cmd) is not None

    for clause, argv in collect_argv_with_inherited_env(cmd):
        if not argv:
            continue
        prog = argv[0]

        # ---- sudo / su ----
        if prog in {"sudo", "doas", "su"} or prog.startswith("sudo"):
            return f"`{prog}` is denied (privilege escalation)"

        # ---- rm -rf ----
        if prog == "rm":
            if has_flag(argv, "-r", "-R", "--recursive") and has_flag(argv, "-f", "--force"):
                targets = [a for a in argv[1:] if not a.startswith("-")]
                resolved = [canonicalize(t, cwd=project) for t in targets]
                for r in resolved:
                    rs = str(r)
                    if r == Path("/") or rs in {"/root", home, cwd_str, "/home", "/Users", "/var"}:
                        return f"rm -rf target {r} is denied"
                    if rs.startswith(home + os.sep) and rs.rstrip(os.sep) == home:
                        return f"rm -rf target {r} resolves to $HOME"
                # Wildcards on root or home
                for t in targets:
                    if t in {"/*", "/", "~", "~/", "$HOME", "$HOME/", "$HOME/*"}:
                        return f"rm -rf {t} is denied"

        # ---- find -delete / find -exec rm ----
        if prog == "find":
            if "-delete" in argv:
                return "`find -delete` is denied (mass-delete vector)"
            if "-exec" in argv:
                rest = argv[argv.index("-exec") + 1:] if "-exec" in argv else ()
                if rest and rest[0] in {"rm", "shred", "truncate"}:
                    return f"`find -exec {rest[0]}` is denied"

        # ---- shred / truncate -s0 / : > FILE ----
        if prog == "shred":
            return "`shred` is denied (irrecoverable wipe)"
        if prog == "truncate" and ("-s0" in argv or "--size=0" in argv):
            return "`truncate -s0` is denied"

        # ---- git push --force ----
        if prog == "git" and len(argv) >= 2 and argv[1] == "push":
            force_flag = has_flag(argv, "-f", "--force", "--force-with-lease", "--force-if-includes")
            refspec_force = any(a.startswith("+") and not a.startswith("--") and "/" not in a[:2] for a in argv[2:])
            if force_flag or refspec_force:
                # Inspect refspec targets.
                refs = [a for a in argv[2:] if not a.startswith("-") and a not in {"origin", "upstream"}]
                # Filter to refspec-y tokens
                ref_targets = [r for r in refs if ":" in r or r.startswith("+") or "/" in r or not r.startswith("-")]
                # Heuristic: if we see "HEAD:main" the target is "main"; if we see "main" alone, target is "main".
                for r in ref_targets:
                    target = r.lstrip("+")
                    if ":" in target:
                        target = target.split(":", 1)[1]
                    target = target.split("/")[-1]  # strip refs/heads/ prefix if present
                    if _is_protected_branch(target, exact, prefixes):
                        return f"`git push --force` to protected branch '{target}' is denied"
                # If no explicit branch is named, the current branch is implied; check it.
                if not ref_targets:
                    # Best-effort: read HEAD ref via the git directory.
                    try:
                        head = (project / ".git" / "HEAD").read_text(encoding="utf-8").strip()
                        if head.startswith("ref: refs/heads/"):
                            current = head[len("ref: refs/heads/"):].strip()
                            if _is_protected_branch(current, exact, prefixes):
                                return f"`git push --force` on protected branch '{current}' is denied"
                    except (OSError, UnicodeDecodeError):
                        pass

        # ---- git reset --hard origin/<protected> ----
        if prog == "git" and len(argv) >= 3 and argv[1] == "reset" and "--hard" in argv:
            for tok in argv[2:]:
                if tok.startswith("-"):
                    continue
                ref = tok.split("/")[-1]
                if _is_protected_branch(ref, exact, prefixes):
                    return f"`git reset --hard {tok}` against protected branch is denied"

        # ---- curl/wget piped to shell, SSRF to cloud metadata ----
        if prog in {"curl", "wget"}:
            joined = " ".join(argv)
            if any(host in joined for host in METADATA_HOSTS):
                return f"`{prog}` to cloud metadata endpoint is denied (SSRF/token theft)"

    # Cross-clause: curl|sh / wget|bash / base64|sh.
    if re.search(r"\bcurl\b.*\|\s*(?:sh|bash|zsh)\b", cmd) or re.search(r"\bwget\b.*\|\s*(?:sh|bash|zsh)\b", cmd):
        return "piping curl/wget output to a shell is denied (remote code exec)"
    if base64_decode and re.search(r"\|\s*(?:sh|bash|zsh|eval|exec)\b", cmd):
        return "base64-decoding to shell/eval is denied (obfuscated RCE)"
    if re.search(r"\beval\s+\$\(\s*(?:curl|wget)\b", cmd):
        return "eval-of-curl is denied"

    return None


def _cwd() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def main() -> int:
    payload = read_payload()
    tool = payload.get("tool_name") or payload.get("tool")
    tinput = payload.get("tool_input") or {}
    if tool != "Bash":
        allow()
        return 0

    cmd = tinput.get("command") or tinput.get("cmd") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        allow()
        return 0

    project = _cwd()
    reason = _check(cmd, project)
    if reason:
        deny(f"blocked by claude-folder-handler/20-pre-deny-destructive: {reason}")

    allow()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"20-pre-deny-destructive hook error (allowing): {e}\n")
        sys.exit(0)
