"""Generate presentation-ready evaluation graphs from JSON reports.

Usage:
  python backend/evaluation/plot_benchmark.py --metrics metrics_report.json --judge judge_report.json --outdir backend/evaluation/plots
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True, help="Output of rag_quality_metrics.py")
    parser.add_argument("--judge", required=False, help="Output of rag_evaluator.py")
    parser.add_argument("--outdir", default="backend/evaluation/plots")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Please install matplotlib: pip install matplotlib") from exc

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.metrics, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    labels = ["Answer F1", "Retrieval P", "Retrieval R", "Retrieval F1"]
    values = [
        metrics.get("answer_f1", 0),
        metrics.get("retrieval_precision", 0),
        metrics.get("retrieval_recall", 0),
        metrics.get("retrieval_f1", 0),
    ]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, values, color=["#9D5DFF", "#C1FF72", "#C1FF72", "#9D5DFF"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("DocQuery Evaluation Metrics")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.2f}", ha="center")
    fig.tight_layout()
    fig.savefig(outdir / "retrieval_answer_metrics.png", dpi=200)
    plt.close(fig)

    if args.judge:
        with open(args.judge, "r", encoding="utf-8") as f:
            judge = json.load(f)

        labels = ["Faithfulness", "Relevance"]
        values = [
            judge.get("faithfulness_mean_1to5", 0),
            judge.get("answer_relevance_mean_1to5", 0),
        ]
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(labels, values, color=["#9D5DFF", "#C1FF72"])
        ax.set_ylim(0, 5)
        ax.set_ylabel("Score (1-5)")
        ax.set_title("LLM-as-Judge Metrics")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.08, f"{value:.2f}", ha="center")
        fig.tight_layout()
        fig.savefig(outdir / "judge_metrics.png", dpi=200)
        plt.close(fig)

    print(f"Saved plots to: {outdir}")


if __name__ == "__main__":
    main()
