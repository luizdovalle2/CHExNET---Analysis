from __future__ import annotations

from itertools import combinations
from typing import Any
import networkx as nx
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from dateutil.relativedelta import relativedelta
import pandas as pd


def create_aggregated_network(adjacency_dict: dict | list[dict]) -> np.ndarray:
    """Return unique node-id pairs (edges) induced by each time-slice's incident nodes."""
    adjacent_values: list[list[int]] = []
    for _, curr in adjacency_dict.items():
        pos_to_id = {pos: node_id for node_id, pos in curr["ids_pos_mat"].items()}
        A = curr["matrix"].toarray()
        rows, cols = np.where(A == 1)
        idx = np.unique(np.concatenate([rows, cols]))
        adjacent_values.append([pos_to_id[i] for i in idx])

    pairs: list[tuple[int, int]] = []
    for group in adjacent_values:
        pairs.extend(combinations(group, 2)) 

    return np.array(list(set(pairs)))


def get_giant_component(G):
    if len(G.nodes) == 0:
        return []
    return G.subgraph(sorted(nx.connected_components(G), key=len, reverse=True)[0])


def edge_density(G):
    # Compute edge density for an undirected graph
    n = G.number_of_nodes()
    if n <= 1:
        return np.nan
    m = G.number_of_edges()
    return 2 * m / (n * (n - 1))


def get_graph_metrics(Gs):
    """
    Gs: iterable of (name, G) pairs.

    Returns a DataFrame with the SAME metric labels you used before
    (e.g., 'LCC average degree ', 'LCC degree assortavity', ...),
    but fixes the definitions so component-based metrics are computed
    on the full graph (not on the LCC).
    """
    rows = []

    # keep original headers exactly (including typos/trailing space)
    metrics = [
        ("Size (nodes)", lambda G, H: G.number_of_nodes()),
        ("Number of components", lambda G, H: nx.number_connected_components(G) if G.number_of_nodes() > 0 else np.nan),
        ("LCC size", lambda G, H: H.number_of_nodes()),
        ("LCC diameter", lambda G, H: int(nx.diameter(H)) if H.number_of_nodes() > 1 else np.nan),
        ("LCC edge density", lambda G, H: edge_density(H)),
        ("LCC average path length", lambda G, H: nx.average_shortest_path_length(H) if H.number_of_nodes() > 1 else np.nan),
        ("LCC average degree ", lambda G, H: np.mean([d for _, d in H.degree()]) if H.number_of_nodes() > 0 else np.nan),
        ("LCC degree assortavity", lambda G, H: nx.degree_assortativity_coefficient(H) if H.number_of_edges() > 0 else np.nan),
        ("LCC clustering coefficient", lambda G, H: nx.average_clustering(H) if H.number_of_nodes() > 0 else np.nan),
    ]

    # ensure we can iterate twice and preserve column order
    Gs_list = list(Gs)
    names = [n for n, _ in Gs_list]

    for metric_name, f in tqdm(metrics, desc="Metrics"):
        values = []
        for _, G in Gs_list:
            H = get_giant_component(G)
            values.append(f(G, H))
        rows.append([metric_name, *values])

    return pd.DataFrame.from_records(rows, columns=["Metric", *names])


def parallel_series(graph_list, func, desc="Metric", max_workers=None):
    # Apply a function to a list of graphs in parallel (process-based)
    # Returns results in original order

    out = np.empty(len(graph_list), dtype=float)

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(func, G): i for i, G in enumerate(graph_list)}

        # Collect results as they complete
        for fut in tqdm(as_completed(futures), total=len(futures), desc=desc):
            i = futures[fut]
            out[i] = fut.result()

    return out


def style_ax(ax):
    # Apply consistent styling to matplotlib axis
    ax.spines[['top', 'right']].set_visible(False)  # Remove top/right borders
    ax.legend(frameon=False)                        # Legend without frame
    ax.set_xlabel("Date")                           # Standard x-label


def build_temporal_graph(dicts, threshold_date, years_window=50):
    # Construct an undirected temporal graph within a rolling time window

    G = nx.Graph()

    # Ensure input is iterable
    if isinstance(dicts, dict):
        dicts = [dicts]

    for d in dicts:
        for time in d:
            curr = d[time]

            # Filter by temporal window
            if not ((threshold_date - relativedelta(years=years_window))
                    <= curr['time'] < threshold_date):
                continue

            # Map matrix positions to node IDs
            pos_to_id = {v: k for k, v in curr['ids_pos_mat'].items()}
            A = curr['matrix'].toarray()

            # Identify active ties (binary adjacency)
            rows, cols = np.where(A == 1)

            # Nodes involved in at least one tie
            indices = np.unique(np.concatenate([rows, cols]))

            # Create clique among active nodes
            adj = list(combinations([pos_to_id[i] for i in indices], 2))

            for s, t in adj:
                if not G.has_edge(s, t):
                    G.add_edge(s, t, time=curr['time'])

    return G