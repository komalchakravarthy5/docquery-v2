"""LLM-as-judge evaluator for faithfulness/relevance.

This module intentionally avoids defaulting failed judge calls to 1.0,
because that can silently hide evaluation issues.
"""

from __future__ import annotations

import argparse
import json
import re
from statistics import mean
from typing import Optional

import google.generativeai as genai

from app.config import get_settings

settings = get_settings()
_SCORE_PATTERN = re.compile(r"\b([1-5](?:\.\d+)?)\b")


def _build_model():
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is missing; cannot run LLM-as-judge evaluation.")
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


def _extract_score(raw: str) -> Optional[float]:
    match = _SCORE_PATTERN.search(raw or "")
    if not match:
        return None
    score = float(match.group(1))
    if score < 1 or score > 5:
        return None
    return score


def judge_score(model, question: str, answer: str, context: str, rubric: str) -> Optional[float]:
    prompt = f"""You are grading an answer for a RAG system.
Return only a numeric score between 1 and 5.

Rubric: {rubric}
Question: {question}
Answer: {answer}
Context: {context}
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=8,
            ),
        )
        return _extract_score((response.text or "").strip())
    except Exception:
        return None


def evaluate(samples: list[dict]) -> dict:
    model = _build_model()
    faithfulness_scores = []
    relevance_scores = []
    failed_faithfulness = 0
    failed_relevance = 0

    for s in samples:
        question = s.get("question", "")
        answer = s.get("predicted_answer", "")
        context = s.get("context", "")

        faith = judge_score(
            model,
            question,
            answer,
            context,
            "How fully is the answer supported by context only (no hallucination)?",
        )
        rel = judge_score(
            model,
            question,
            answer,
            context,
            "How directly and completely does the answer address the question?",
        )

        if faith is None:
            failed_faithfulness += 1
        else:
            faithfulness_scores.append(faith)
        if rel is None:
            failed_relevance += 1
        else:
            relevance_scores.append(rel)

    return {
        "num_samples": len(samples),
        "faithfulness_mean_1to5": round(mean(faithfulness_scores), 3) if faithfulness_scores else 0.0,
        "answer_relevance_mean_1to5": round(mean(relevance_scores), 3) if relevance_scores else 0.0,
        "faithfulness_scored_samples": len(faithfulness_scores),
        "relevance_scored_samples": len(relevance_scores),
        "faithfulness_failed_samples": failed_faithfulness,
        "relevance_failed_samples": failed_relevance,
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
