from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

import algos.walker as wk
from helper_functions import graph_helper_functions as gh


def run(path, figsize=(20, 20), key=None):
    G = gh.load_file(path, key=key)
    G.greedy_cycle_removal()
    G.longest_path_layering()

    pos = wk.tree_layout(G.to_tree())

    for u in G.nodes:
        x, y = pos[u]
        pos[u] = (x, -G.nodes[u]['level'])

    print("Drawing...")
    plt.figure(figsize=figsize)
    nx.draw(G, pos=pos, with_labels=True)

    print("Writing to file...")
    plt.savefig(f'results/{Path(path).stem}.png')
