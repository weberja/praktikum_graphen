from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

import algos.walker as wk
from digraph import DiGraph
from helper_functions import graph_helper_functions as gh


def run(path, figsize=(20, 20), key=None):
    G = gh.load_file(path, key=key)
    print("Cycle removal...")
    G_cycle_removed, root = DiGraph.as_tree(G.greedy_cycle_removal())
    print("Generate layout...")
    pos = wk.tree_layout(G_cycle_removed, root)
    # pos = nx.shell_layout(G_cycle_removed)
    colors = [G[u][v]['color'] for u, v in G.edges()]

    print("Drawing...")
    plt.figure(figsize=figsize)
    colors = [G[u][v]['color'] for u, v in G.edges()]
    nx.draw(G, pos=pos, edge_color=colors, with_labels=True)

    print("Writing to file...")
    plt.savefig(f'results/{Path(path).stem}.png')

    print("Drawing 2...")
    plt.figure(figsize=figsize)
    colors = [G_cycle_removed[u][v]['color'] for u, v in G_cycle_removed.edges()]
    nx.draw(G_cycle_removed, pos=pos, edge_color=colors, with_labels=True)

    print("Writing to file 2...")
    plt.savefig(f'results/{Path(path).stem}_cycle_removed.png')
