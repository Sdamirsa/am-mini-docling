# Issues with upstream Docling

Tracking known limitations / bugs in upstream Docling that affect the
**Amir Engine** build. Each issue file describes a single failure mode with
a reproducer, root-cause hypothesis, and tested workarounds (if any).

## Conventions

- One markdown file per issue, kebab-case filename.
- Front-matter as a header table: `Severity`, `Status`, `First-seen`, `Upstream-issue`.
- Reproducer must be a concrete file in this repo (e.g. under `samples/` or
  `tests/data/`) — no "I once saw this".
- Workarounds must say whether they were *tested* or *hypothesised*.

## Index

| File | One-line summary |
|---|---|
| [reading-order-mixed-layout-page.md](reading-order-mixed-layout-page.md) | Column-flip on a page that mixes full-width (abstract spillover) and two-column body regions. |
