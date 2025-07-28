# Adobe Hackathon Round 1B - Persona-Based Document Analysis

## Overview

This solution identifies and ranks the most relevant sections across a collection of PDFs based on:
- A specified persona
- A job-to-be-done description

It outputs metadata, ranked sections, and refined summaries without internet access or large models.

## Features

- Accepts multiple collections (e.g., Collection 1, Collection 2)
- Extracts and ranks relevant sections
- Generates refined text snippets per section
- Fully offline and CPU-only
- Execution time < 60s

## Directory Structure

```
Collection X/
├── challenge1b_input.json
├── PDFs/
└── challenge1b_output.json (generated)
```

## Build

```bash
docker build --platform linux/amd64 -t doc-analyst .
```

## Run

```bash
docker run --rm -v $(pwd):/app doc-analyst
```

To process a specific folder:

```bash
docker run --rm -v $(pwd):/app doc-analyst "Collection 1"
```

## Output Format

```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Analyst",
    "job_to_be_done": "Summarize trends",
    "processing_timestamp": "..."
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "section_title": "Market Overview",
      "importance_rank": 1,
      "page_number": 2
    }
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "The market is expected to grow rapidly...",
      "page_number": 2
    }
  ]
}
```

## Notes

- Heuristic-based summarization without LLMs or APIs
- Lightweight, modular, and optimized for offline use