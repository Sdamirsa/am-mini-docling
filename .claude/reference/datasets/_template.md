<!-- last-reviewed: 2026-05-18 -->

# Dataset card: `<dataset-name>`

> Copy this file to `<dataset-name>.md` and fill in. Update `last-reviewed`
> when you revisit / re-verify the contents.

## Source
- Origin: <where this came from>
- License: <license / use restrictions>
- Acquired: <date / via API / via collaborator>
- File(s): `<path>/<file>.parquet`

## Schema
| Column | Dtype | Nullable | Description |
|---|---|---|---|
| `<col>` | `int64` | no | Primary key |
| `<col>` | `string` | yes | Free-text label |

## Volume
- Rows: ~<N>
- Size: <N> MB

## Known gotchas
- <e.g., dates in `event_at` are UTC, but the legacy `created` column is local time>
- <e.g., 12% of rows have `value=-1` as a sentinel; treat as null>

## Cleaning pipeline applied
- See `.claude/reference/datasets/<dataset>-cleaning.py` if applicable.

## Related
- ADR: `.claude/reference/adr/000X-<topic>.md`
- Experiment: `.claude/reference/experiments/<YYYY-MM>-<topic>.md`
