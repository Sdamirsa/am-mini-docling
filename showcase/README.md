# Showcase: one paper, three configs

Same input, three `amir-batch` configurations, full output committed for each.
Pick the folder that matches your hardware and open its `preview.embedded.html`.

**Input:** [`Public-test-manuscript.pdf`](Public-test-manuscript.pdf):
*Vision-Language and Large Language Model Performance in Gastroenterology*
(arXiv preprint, 68 pages, 15 figures, 17 tables), shared by its first author.

## ⚡ Which one should I look at?

| Folder | Command | Figures | Tables | GPU | Time* |
|---|---|---|---|---|---|
| [`fast/`](fast/Public-test-manuscript/) | `amir-batch paper.pdf --picture-description off --no-granite-vision-tables` | caption + class only | TableFormer | not required | **1.4 min** |
| [`figures-vlm/`](figures-vlm/Public-test-manuscript/) | `amir-batch paper.pdf --no-granite-vision-tables` | + VLM description | TableFormer | yes (one 4B VLM) | **3.4 min** |
| [`default/`](default/Public-test-manuscript/) | `amir-batch paper.pdf` | + VLM description | Granite-Vision VLM | ≥ 32 GB (peak 25.5 GB) | **13.2 min** |

\*NVIDIA GB10 (DGX Spark). `fast` and `figures-vlm` ran while an unrelated
Ollama server shared the GPU, so their times are upper bounds.

No config calls an external LLM API: everything runs locally. The only VLM is
[Granite-Vision 4.1-4B](https://huggingface.co/ibm-granite/granite-vision-4.1-4b)
(HF `transformers`; vLLM is used instead when installed).

## 🔍 What actually changes between configs

**Same in all three:** 68 pages · 15 figures · 17 tables · ~130 chunks · 0 errors,
same markdown text, same `self_ref` IDs, same viewer.

**Figures:** `fast` gives you the printed caption and a class label
(`bar_chart`, `flow_chart`, ...). The VLM configs add a paragraph in
`figures.jsonl[*].vlm_caption`. For Figure 4:

> *fast:* `Figure 4. LLM Performance on Text-Only Gastroenterology Multiple-choice Questions.` · `bar_chart`
>
> *VLM:* "The chart is a horizontal bar graph titled 'All 2022 ACG questions (N = 300)' and displays the performance of various language models... The bars are segmented into different colors: green for correct answers, red for incorrect answers..."

⚠️ VLM descriptions read well but can misstate numbers. The same paragraph
calls GPT-4's 73.7% "near-perfect". Use them for search and context, and
check figures themselves before citing a value.

**Tables:** TableFormer and Granite-Vision agree on 15 of 17 tables.

| Table | Truth | TableFormer | Granite-Vision |
|---|---|---|---|
| 3 (wide, 11 cols) | 8 × 11 | ✅ 8 × 11 | ✅ in `default/` · ❌ 14 × 10 on Docling v2.131.0 |
| 14 (temperature) | 8 × 3 | ❌ 7 × 3 | ✅ 8 × 3 |
| 17 (sparse, many empty cols) | ~9 cols | ❌ | ❌ |

Takeaway: `figures-vlm` is ~4× faster than `default` with similar table
quality on this paper. `default` is kept as the suggested config because it
wins on some dense tables; try both on your own documents.

## 📦 Inside each folder

```
Public-test-manuscript/
├── preview.embedded.html   👀 viewer, one file (download → open in a browser)
├── preview.html            👀 same viewer, needs images/ next to it
├── *.md / *.embedded.md    📝 markdown (linked / inlined images)
├── chunks.jsonl            🤖 text chunks with headings, pages, self_refs
├── tables.jsonl            🤖 one row per table
├── figures.jsonl           🤖 one row per figure (+ vlm_caption)
├── nodes.jsonl             🤖 every node with bbox
├── document.json           🤖 full DoclingDocument
├── run.json                🧾 exact options, models, package versions, timing
└── images/                 🖼️ page renders + crops
```

GitHub shows `.html` as source: download the file (or clone) and open it locally.

## 🧾 Versions

- `default/` was produced **before** this fork was synced to upstream Docling
  v2.131.0 (docling-core 2.75.0).
- `fast/` and `figures-vlm/` were produced **after** the sync (docling-core 2.98.0).

Each `run.json` has the exact package versions. Reproduce any folder with the
command in the table above plus `-o <dir>`.
