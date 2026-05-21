---
name: inspect-df
description: |
  Profiles a pandas/polars/pyarrow dataframe: dtypes, shape, null counts per column, cardinality, basic descriptive stats for numeric columns, sample of unique values for categorical columns, and the first 5 rows. Loads from a file path (csv, parquet, feather, jsonl) or inspects an in-memory df named in user code. Reports as a structured markdown summary; never modifies the data. Use when the user says "what's in this dataframe", "describe the data", "what columns does X have", "summarize this csv", "profile <file>", "show me the schema of", "what's in <name>.parquet", or pastes a path to a tabular file. NOT for cleaning the data — use the clean-data skill. NOT for visualizing — use quick-chart from +visualization.
---

# inspect-df

Read-only profile of a tabular dataset.

## Workflow

1. Identify the input: a file path, a variable name in surrounding code, or a question about a known dataset.
2. If file path:
   - Detect format from extension (`.csv`, `.parquet`, `.feather`, `.jsonl`, `.tsv`, `.xlsx`).
   - Use pandas (or polars if the project uses it).
   - Read with sensible defaults (`low_memory=False` for csv, no index col guessing).
3. Profile:
   - `df.shape` → rows × cols
   - `df.dtypes` per column
   - `df.isna().sum()` → null counts per column
   - `df.nunique()` → cardinality per column
   - For numeric: `df.describe()` (count, mean, std, min, 25/50/75%, max).
   - For categorical (cardinality ≤ 50): list of unique values + count.
   - For high-cardinality (e.g. free text): top-5 by frequency + a "[N unique]" tag.
   - `df.head()` (first 5 rows).
4. Format as markdown sections; offer to save the profile under `.claude/reference/datasets/<name>.md` if it's worth keeping.

## Constraints

- Never writes to the source file.
- Never modifies the dataframe in place (always `.copy()` for any inspection that would mutate).
- For very large files, sample (`nrows=10_000`) and label the profile as "sampled".
