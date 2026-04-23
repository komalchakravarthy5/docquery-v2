# RAG Benchmark Protocol (Capstone)

## Goal
Benchmark DocQuery against standard RAG metrics for academic comparison.

## Dataset design
- 100–200 questions total
- 4 buckets:
  1. factual extraction
  2. summarization
  3. cross-document comparison
  4. numerical/table lookup

Each sample should include:
- `question`
- `ground_truth_answer`
- `ground_truth_sources` (list of expected source filenames)
- `retrieved_sources` (captured from model citations)
- `predicted_answer`

## Metrics to report
1. Retrieval Precision
2. Retrieval Recall
3. Retrieval F1
4. Answer F1 overlap
5. Faithfulness (LLM-as-judge score 1–5)
6. Answer Relevance (LLM-as-judge score 1–5)
7. Latency P50 / P95 (from API runtime metrics)
8. Grounding score (token support ratio)

## Protocol
1. Freeze model/configuration.
2. Run all benchmark questions with deterministic temperature.
3. Save outputs and citations.
4. Compute `rag_quality_metrics.py` metrics.
5. Add faithfulness/relevance judge pass.
6. Compare to at least 2 baseline settings:
   - semantic retrieval only
   - hybrid retrieval enabled

## Reporting template
- Table 1: Retrieval metrics
- Table 2: Answer quality metrics
- Table 3: Latency and throughput
- Figure 1: Latency trend
- Figure 2: Faithfulness/Relevance distribution
