---
name: quick-chart
description: |
  Produces an appropriate chart (matplotlib, plotly, or altair depending on the project's existing imports) from a dataframe and a natural-language question. Picks the chart type based on the variable types (numeric × numeric → scatter; numeric × categorical → boxplot/violin; categorical × count → bar; time × numeric → line; one numeric → histogram). Adds title, axis labels, legend, color-blind-safe palette, and saves a PNG to `figures/` (or a configured path). Use when the user says "plot X", "make a chart of Y", "visualize this", "graph the data", "show me a histogram of", "scatter X vs Y", "make a bar chart of", "line chart of Z over time", or asks how something looks. NOT for critiquing existing charts — use chart-review. NOT for interactive dashboards — this is single-figure output; use streamlit/dash for live UIs.
---

# quick-chart

Pick a chart, render it, save it.

## Workflow

1. Identify the data source (dataframe in cwd code / a file path / inline data).
2. Identify the encoding question:
   - one numeric → histogram or kde
   - two numeric → scatter (or hexbin if N > 5000)
   - numeric × categorical → boxplot (ordered by median)
   - categorical × count → horizontal bar (sorted desc)
   - time × numeric → line (single) or small-multiples (multi)
3. Pick the library based on existing project imports (matplotlib by default).
4. Apply style conventions from `.claude/reference/charts/_examples.md` if it exists.
5. Render:
   - Figure size 8×5 inches; dpi 150 for print, 100 for screen.
   - Color-blind-safe palette (e.g., okabe-ito or viridis for sequential).
   - Title (short), axis labels (with units), legend if needed.
   - No chartjunk (no 3D, no gradients, no shadows).
6. Save PNG to `figures/<descriptive-name>.png` (creating `figures/` if needed).
7. Return: figure path, the rendering code, and a one-line description.

## Constraints

- Never silently picks a chart type the question doesn't match.
- Always saves; doesn't rely on `plt.show()` in non-interactive code.
- For >2 dimensions, faceting > color-coding > size-coding (in that preference).
- Refuses pie charts unless explicitly asked (and warns about angular perception).
