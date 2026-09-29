# am-mini-docling · the Amir Engine 📌

> **A fork of [Docling](https://github.com/docling-project/docling) that turns one PDF into one folder an AI agent (or a tired human) can actually use.**
> Upstream Docling docs follow [further down](#docling-upstream).

## ⚡ TL;DR

```bash
uv sync                                     # install
uv run amir-batch my-paper.pdf -o out/      # convert → out/my-paper/
open out/my-paper/preview.embedded.html     # look at it (one file, works offline)
```

That's it. Everything below is optional reading.

## 🖥️ Hardware for the suggested config

| Mode | Command | GPU | Speed (68-page paper) |
|---|---|---|---|
| **Suggested (default)** — VLM figure descriptions + VLM tables | `amir-batch paper.pdf` | **≥ 32 GB GPU memory** (measured peak **25.5 GB**) | ~13 min |
| Fast — no VLMs | `amir-batch paper.pdf --picture-description off --no-granite-vision-tables` | not required (this run used the GPU for layout; CPU-only is slower, untimed) | ~1 min |

Measured on an NVIDIA GB10 (DGX Spark, 128 GB unified memory), HF `transformers` backend. First run downloads ~12 GB of model weights. 24 GB cards are untested.

## 🧠 The suggested config (what `amir-batch` does by default)

| Stage | Model | Why |
|---|---|---|
| Layout + reading order | Docling **Heron** layout model | upstream default, fast |
| Tables | **Granite-Vision 3.2-2B** (VLM) | better than TableFormer on messy clinical tables |
| Figure descriptions | **Granite-Vision 4.1-4B** (VLM) | one paragraph per figure → `figures.jsonl[*].vlm_caption` |
| Figure classification | Docling picture classifier | tags + strips logos / repeated banners ("noise") |
| Chunking | Docling `HybridChunker`, MiniLM tokenizer, 512 tokens | ready for embeddings / RAG |

VLM runtime: HF `transformers` by default; if [vLLM](https://github.com/vllm-project/vllm) is installed it is picked up automatically (`picture_description_engine="vllm"` to force). No LLM API calls: everything runs locally. The outputs are shaped so *your* LLM can read them (chunks, tables, figures as JSONL).

## 📦 What you get per PDF

```
out/<pdf-name>/
├── preview.embedded.html   👀 clickable viewer, ONE file, images inlined: share this
├── preview.html            👀 same viewer, links to images/ (small; keep the folder together)
├── <pdf-name>.md           📝 markdown, figures linked from images/
├── <pdf-name>.embedded.md  📝 markdown, figures inlined (one file)
├── chunks.jsonl            🤖 text chunks + headings + page numbers + self_refs
├── tables.jsonl            🤖 one row per table: caption, markdown, html, cells
├── figures.jsonl           🤖 one row per figure: caption, VLM description, class, noise flag
├── nodes.jsonl             🤖 every document node with bbox
├── document.json           🤖 full DoclingDocument (lossless)
├── run.json                🧾 models, options, timing, package versions
└── images/                 🖼️ page renders + figure/table crops
```

**Citable:** every chunk/table/figure carries a `self_ref` (e.g. `#/texts/12`). Open `preview.html?ref=%23%2Ftexts%2F12` to jump to the highlighted box on the page. See [docs/hand-off-notes/hand-off-note-for-citation.md](docs/hand-off-notes/hand-off-note-for-citation.md).

## 🔬 Worked example (real output, committed)

Input: [`showcase/Public-test-manuscript.pdf`](showcase/Public-test-manuscript.pdf): *Vision-Language and Large Language Model Performance in Gastroenterology* (arXiv preprint, 68 pages), shared by its first author.

Output: [`showcase/Public-test-manuscript/`](showcase/Public-test-manuscript/), produced by the default config above:
**68 pages · 15 figures (all VLM-described) · 17 tables · 131 chunks · 0 errors · 13 min 17 s.**

- Standalone viewer: [`preview.embedded.html`](showcase/Public-test-manuscript/preview.embedded.html) (download, then open in a browser)
- Markdown: [`Public-test-manuscript.md`](showcase/Public-test-manuscript/Public-test-manuscript.md)
- Figures + VLM descriptions: [`figures.jsonl`](showcase/Public-test-manuscript/figures.jsonl)

Known rough edges seen in this run: some supplementary figures/tables have no detected caption, and the picture classifier occasionally mislabels a chart (e.g. `calendar`). The VLM descriptions are still correct for those figures.

## 🧩 What this fork adds on top of Docling

- `docling/engines/`: the Amir Engine (`PdfEngine`), the only new code subtree
- `amir-batch` CLI: batch conversion with a rich summary table (`--compare` A/Bs against full-page GraniteDocling)
- Clickable HTML bbox viewer, linked + standalone versions, deep-linkable by `self_ref`
- Agent-ready JSONL (chunks / tables / figures / nodes) + `run.json` provenance
- Noise filter for journal logos and repeated banners
- Granite-Vision 4.1-4B figure-description preset + Granite-Vision tables, with fixes so they load under current `transformers`

More: [RUN.md](RUN.md) (CLI reference) · [.claude/HANDOFF.md](.claude/HANDOFF.md) (architecture + defaults).

---

<a id="docling-upstream"></a>

<p align="center">
  <a href="https://github.com/docling-project/docling">
    <img loading="lazy" alt="Docling" src="https://github.com/docling-project/docling/raw/main/docs/assets/docling_processing.png" width="100%"/>
  </a>
</p>

# Docling (upstream)

<p align="center">
  <a href="https://trendshift.io/repositories/17240" target="_blank"><img src="https://trendshift.io/api/badge/repositories/17240" alt="DS4SD%2Fdocling | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

[![arXiv](https://img.shields.io/badge/arXiv-2408.09869-b31b1b.svg)](https://arxiv.org/abs/2408.09869)
[![Docs](https://img.shields.io/badge/docs-live-brightgreen)](https://docling-project.github.io/docling/)
[![PyPI version](https://img.shields.io/pypi/v/docling)](https://pypi.org/project/docling/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/docling)](https://pypi.org/project/docling/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![prek](https://img.shields.io/badge/prek-enabled-brightgreen)](https://pypi.org/project/prek/)
[![License MIT](https://img.shields.io/github/license/docling-project/docling)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://static.pepy.tech/badge/docling/month)](https://pepy.tech/projects/docling)
[![Docling Actor](https://apify.com/actor-badge?actor=vancura/docling&fpr=docling)](https://apify.com/vancura/docling)
[![Chat with Dosu](https://dosu.dev/dosu-chat-badge.svg)](https://app.dosu.dev/097760a8-135e-4789-8234-90c8837d7f1c/ask?utm_source=github)
[![Discord](https://img.shields.io/discord/1399788921306746971?color=6A7EC2&logo=discord&logoColor=ffffff)](https://docling.ai/discord)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10101/badge)](https://www.bestpractices.dev/projects/10101)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-003778?logo=linuxfoundation&logoColor=fff&color=0094ff&labelColor=003778)](https://lfaidata.foundation/projects/)

## What is Docling ?

Docling simplifies document processing, parsing diverse formats — including advanced PDF understanding — and providing seamless integrations with the gen AI ecosystem.

## Features

- 🗂️ Parsing of [multiple document formats][supported_formats] incl. PDF, DOCX, PPTX, XLSX, HTML, WAV, MP3, WebVTT, images (PNG, TIFF, JPEG, ...), LaTeX, plain text, and more
- 📑 Advanced PDF understanding incl. page layout, reading order, table structure, code, formulas, image classification, and more
- 🧬 Unified, expressive [DoclingDocument][docling_document] representation format
- ↪️ Various [export formats][supported_formats] and options, including Markdown, HTML, WebVTT, [DocTags](https://arxiv.org/abs/2503.11576) and lossless JSON
- 📜 Support of several application-specifc XML schemas incl. [USPTO](https://www.uspto.gov/patents) patents, [JATS](https://jats.nlm.nih.gov/) articles, and [XBRL](https://www.xbrl.org/) financial reports.
- 🔒 Local execution capabilities for sensitive data and air-gapped environments
- 🤖 Plug-and-play [integrations][integrations] incl. LangChain, LlamaIndex, Crew AI & Haystack for agentic AI
- 🔍 Extensive OCR support for scanned PDFs and images
- 👓 Support of several Visual Language Models ([GraniteDocling](https://huggingface.co/ibm-granite/granite-docling-258M))
- 🎙️ Audio support with Automatic Speech Recognition (ASR) models
- 🔌 Connect to any agent using the [MCP server](https://docling-project.github.io/docling/usage/mcp/)
- 💻 Simple and convenient CLI

### What's new

- 📤 Structured [information extraction][extraction] \[🧪 beta\]
- 📑 New layout model (**Heron**) by default, for faster PDF parsing
- 🔌 [MCP server](https://docling-project.github.io/docling/usage/mcp/) for agentic applications
- 💼 Parsing of XBRL (eXtensible Business Reporting Language) documents for financial reports
- 💬 Parsing of WebVTT (Web Video Text Tracks) files and export to WebVTT format
- 💬 Parsing of LaTeX files
- 📝 Parsing of plain-text files (`.txt`, `.text`) and Markdown supersets (`.qmd`, `.Rmd`)
- 📝 Chart understanding (Barchart, Piechart, LinePlot): converting them into tables, code or adding detailed descriptions

### Coming soon

- 📝 Metadata extraction, including title, authors, references & language
- 📝 Complex chemistry understanding (Molecular structures)

## Quickstart

### 1. Install

```bash
pip install docling
```

> **Note:** Python 3.9 support was dropped in docling version 2.70.0. Please use Python 3.10 or higher.

Works on macOS, Linux and Windows environments. Both x86_64 and arm64 architectures.

More [detailed installation instructions](https://docling-project.github.io/docling/installation/) are available in the docs.

## 2. Convert a document (CLI)

```bash
docling https://arxiv.org/pdf/2206.01062
```

This generates a .md file in the current directory containing structured document content.

You can also use 🥚[GraniteDocling](https://huggingface.co/ibm-granite/granite-docling-258M) and other VLMs via Docling CLI:

```bash
docling --pipeline vlm --vlm-model granite_docling https://arxiv.org/pdf/2206.01062
```

## 3. Python usage (recommended)

```python
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"  # document per local path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "## Docling Technical Report[...]"
```

More advanced [usage](https://docling-project.github.io/docling/usage/) and [configuration](https://docling-project.github.io/docling/installation/) options.

## Documentation

Check out Docling's [documentation](https://docling-project.github.io/docling/), for details on
installation, usage, concepts, recipes, extensions, and more.

## Examples

Go hands-on with our [examples](https://docling-project.github.io/docling/examples/),
demonstrating how to address different application use cases with Docling.

## Integrations

To further accelerate your AI application development, check out Docling's native
[integrations](https://docling-project.github.io/docling/integrations/) with popular frameworks
and tools.

## Get help and support

Please feel free to connect with us using the [discussion section](https://github.com/docling-project/docling/discussions).

## Technical report

For more details on Docling's inner workings, check out the [Docling Technical Report](https://arxiv.org/abs/2408.09869).

## Contributing

Please read [Contributing to Docling](https://github.com/docling-project/docling/blob/main/CONTRIBUTING.md) for details.

## References

If you use Docling in your projects, please consider citing the following:

```bib
@techreport{Docling,
  author = {Deep Search Team},
  month = {8},
  title = {Docling Technical Report},
  url = {https://arxiv.org/abs/2408.09869},
  eprint = {2408.09869},
  doi = {10.48550/arXiv.2408.09869},
  version = {1.0.0},
  year = {2024}
}
```

## License

The Docling codebase is under MIT license.
For individual model usage, please refer to the model licenses found in the original packages.

## LF AI & Data

Docling is hosted as a project in the [LF AI & Data Foundation](https://lfaidata.foundation/projects/).

### IBM ❤️ Open Source AI

The project was started by the AI for knowledge team at IBM Research Zurich.

[supported_formats]: https://docling-project.github.io/docling/usage/supported_formats/
[docling_document]: https://docling-project.github.io/docling/concepts/docling_document/
[integrations]: https://docling-project.github.io/docling/integrations/
[extraction]: https://docling-project.github.io/docling/examples/extraction/
