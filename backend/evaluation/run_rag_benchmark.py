"""Run end-to-end benchmark by querying running DocQuery API.

Usage:
  python backend/evaluation/run_rag_benchmark.py \
    --dataset backend/evaluation/benchmark_dataset_template.json \
    --api http://127.0.0.1:8000/api \
    --out backend/evaluation/predictions.json
"""

import argparse
import json
from urllib import request


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000/api")
    parser.add_argument("--out", default="backend/evaluation/predictions.json")
    args = parser.parse_args()

    with open(args.dataset, "r", encoding="utf-8") as f:
        samples = json.load(f)

    outputs = []
    for sample in samples:
        doc_id = sample.get("document_id")
        if not doc_id:
            raise ValueError("Each sample must include document_id")

        response = post_json(
            f"{args.api}/query",
            {
                "document_id": doc_id,
                "query": sample["question"],
                "source_filter": sample.get("source_filter"),
            },
        )

        outputs.append({
            "question": sample["question"],
            "ground_truth_answer": sample.get("ground_truth_answer", ""),
            "predicted_answer": response.get("answer", ""),
            "ground_truth_sources": sample.get("ground_truth_sources", []),
            "retrieved_sources": [
                (citation.get("text_snippet", "").split("]", 1)[0].replace("[", "").replace(" p.", ":"))
                for citation in response.get("citations", [])
            ],
            "context": "\n".join(c.get("text_snippet", "") for c in response.get("citations", [])),
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)

    print(f"Saved predictions to {args.out}")


if __name__ == "__main__":
    main()
