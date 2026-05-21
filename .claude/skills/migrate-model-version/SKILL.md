---
name: migrate-model-version
description: |
  Migrates Claude model identifiers across the codebase from one version to another (e.g., `claude-sonnet-4-5` → `claude-sonnet-4-6`). Greps for the old model ID, lists every call site, shows the proposed diff, and applies on confirmation. Verifies the new model exists in the Anthropic model catalog (consulting reference/apis/anthropic-sdk.md). Use when the user says "upgrade to claude 4.7", "migrate to a newer Claude version", "swap the model version", "bump the model ID", "switch from sonnet to opus", or names a specific from→to model pair. NOT for changing models at runtime via config (that's normal code editing); this skill is for project-wide hard-coded migrations. NOT for non-Anthropic model IDs.
---

# migrate-model-version

Project-wide migration of Claude model identifiers.

## Workflow

1. Identify the from/to model IDs from the user's request, or ask if ambiguous.
2. Confirm the target exists per `.claude/reference/apis/anthropic-sdk.md` (or
   surface a warning if the reference is stale).
3. `grep -rn "<from-id>" --include="*.py" --include="*.ts" --include="*.js" --include="*.toml" --include="*.yaml" --include="*.json" --include="*.md"`
4. Filter false positives (e.g., a changelog entry that should not change).
5. Build the change list:
   - file:line → before → after
6. Show the diff. Wait for confirmation.
7. Apply via Edit per file.
8. Run the project's tests if fast; surface any new failures (likely none, but
   model-version changes can flip cached evals).
9. Suggest opening a PR via the `open-pr` skill if +pr-flow is installed.

## Constraints

- Doesn't replace model IDs inside docstrings/comments unless the user asks
  (those usually document historical context).
- Surfaces every match before applying — no silent global replace.
- Updates `.claude/reference/apis/anthropic-sdk.md`'s "current default" if
  the user is migrating the project's default.
