"""Chunked text view of a converted PDF, written as ``chunks.jsonl``.

Wraps :class:`docling_core.transforms.chunker.HybridChunker` so an agent or
RAG pipeline can consume per-PDF chunks without rebuilding the chunker
configuration each time. The output sits next to ``nodes.jsonl`` and
``document.json`` in the per-PDF output folder.

Each line in ``chunks.jsonl`` is one chunk:

```json
{
  "index": 0,
  "text": "1. Introduction\\n...",
  "token_count": 487,
  "headings": ["1. Introduction"],
  "page_nos": [2, 3],
  "self_refs": ["#/texts/12", "#/texts/13"]
}
```
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from docling_core.transforms.chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

if TYPE_CHECKING:
    from docling.datamodel.document import ConversionResult

_log = logging.getLogger(__name__)

_CHUNKS_FILENAME = "chunks.jsonl"

DEFAULT_TOKENIZER = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MAX_TOKENS = 512  # matches MiniLM model_max_length; bump alongside tokenizer.


class ChunkerError(RuntimeError):
    """Raised when chunking cannot complete."""


@dataclass
class ChunkPaths:
    """Path bundle returned by :func:`write_chunks`."""

    chunks_jsonl: Path
    chunk_count: int
    tokenizer_repo: str
    max_tokens: int


def write_chunks(
    result: ConversionResult,
    pdf_dir: Path,
    *,
    tokenizer_repo: str = DEFAULT_TOKENIZER,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    merge_peers: bool = True,
) -> ChunkPaths:
    """Run HybridChunker over the DoclingDocument and persist ``chunks.jsonl``."""
    if result.document is None:
        raise ChunkerError("ConversionResult has no document.")

    pdf_dir.mkdir(parents=True, exist_ok=True)
    target = pdf_dir / _CHUNKS_FILENAME

    tokenizer = HuggingFaceTokenizer.from_pretrained(
        model_name=tokenizer_repo, max_tokens=max_tokens
    )
    chunker = HybridChunker(tokenizer=tokenizer, merge_peers=merge_peers)

    count = 0
    with target.open("w", encoding="utf-8") as fh:
        for idx, chunk in enumerate(chunker.chunk(dl_doc=result.document)):
            row = _chunk_to_dict(idx, chunk, tokenizer)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1

    _log.info(
        "Chunks written: %s (%d chunks, tokenizer=%s, max_tokens=%d)",
        target,
        count,
        tokenizer_repo,
        max_tokens,
    )
    return ChunkPaths(
        chunks_jsonl=target,
        chunk_count=count,
        tokenizer_repo=tokenizer_repo,
        max_tokens=max_tokens,
    )


def _chunk_to_dict(index: int, chunk, tokenizer) -> dict:
    """Serialise a HybridChunker chunk for JSONL."""
    text = chunk.text
    token_count: int | None
    try:
        token_count = tokenizer.count_tokens(text=text)
    except Exception:
        token_count = None

    meta = chunk.meta
    headings = list(getattr(meta, "headings", None) or [])
    captions = list(getattr(meta, "captions", None) or [])

    doc_items = list(getattr(meta, "doc_items", None) or [])
    self_refs: list[str] = []
    page_nos: list[int] = []
    for item in doc_items:
        ref = getattr(item, "self_ref", None)
        if ref:
            self_refs.append(ref)
        for prov in getattr(item, "prov", None) or []:
            page_no = getattr(prov, "page_no", None)
            if page_no is not None and page_no not in page_nos:
                page_nos.append(page_no)

    return {
        "index": index,
        "text": text,
        "token_count": token_count,
        "headings": headings,
        "captions": captions,
        "page_nos": sorted(page_nos),
        "self_refs": self_refs,
    }
