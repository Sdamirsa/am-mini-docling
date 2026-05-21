---
paths:
  - "**/*.py"
  - "**/*.ipynb"
applies_when: "file contains 'import pandas' or 'import polars'"
---

# Pandas / polars conventions

- Use `df.copy()` before any chained operation; never `inplace=True`.
- Avoid chained indexing (`df['a']['b']`); use `df.loc[a, b]`.
- For new code, prefer `pd.options.mode.copy_on_write = True` (pandas 2.0+).
- `pd.read_csv` with explicit dtypes when known; avoid `low_memory=True` for production code.
- Prefer `pa.Table` / parquet over csv for intermediate storage.
- Never `pd.concat` in a loop; collect to a list and concat once.
- Be explicit about indexes: `reset_index(drop=True)` after operations that
  scramble indexes if a clean numeric index is needed.
- Use `query()` for readable filters when the predicate is non-trivial.
- For categorical columns, dtype `"category"` is a 10× memory + speed win.

## Notebook-specific (when `.ipynb`)

- Clear outputs before committing (or use a pre-commit hook). Outputs are
  large diffs and may contain secrets.
- Pin the kernel: `metadata.kernelspec` should reference a specific named env.
- Section headings via markdown cells; one logical step per cell.
