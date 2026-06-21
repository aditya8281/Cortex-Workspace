"""Search result clustering — group results by document."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.services.hybrid_retrieval import RetrievalResult


@dataclass
class ResultCluster:
    document_path: str
    results: list[RetrievalResult] = field(default_factory=list)
    best_score: float = 0.0
    total_score: float = 0.0
    result_count: int = 0


class SearchClusterer:
    """Group search results by document for better UX."""

    def cluster(self, results: list[RetrievalResult]) -> list[ResultCluster]:
        groups: dict[str, ResultCluster] = {}

        for result in results:
            key = result.file_path or f"doc_{result.document_id}" or "unknown"
            if key not in groups:
                groups[key] = ResultCluster(document_path=key)
            cluster = groups[key]
            cluster.results.append(result)
            cluster.best_score = max(cluster.best_score, result.score)
            cluster.total_score += result.score
            cluster.result_count += 1

        sorted_clusters = sorted(groups.values(), key=lambda c: c.best_score, reverse=True)
        return sorted_clusters

    def get_top_per_document(self, results: list[RetrievalResult], max_per_doc: int = 3) -> list[RetrievalResult]:
        clusters = self.cluster(results)
        top_results = []
        for cluster in clusters:
            sorted_results = sorted(cluster.results, key=lambda r: r.score, reverse=True)
            top_results.extend(sorted_results[:max_per_doc])
        return top_results
