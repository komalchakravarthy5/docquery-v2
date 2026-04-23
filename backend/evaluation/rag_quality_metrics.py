"""RAG quality evaluation helper for capstone benchmarking.

Usage:
  python backend/evaluation/rag_quality_metrics.py --pred predictions.json --out metrics_report.json

Input format (JSON list):
[
  {
    "question": "...",
    "ground_truth_answer": "...",
    "predicted_answer": "...",
    "ground_truth_sources": ["paper1.pdf", "paper2.pdf"],
    "retrieved_sources": ["paper1.pdf", "paper3.pdf"]
  }
]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Dict, List


def token_set(text: str) -> set[str]:
    punctuation = ".,!?;:()[]{}\"'`"
    return {tok.strip(punctuation).lower() for tok in text.split() if tok.strip()}


def f1_overlap(reference: str, predicted: str) -> float:
    ref = token_set(reference)
    pred = token_set(predicted)
    if not ref or not pred:
        return 0.0
    common = len(ref & pred)
    precision = common / len(pred)
    recall = common / len(ref)
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def source_metrics(gt_sources: List[str], ret_sources: List[str]) -> Dict[str, float]:
    gt = set(gt_sources)
    ret = set(ret_sources)
    tp = len(gt & ret)
    precision = tp / len(ret) if ret else 0.0
    recall = tp / len(gt) if gt else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def evaluate(samples: List[dict]) -> Dict[str, float]:
    answer_f1_scores = []
    retrieval_precision_scores = []
    retrieval_recall_scores = []
    retrieval_f1_scores = []

    for sample in samples:
        answer_f1_scores.append(
            f1_overlap(sample.get("ground_truth_answer", ""), sample.get("predicted_answer", ""))
        )
        m = source_metrics(
            sample.get("ground_truth_sources", []),
            sample.get("retrieved_sources", []),
        )
        retrieval_precision_scores.append(m["precision"])
        retrieval_recall_scores.append(m["recall"])
        retrieval_f1_scores.append(m["f1"])

    return {
        "num_samples": len(samples),
        "answer_f1": round(mean(answer_f1_scores), 4) if answer_f1_scores else 0.0,
        "retrieval_precision": round(mean(retrieval_precision_scores), 4) if retrieval_precision_scores else 0.0,
        "retrieval_recall": round(mean(retrieval_recall_scores), 4) if retrieval_recall_scores else 0.0,
        "retrieval_f1": round(mean(retrieval_f1_scores), 4) if retrieval_f1_scores else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True, help="Path to predictions JSON file")
    parser.add_argument("--out", default="metrics_report.json", help="Output report path")
    args = parser.parse_args()

    with open(args.pred, "r", encoding="utf-8") as f:
        samples = json.load(f)

    report = evaluate(samples)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
