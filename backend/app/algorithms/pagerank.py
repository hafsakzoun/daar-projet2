def compute_pagerank(
    graph: dict[int, dict[int, float]],
    *,
    damping: float = 0.85,
    tolerance: float = 1e-10,
    max_iterations: int = 200,
) -> dict[int, float]:
    size = len(graph)
    if size == 0:
        return {}

    scores = {book_id: 1 / size for book_id in graph}
    total_weights = {
        book_id: sum(neighbors.values())
        for book_id, neighbors in graph.items()
    }

    for _ in range(max_iterations):
        isolated_score = sum(
            scores[book_id] for book_id in graph if total_weights[book_id] == 0
        )
        base_score = (1 - damping + damping * isolated_score) / size
        new_scores = {book_id: base_score for book_id in graph}

        for book_id, neighbors in graph.items():
            for neighbor_id, weight in neighbors.items():
                share = weight / total_weights[book_id]
                new_scores[neighbor_id] += damping * scores[book_id] * share

        change = sum(abs(new_scores[book_id] - scores[book_id]) for book_id in graph)
        if change <= tolerance:
            return new_scores

        scores = new_scores

    raise RuntimeError("PageRank n’a pas convergé.")