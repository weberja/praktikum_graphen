from pathlib import Path

import networkx as nx
from newick import load

from digraph import DiGraph
from helper_functions.graphml import GraphML


def left_siblings(G, node):
    parent = _parent(G, node)
    if not parent:
        return None
    for v in children(G, parent):
        if G.nodes[v]['order'] == G.nodes[node]['order'] - 1:
            return v
    return None


def leftmost_sibling(G, node):
    parent = _parent(G, node)
    if not parent:
        return None
    left_sibling = [v for v in children(G, parent) if G.nodes[v]['order'] < G.nodes[node]['order']]
    sorted_siblings = sorted(left_sibling, key=lambda n: G.nodes[n]['order'])
    if not sorted_siblings:
        return None
    else:
        return sorted_siblings[0]


def children(G, node):
    return list(G.successors(node))


def leftmost_child(G, node):
    ch = children(G, node)
    if not ch:
        return None
    return sorted(ch, key=lambda x: G.nodes[x]['order'])[0]


def rightmost_child(G, node):
    ch = children(G, node)
    if not ch:
        return None
    return sorted(ch, key=lambda x: G.nodes[x]['order'])[-1]


def _parent(G, node):
    result = list(G.predecessors(node))
    if result:
        return result[0]
    return None

def load_file(path, key=None):
    _path = Path(path)

    root = None

    print(f"Loading file {_path.stem}...")
    if _path.suffix == '.nh':
        return load_nh_file(path)
    elif _path.suffix == '.graphml':
        return load_graphml_file(path, key)
    elif _path.suffix == '.dat':
        return nx.readwrite.read_gpickle(path)
    else:
        raise NotImplementedError('Format wird nicht unterstützt')


def load_nh_file(file_path):
    G = DiGraph()
    with open(file_path, mode='r') as f:
        # G = nx.DiGraph()
        nh = load(f)

        noname_number = 0

        if not nh[0].name:
            nh[0].name = f'#{noname_number}'
            noname_number += 1

        G.add_node(nh[0].name)

        parent_nodes = nh

        while True:
            new_nodes = []
            child_order = 0
            for parent in parent_nodes:
                for child in parent.descendants:

                    if not child.name:
                        child.name = f'#{noname_number}'
                        noname_number += 1

                    G.add_node(child.name, order=child_order)
                    G.add_edge(parent.name, child.name)
                    child_order += 1

                    new_nodes.append(child)

            if not new_nodes:
                break
            parent_nodes = new_nodes
    return G


def load_graphml_file(path, key):
    return GraphML(path).to_graph(key)
