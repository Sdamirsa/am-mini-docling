---
name: clean-data
description: |
  Builds a reviewable, step-by-step preprocessing pipeline for a tabular dataset: column renames/dtype coercions, null handling per column (drop / fill / flag), deduplication, parsing dates/strings, basic outlier handling. Surfaces each step to the user for confirmation before stacking the next. Saves the pipeline as a Python function the user can re-run. Use when the user says "clean this", "preprocess this", "handle missing values", "tidy this dataframe", "fix the dtypes", "deduplicate this", "parse the date column", "drop bad rows from", or asks how to prepare a dataset for modeling. NOT for inspecting/describing data — use inspect-df first. NOT for visualizing — use quick-chart. NOT for irreversible in-place mutation; always operates on a `.copy()`.
---

# clean-data

Incremental, reviewable preprocessing pipeline.

## Workflow

1. Start from a known input (call `inspect-df` first if profile is unknown).
2. Propose ONE cleaning step at a time:
   - Step N: `<operation>` on `<column(s)>`, e.g., "fillna(0) on `price`".
   - Show: before/after counts (null delta, shape delta, dtype delta, dup delta).
   - Pause for user confirmation.
3. On confirmation, append the step to the pipeline as a function.
4. Repeat until the user says "done" or the data is clean.
5. Save the full pipeline as a Python function:
   ```python
   def clean(df: pd.DataFrame) -> pd.DataFrame:
       df = df.copy()
       df = df.rename(...)
       df["price"] = df["price"].fillna(0)
       df = df.drop_duplicates(...)
       return df
   ```
6. Suggest adding a `<!-- last-reviewed: YYYY-MM-DD -->` note in
   `.claude/reference/datasets/<name>.md` documenting the cleaning decisions.

## Constraints

- One step at a time; never stack 5 transformations and present as fait accompli.
- Always works on `.copy()`; never `inplace=True`.
- Surface tradeoffs: "dropping 200 rows with null `age` will bias the sample toward younger users — keep going or use a fill?"
- Never silently coerce types; show the dtype change and confirm.
