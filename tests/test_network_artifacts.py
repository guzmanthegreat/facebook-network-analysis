import pickle
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class NetworkArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = pd.read_csv(PROJECT_ROOT / "processed_nodes.csv")
        with open(PROJECT_ROOT / "graph.pkl", "rb") as file:
            cls.graph = pickle.load(file)
        with open(PROJECT_ROOT / "summary_stats.pkl", "rb") as file:
            cls.summary = pickle.load(file)

    def test_processed_nodes_match_graph(self):
        self.assertEqual(len(self.nodes), self.graph.number_of_nodes())
        self.assertEqual(set(self.nodes["node"]), set(self.graph.nodes))

    def test_required_metrics_are_present(self):
        required_columns = {
            "node",
            "name",
            "degree",
            "degree_centrality",
            "betweenness",
            "clustering",
            "community",
        }
        self.assertTrue(required_columns.issubset(self.nodes.columns))

    def test_summary_statistics_match_graph(self):
        self.assertEqual(self.summary["nodes"], self.graph.number_of_nodes())
        self.assertEqual(self.summary["edges"], self.graph.number_of_edges())
        self.assertEqual(self.summary["components"], 1)
        self.assertGreater(self.summary["communities"], 0)


if __name__ == "__main__":
    unittest.main()
