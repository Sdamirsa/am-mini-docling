<!-- last-reviewed: 2026-05-18 -->

# Schema: `<name>`

> Copy this file to `<name>.md` and fill in. Update `last-reviewed` on
> every revision.

## Purpose
- What this schema extracts: <e.g., "Author + title + DOI from PDF metadata">
- Used by extractor(s): `extractors/<name>/`
- Schema version: 1.0.0

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "authors": {"type": "array", "items": {"type": "string"}},
    "doi": {"type": ["string", "null"], "pattern": "^10\\."}
  },
  "required": ["title", "authors"]
}
```

## Pydantic model

```python
class Record(BaseModel):
    title: str
    authors: list[str]
    doi: str | None = None
```

## Example valid record

```json
{"title": "...", "authors": ["..."], "doi": "10.1234/xyz"}
```

## Example invalid

```json
{"authors": [], "doi": "12.bad-doi"}  // missing title; DOI fails pattern
```

## Known edge cases

- Single author vs list of one (always list).
- Honorifics in author names ("Dr. Foo" vs "Foo").
- Trailing whitespace in title — strip.
- DOI with "doi:" prefix — strip before validation.

## Change log
- v1.0.0 (YYYY-MM-DD): initial.
