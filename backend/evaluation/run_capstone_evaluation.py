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
import sys
from typing import List

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.evaluation.rag_quality_metrics import evaluate as evaluate_quality
from backend.evaluation.rag_evaluator import evaluate as evaluate_judge


def _validate_dataset_sources(dataset: List[dict], file_paths: List[str], allow_missing_sources: bool = False) -> None:
    uploaded_names = {Path(path).name for path in file_paths}
    referenced = set()

    for sample in dataset:
        source_filter = (sample.get("source_filter") or "").strip()
        if source_filter:
            referenced.add(source_filter)
        for source_name in sample.get("ground_truth_sources", []):
            if source_name:
                referenced.add(source_name.strip())

    missing = sorted(name for name in referenced if name not in uploaded_names)
    if missing and not allow_missing_sources:
        missing_preview = "\n".join(f"  - {name}" for name in missing[:20])
        raise ValueError(
            "Dataset references sources that were not uploaded. "
            "Upload all referenced files or pass --allow-missing-sources.\n"
            f"Missing source files:\n{missing_preview}"
        )


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
            "source_filter": sample.get("source_filter"),
            "query_latency_ms": answer_payload.get("latency_ms"),
        })
    return outputs


def build_plots(metrics_path: Path, judge_path: Path | None, outdir: Path):
    import subprocess
    from backend.evaluation.plot_benchmark import main as _  # noqa: F401

    cmd = [
        sys.executable,
        str(REPO_ROOT / "backend/evaluation/plot_benchmark.py"),
        "--metrics",
        str(metrics_path),
        "--outdir",
        str(outdir),
    ]
    if judge_path and judge_path.exists():
        cmd.extend(["--judge", str(judge_path)])
    subprocess.run(cmd, check=True)


def main():
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000/api")
    parser.add_argument("--dataset", default=str(base_dir / "capstone_eval_dataset.json"))
    parser.add_argument("--files", nargs="+", required=True, help="Paths of files to upload for workspace")
    parser.add_argument("--outdir", default=str(base_dir / "results"))
    parser.add_argument("--run-judge", action="store_true")
    parser.add_argument(
        "--allow-missing-sources",
        action="store_true",
        help="Allow evaluation to run even when dataset references files not uploaded for this workspace.",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    _validate_dataset_sources(
        dataset=dataset,
        file_paths=args.files,
        allow_missing_sources=args.allow_missing_sources,
    )

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

    judge_path = outdir / "judge_report.json"
    if args.run_judge:
        judge_report = evaluate_judge(predictions)
        with open(judge_path, "w", encoding="utf-8") as f:
            json.dump(judge_report, f, indent=2)
    elif judge_path.exists():
        judge_path.unlink()
        judge_path = None

    build_plots(metrics_path, judge_path, outdir / "plots")

    print("\nEvaluation completed.")
    print(f"Predictions: {pred_path}")
    print(f"Metrics: {metrics_path}")
    if judge_path:
        print(f"Judge metrics: {judge_path}")
    print(f"Plots: {outdir / 'plots'}")


if __name__ == "__main__":
    main()
