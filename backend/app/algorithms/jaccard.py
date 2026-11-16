from itertools import combinations

def jaccard_similarity(first: set[str], second: set[str]) -> float:
    common_count = len(first & second)
    union_count = len(first) + len(second) - common_count
    return common_count / union_count if union_count else 0.0

def build_jaccard_graph(
    vocabularies: dict[int, set[str]], *, threshold: float
) -> dict[int, dict[int, float]]:
    graph: dict[int, dict[int, float]] = {
        book_id: {} for book_id in vocabularies
    }

    for first_id, second_id in combinations(vocabularies, 2):
        similarity = jaccard_similarity(
            vocabularies[first_id], vocabularies[second_id]
        )

        if similarity > 0 and similarity >= threshold:
            graph[first_id][second_id] = similarity
            graph[second_id][first_id] = similarity

    return graph