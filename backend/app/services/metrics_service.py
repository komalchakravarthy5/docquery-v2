"""Runtime metrics service for query performance and retrieval quality."""

from collections import defaultdict, deque
from statistics import mean
from typing import Deque, Dict, List


class MetricsService:
    """Tracks lightweight in-memory metrics per document workspace."""

    def __init__(self, max_points: int = 100):
        self.max_points = max_points
        self._query_metrics: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=self.max_points))

    def record_query(self, document_id: str, payload: dict):
        self._query_metrics[document_id].append(payload)

    def get_document_metrics(self, document_id: str) -> dict:
        points = list(self._query_metrics.get(document_id, []))
        if not points:
            return {
                "document_id": document_id,
                "total_queries": 0,
                "avg_latency_ms": 0.0,
                "avg_relevance_score": 0.0,
                "avg_citations": 0.0,
                "query_success_rate": 0.0,
                "trend": [],
            }

        return {
            "document_id": document_id,
            "total_queries": len(points),
            "avg_latency_ms": round(mean(p["latency_ms"] for p in points), 2),
            "avg_relevance_score": round(mean(p["avg_relevance_score"] for p in points), 3),
            "avg_citations": round(mean(p["num_citations"] for p in points), 2),
            "query_success_rate": round(mean(1.0 if p["answer_found"] else 0.0 for p in points), 3),
            "trend": points[-20:],
        }


metrics_service = MetricsService()

