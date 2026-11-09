import unittest

from app.algorithms.jaccard import build_jaccard_graph, jaccard_similarity
from app.algorithms.pagerank import compute_pagerank


class GraphAlgorithmsTests(unittest.TestCase):
    def test_jaccard_un_mot_en_commun(self):
        score = jaccard_similarity({"roi", "reine"}, {"reine", "château"})
        self.assertAlmostEqual(score, 1 / 3)

    def test_jaccard_sans_mot_en_commun(self):
        score = jaccard_similarity({"roi"}, {"château"})
        self.assertEqual(score, 0.0)

    def test_graphe_jaccard(self):
        books = {
            1: {"roi"},
            2: {"roi", "reine"},
            3: {"reine", "château", "jardin"},
        }

        graph = build_jaccard_graph(books, threshold=0.25)

        self.assertEqual(graph, {
            1: {2: 0.5},
            2: {1: 0.5, 3: 0.25},
            3: {2: 0.25},
        })

    def test_pagerank_pondere(self):
        graph = {
            1: {2: 0.5},
            2: {1: 0.5, 3: 0.25},
            3: {2: 0.25},
        }

        scores = compute_pagerank(graph, damping=0.5)

        self.assertAlmostEqual(scores[1], 17 / 54)
        self.assertAlmostEqual(scores[2], 4 / 9)
        self.assertAlmostEqual(scores[3], 13 / 54)
        self.assertAlmostEqual(sum(scores.values()), 1.0)