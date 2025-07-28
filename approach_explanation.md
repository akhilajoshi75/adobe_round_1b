approach_explanation.md

Problem Understanding

The objective of Round 1B is to build an intelligent document analysis system that identifies the most relevant content from a collection of PDFs, guided by a given persona and their task (job-to-be-done). This system should operate offline, be efficient, and return ranked sections and concise summaries without any network dependencies.

Methodology

We structured our solution into three core components:

1. Section Extraction

Using the pdfplumber library, each PDF is parsed page by page. Words are grouped into lines based on vertical proximity, and headings are identified using a mix of heuristics:
- Font size significantly larger than average
- Short line length (potential heading)
- Full uppercase text

When a heading is detected, it marks the beginning of a new section. The lines following it are captured as the section body. Each section is tagged with the source document, title, page number, and content.

2. Section Ranking

To rank the relevance of sections, we compute a score based on how well the section content aligns with the persona and the job-to-be-done. The score combines:
- TF-IDF similarity between section text and persona+job context
- Overlap of meaningful keywords (words longer than 3 characters)
- A penalty if the heading is generic or uninformative (e.g., "Introduction", "Summary")

This approach ensures that the most relevant and content-rich sections are ranked highest.

3. Subsection Refinement

Each top-ranked section is then further refined by selecting key sentences. Sentences are scored based on how many words overlap with the persona and task description. We select sentences until a character limit is reached, or fallback to the first few sentences if there's no keyword match. This produces a concise, meaningful snippet that represents the section.

Technical Implementation

- Language: Python 3.10
- Libraries used: pdfplumber, scikit-learn, numpy
- Model-free, fully offline, CPU-compliant
- Execution time under 10 seconds for typical input

Why This Works

The design prioritizes generalization and robustness. We do not rely on hardcoded formats, and we avoid assumptions about layout or headings. The result is a clean, explainable pipeline that ranks and summarizes PDF content effectively while staying within the constraints of offline execution and small resource usage.