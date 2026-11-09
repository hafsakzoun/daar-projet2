from itertools import combinations

def jaccard_similarity(first: set[str], second: set[str]) -> float:
    common_words = first & second
    all_words = first | second

    if not all_words:
        return 0.0

    return len(common_words) / len(all_words)

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