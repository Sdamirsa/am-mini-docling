---
paths:
  - "**/*.py"
  - "**/*.ipynb"
applies_when: "file imports matplotlib, plotly, altair, or seaborn"
---

# Plotting conventions

## Defaults
- Figure size: 8×5 (single) or 12×8 (multi).
- DPI: 150 for any chart that might be printed; 100 for screen-only.
- Color palette: okabe-ito (8 colors, color-blind safe) for categorical;
  viridis for sequential; coolwarm for diverging (centered on a meaningful zero).

## Required on every chart
- Title (short, declarative — "Revenue grew 12% Q4" beats "Revenue over time").
- Axis labels with units.
- Legend if >1 series.
- For time series: explicit x-axis tick rotation 45° or use weekly/monthly grouping.

## Avoid
- Pie charts (use horizontal bar).
- Dual y-axes (split into facets or normalize).
- 3D anything.
- Truncated y-axis on bar charts (always start at 0).

## Save / commit
- Save under `figures/` with descriptive names: `figures/revenue-by-quarter-2026.png`.
- Don't commit large PNGs (>1 MB) — point to S3 or use `.gitattributes` git-lfs.
- Notebooks: clear inline outputs before commit; the figure file is the canonical artifact.
