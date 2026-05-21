---
name: chart-review
description: |
  Critiques an existing chart for clarity, encoding, accessibility, and honesty. Reads the rendering code (or the saved figure if PNG metadata or surrounding code is available) and reports issues: misleading axes (truncated, dual-y), poor color choice (no color-blind safety, redundant encoding), chartjunk (3D, shadows, unnecessary gridlines), missing labels/units, inappropriate chart type for the data, and undertelling/overtelling the data. Returns a prioritized list (Must Fix / Should Fix / Could Improve). Use when the user says "is this chart good", "critique this viz", "review my plot", "what's wrong with this figure", "does this chart work", "help me improve this graph", or shares a chart for feedback. NOT for producing a new chart from data — use quick-chart. NOT for layout/design of a multi-chart dashboard.
---

# chart-review

Read a chart's rendering code (or surrounding code if only a PNG exists),
report what's wrong, prioritized.

## Workflow

1. Locate the chart-producing code or the figure path.
2. Inspect the rendering for:
   - **Encoding**: does the chart type match the variable types? (categorical-x-categorical as a bar = wrong)
   - **Axes**: starts at 0 for bars? Truncated y-axis on a difference chart is dishonest.
   - **Color**: color-blind safe? Sequential vs categorical palette appropriate?
   - **Labels**: title, axis labels with units, legend?
   - **Junk**: 3D, shadows, decorative icons, redundant pie slices?
   - **Type fit**: pie chart for >5 slices = bad. Line chart on categorical x = bad.
   - **Annotation**: key takeaway visible at a glance or buried?
3. Output as Must Fix / Should Fix / Could Improve. Be specific (file:line + fix).
4. Don't apply changes — just report.

## Constraints

- Don't moralize about chartjunk; flag and explain the cost.
- Don't tell the user to remix the entire chart unless type is fundamentally wrong; suggest minimal fixes.
- If the chart is fine, say so explicitly.
