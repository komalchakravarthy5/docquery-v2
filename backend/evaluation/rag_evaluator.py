"""Advanced RAG evaluator with LLM-as-judge faithfulness/relevance."""

import argparse
import json
from statistics import mean
from app.services.gemini_service import gemini_service


def judge_score(question: str, answer: str, context: str, rubric: str) -> float:
    prompt = f"""Score from 1 to 5.
Rubric: {rubric}
Question: {question}
Answer: {answer}
Context: {context}
Return ONLY the numeric score.
"""
    try:
        raw = gemini_service.generate_answer(prompt, [{"text": context, "page_number": 1, "source_file": "eval"}], max_context_length=7000)
        value = float(''.join(ch for ch in raw if ch.isdigit() or ch == '.'))
        return max(1.0, min(5.0, value))
    except Exception:
        return 1.0


def evaluate(samples: list[dict]) -> dict:
    faithfulness_scores = []
    relevance_scores = []

    for s in samples:
        question = s.get("question", "")
        answer = s.get("predicted_answer", "")
        context = s.get("context", "")
        faithfulness_scores.append(judge_score(
            question,
            answer,
            context,
            "How well answer is fully supported by provided context without hallucination",
        ))
        relevance_scores.append(judge_score(
            question,
            answer,
            context,
            "How directly and completely answer addresses the question",
        ))

    return {
        "num_samples": len(samples),
        "faithfulness_mean_1to5": round(mean(faithfulness_scores), 3) if faithfulness_scores else 0.0,
        "answer_relevance_mean_1to5": round(mean(relevance_scores), 3) if relevance_scores else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="rag_judge_report.json")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        samples = json.load(f)

    report = evaluate(samples)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
