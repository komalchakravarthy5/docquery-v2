# DocQuery – Query Capabilities Guide

## What your project can answer well

1. **Single-document factual Q&A**
   - "What is the objective of this paper?"
   - "Which dataset was used in this study?"

2. **Section-level extraction**
   - "List the evaluation metrics mentioned in the paper."
   - "What are the limitations discussed by the authors?"

3. **Summaries and key findings**
   - "Summarize the key findings from this document."
   - "Give me a 5-point executive summary."

4. **Multi-document comparison (best with 2–5 files)**
   - "Compare the approaches used across the uploaded papers."
   - "Which model performs best across these studies?"

5. **Source-specific querying**
   - Use the source dropdown in chat to restrict to one file:
   - "In this specific paper, what is the proposed method?"

## Recommended user query patterns

- Be specific: include method names, section names, or result type.
- For comparisons, ask with explicit dimensions:
  - performance, dataset, architecture, limitations.
- For long files, ask iterative questions:
  - first summary, then deeper follow-ups.

## Known limits

- If retrieved chunks miss a detail, response may say information is unavailable.
- Tables/images without OCR-friendly text may reduce answer quality.
- For very large batches, processing time rises with total pages.

## Metrics you can now present in capstone demo

- Runtime metrics in app UI:
  - Average Latency (ms)
  - Average Relevance
  - Success Rate
  - Total Queries
  - Latency Trend graph

- Offline benchmark metrics (`backend/evaluation/rag_quality_metrics.py`):
  - Answer F1 overlap
  - Retrieval Precision
  - Retrieval Recall
  - Retrieval F1

These align with common RAG project evaluation practice and are suitable for literature-comparison style academic review.
