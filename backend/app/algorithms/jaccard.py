"""Similarite de Jaccard et construction du graphe de similarite."""

import heapq
from itertools import combinations


def jaccard_similarity(first: set, second: set) -> float:
    """|A ∩ B| / |A ∪ B| ; 0 si les deux ensembles sont vides."""
    common_count = len(first & second)
    union_count = len(first) + len(second) - common_count
    return common_count / union_count if union_count else 0.0


def build_jaccard_graph(
    vocabularies: dict[int, set],
    *,
    threshold: float,
    min_neighbors: int = 0,
) -> dict[int, dict[int, float]]:
    """Graphe non oriente pondere par la similarite de Jaccard.

    Deux livres sont relies si leur similarite atteint `threshold`.
    Avec `min_neighbors` > 0, chaque livre garde en plus ses k plus
    proches voisins : aucun livre ne reste sans suggestion, meme si
    aucun autre ne depasse le seuil.

    Cout : O(n²) comparaisons d'ensembles (n = nombre de livres).
    """
    graph: dict[int, dict[int, float]] = {book_id: {} for book_id in vocabularies}
    # Tas des k meilleurs voisins de chaque livre : (similarite, voisin).
    nearest: dict[int, list] = {book_id: [] for book_id in vocabularies}

    for first_id, second_id in combinations(vocabularies, 2):
        similarity = jaccard_similarity(
            vocabularies[first_id], vocabularies[second_id]
        )
        if similarity <= 0:
            continue

        if similarity >= threshold:
            graph[first_id][second_id] = similarity
            graph[second_id][first_id] = similarity

        if min_neighbors:
            for source, target in ((first_id, second_id), (second_id, first_id)):
                heap = nearest[source]
                if len(heap) < min_neighbors:
                    heapq.heappush(heap, (similarity, target))
                elif similarity > heap[0][0]:
                    heapq.heapreplace(heap, (similarity, target))

    for source, heap in nearest.items():
        for similarity, target in heap:
            graph[source][target] = similarity
            graph[target][source] = similarity

    return graph
