import os
import random
from typing import List, Tuple

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


def generate_synthetic_facebook(n_nodes: int = 4039, target_edges: int = 88234, seed: int = 42) -> List[Tuple[int, int]]:
    rng = random.Random(seed)
    if HAS_NETWORKX:
        graph = nx.barabasi_albert_graph(n_nodes, 10, seed=seed)
        edges = [(min(u, v), max(u, v)) for u, v in graph.edges()]
        if len(edges) > target_edges:
            edges = rng.sample(edges, target_edges)
        return edges
    else:
        edges = []
        degrees = [1] * n_nodes
        total_edges = 0
        while total_edges < target_edges:
            src = rng.randint(0, n_nodes - 1)
            tgt = rng.choices(range(n_nodes), weights=degrees, k=1)[0]
            if src != tgt:
                edge = (min(src, tgt), max(src, tgt))
                if edge not in edges:
                    edges.append(edge)
                    degrees[src] += 1
                    degrees[tgt] += 1
                    total_edges += 1
        return edges


def try_download_snap(data_dir: str = "data", target_rels: int = 88234, seed: int = 42) -> List[Tuple[int, int]]:
    import requests
    import tarfile
    import io
    import glob

    candidates = [
        ("https://snap.stanford.edu/data/facebook.tar.gz", "facebook"),
        ("https://snap.stanford.edu/data/ego-Facebook.tar.gz", "ego-Facebook"),
    ]

    for url, name in candidates:
        try:
            dest = os.path.join(data_dir, f"{name}.tar.gz")
            if not os.path.exists(dest):
                print(f"Trying {url}...")
                r = requests.get(url, stream=True, timeout=120)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    continue
            extract_dir = os.path.join(data_dir, name)
            if not os.path.exists(extract_dir):
                with tarfile.open(dest, "r:gz") as tar:
                    tar.extractall(data_dir)
            edges_paths = glob.glob(os.path.join(extract_dir, "*.edges"))
            if edges_paths:
                edges = []
                for ep in edges_paths:
                    edges.extend(load_edges(ep, sample_size=None, seed=seed))
                rng = random.Random(seed)
                if len(edges) > target_rels:
                    edges = rng.sample(edges, target_rels)
                return edges
        except Exception as e:
            print(f"Download failed for {url}: {e}")

    return []


def load_edges(edges_path: str, sample_size: int = None, seed: int = 42) -> List[Tuple[int, int]]:
    edges = []
    with open(edges_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                edges.append((int(parts[0]), int(parts[1])))
    if sample_size and len(edges) > sample_size:
        rng = random.Random(seed)
        edges = rng.sample(edges, sample_size)
    return edges


def get_dataset(target_rels: int = 88234, seed: int = 42, data_dir: str = "data") -> List[Tuple[int, int]]:
    os.makedirs(data_dir, exist_ok=True)
    edges = try_download_snap(data_dir, target_rels, seed)
    if not edges:
        print("SNAP download unavailable. Generating synthetic social network...")
        edges = generate_synthetic_facebook(target_edges=target_rels, seed=seed)
    print(f"Loaded {len(edges)} relationships")
    return edges
