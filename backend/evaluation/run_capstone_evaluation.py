"""End-to-end capstone evaluation runner.

Pipeline:
1) Upload selected files to DocQuery API
2) Run benchmark questions from dataset
3) Save predictions
4) Compute retrieval/answer metrics
5) Optionally compute LLM-judge metrics
6) Generate PNG plots

Usage:
python backend/evaluation/run_capstone_evaluation.py \
  --api http://127.0.0.1:8000/api \
  --dataset backend/evaluation/capstone_eval_dataset.json \
  --files /abs/path/setConf.pdf /abs/path/Sales.pdf /abs/path/Consent.pdf \
  --outdir backend/evaluation/results \
  --run-judge
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import requests

from backend.evaluation.rag_quality_metrics import evaluate as evaluate_quality
from backend.evaluation.rag_evaluator import evaluate as evaluate_judge


def upload_workspace(api: str, file_paths: List[str]) -> str:
    files = [("files", (Path(path).name, open(path, "rb"), "application/octet-stream")) for path in file_paths]
    try:
        resp = requests.post(f"{api}/upload", files=files, timeout=600)
        resp.raise_for_status()
        payload = resp.json()
        return payload["document_id"]
    finally:
        for _, file_tuple in files:
            file_tuple[1].close()


def run_queries(api: str, document_id: str, dataset: List[dict]) -> List[dict]:
    outputs = []
    for sample in dataset:
        payload = {
            "document_id": document_id,
            "query": sample["question"],
            "source_filter": sample.get("source_filter"),
        }
        resp = requests.post(f"{api}/query", json=payload, timeout=180)
        resp.raise_for_status()
        answer_payload = resp.json()

        citations = answer_payload.get("citations", [])
        retrieved_sources = []
        for c in citations:
            snippet = c.get("text_snippet", "")
            if snippet.startswith("[") and "]" in snippet:
                source = snippet.split("]", 1)[0].strip("[]")
                retrieved_sources.append(source.split(" p.")[0])

        outputs.append({
            "question": sample["question"],
            "ground_truth_answer": sample.get("ground_truth_answer", ""),
            "predicted_answer": answer_payload.get("answer", ""),
            "ground_truth_sources": sample.get("ground_truth_sources", []),
            "retrieved_sources": list(dict.fromkeys(retrieved_sources)),
            "context": "\n".join([c.get("text_snippet", "") for c in citations]),
        })
    return outputs


def build_plots(metrics_path: Path, judge_path: Path | None, outdir: Path):
    from backend.evaluation.plot_benchmark import main as _  # noqa: F401
    import subprocess

    cmd = [
        "python",
        "backend/evaluation/plot_benchmark.py",
        "--metrics",
        str(metrics_path),
        "--outdir",
        str(outdir),
    ]
    if judge_path and judge_path.exists():
        cmd.extend(["--judge", str(judge_path)])
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000/api")
    parser.add_argument("--dataset", default="backend/evaluation/capstone_eval_dataset.json")
    parser.add_argument("--files", nargs="+", required=True, help="Paths of files to upload for workspace")
    parser.add_argument("--outdir", default="backend/evaluation/results")
    parser.add_argument("--run-judge", action="store_true")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print("Uploading workspace files...")
    doc_id = upload_workspace(args.api, args.files)
    print(f"Workspace document_id: {doc_id}")

    predictions = run_queries(args.api, doc_id, dataset)
    pred_path = outdir / "predictions.json"
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    metrics_report = evaluate_quality(predictions)
    metrics_path = outdir / "metrics_report.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_report, f, indent=2)

    judge_path = None
    if args.run_judge:
        judge_report = evaluate_judge(predictions)
        judge_path = outdir / "judge_report.json"
        with open(judge_path, "w", encoding="utf-8") as f:
            json.dump(judge_report, f, indent=2)

    build_plots(metrics_path, judge_path, outdir / "plots")

    print("\nEvaluation completed.")
    print(f"Predictions: {pred_path}")
    print(f"Metrics: {metrics_path}")
    if judge_path:
        print(f"Judge metrics: {judge_path}")
    print(f"Plots: {outdir / 'plots'}")


if __name__ == "__main__":
    main()
