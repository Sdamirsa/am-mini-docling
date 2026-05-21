# Global conventions

Always-loaded. Keep this file short — long rules belong in path-scoped files.

## Code
- Prefer editing existing files to creating new ones.
- Don't add comments unless the WHY is non-obvious.
- Default to writing no error handling unless the failure case is real.
- Don't introduce abstractions for hypothetical future requirements.

## Tests
- Run the local test gate before declaring a task done.
- If you can't run tests in the current environment, say so explicitly.

## Git
- Create new commits; don't amend or rewrite history without explicit ask.
- Don't bypass hooks (`--no-verify`).
- Don't push to `main`/`master`/`develop`/`release/*` without explicit ask.

## Reference catalog
- Before designing a new schema, prompt, extractor, or chart, consult `.claude/reference/INDEX.md`.
- New persistent knowledge → add a file under `.claude/reference/<topic>/` with a `<!-- last-reviewed: YYYY-MM-DD -->` header.
