# `.claude/reference/` — editing conventions

The reference catalog stores **persistent, on-demand knowledge** that Claude
consults when relevant — not always-in-context content.

## File header (required)

Every file must start with a `last-reviewed` HTML comment:

```markdown
<!-- last-reviewed: 2026-05-18 -->

# <topic>
...
```

`audit_claude_folder` flags files older than 180 days for review.

## What belongs here vs elsewhere

| Content | Belongs in | Why |
|---|---|---|
| Dataset cards (schema, source, gotchas) | `reference/datasets/` | Read when working with that dataset, not every turn |
| Reusable JSON schemas / pydantic models | `reference/schemas/` | Re-used across extractors |
| System prompts, few-shot templates | `reference/prompts/` | Reusable across tasks |
| External API quick-refs (Anthropic SDK, etc.) | `reference/apis/` | Re-read at relevant moments |
| Architecture decisions | `reference/adr/` | Why we did X, never need to load everywhere |
| Eval results, baselines | `reference/experiments/` | Auditable history |
| Always-on conventions | `.claude/rules/` (path-scoped) | Loaded when relevant files are touched |
| Project-wide truth (build/test/lint) | `CLAUDE.md` (root) | Every-turn context |

## Anti-patterns

- File > 300 lines → split.
- No `last-reviewed` → audit warns.
- Duplicates content from `CLAUDE.md` or `rules/` → choose one home.
- Reference that's actually a workflow → it's a skill, not reference.
- Not listed in `INDEX.md` → orphan; audit warns.
