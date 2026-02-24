"""GNN stub: tries to import PyTorch Geometric, otherwise falls back to networkx heuristics."""

try:
    import torch
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv
    PYG_AVAILABLE = True
except Exception:
    PYG_AVAILABLE = False

import networkx as nx


class RouteGNN:
    def __init__(self):
        if PYG_AVAILABLE:
            self.model = GCNConv(4, 2)
        else:
            self.model = None

    def predict(self, graph):
        """Return simple scores per edge as prediction stub."""
        if PYG_AVAILABLE:
            # Minimal placeholder: return zeros
            return [0.0 for _ in range(graph.num_edges)]
        else:
            # NetworkX heuristic: return inverse distance as score
            scores = []
            for u, v, d in graph.edges(data=True):
                dist = d.get('distance', 1.0)
                scores.append(1.0 / (dist + 1e-6))
            return scores
