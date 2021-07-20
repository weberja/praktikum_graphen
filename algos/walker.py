from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from helper_functions import graph_helper_functions as gh

SUBTREE_SPACING = 1
NODE_SPACING = 1


def run(path, figsize=(20, 20), key=None):
    G, root = gh.load_file(path, key=key)

    print("Calculate Postions in Tree...")
    pos = tree_layout(G, root)

    print("Drawing...")
    plt.figure(figsize=figsize)
    nx.draw(G, pos=pos, with_labels=True)

    print("Writing to file...")
    plt.savefig(f'results/{Path(path).stem}.png')


def tree_layout(G, root=None):
    for v in G.nodes:
        G.nodes[v]['mod'] = 0
        G.nodes[v]['change'] = 0
        G.nodes[v]['shift'] = 0
        G.nodes[v]['threads'] = None
        G.nodes[v]['ancestor'] = v
    if not root:
        root = [n for n, d in G.in_degree() if d == 0][0]
    print('Root: ' + root)
    first_walk(G, root)
    return secound_walk(G, root, -G.nodes[root]['prelim'], {})


def first_walk(G, v):
    child_nodes = sorted(gh.children(G, v), key=lambda n: G.nodes[n]['order'])
    if not child_nodes:
        if w := gh.left_siblings(G, v):
            G.nodes[v]['prelim'] = G.nodes[w]['prelim'] + NODE_SPACING
        else:
            G.nodes[v]['prelim'] = 0
    else:
        default_ancestor = child_nodes[0]
        for w in child_nodes:
            # print(f'--- current node ---\n--- {w} ---')
            first_walk(G, w)
            default_ancestor = apporation(G, w, default_ancestor)
        exec_shift(G, v)
        midpoint = 0.5 * (G.nodes[child_nodes[0]]['prelim'] + G.nodes[child_nodes[-1]]['prelim'])
        if w := gh.left_siblings(G, v):
            try:
                G.nodes[v]['prelim'] = G.nodes[w]['prelim'] + NODE_SPACING
            except:
                print(w, v)

            G.nodes[v]['mod'] = G.nodes[v]['prelim'] - midpoint
        else:
            G.nodes[v]['prelim'] = midpoint


def apporation(G, v, default_ancestor):
    left_sibling = gh.left_siblings(G, v)
    if left_sibling:
        vip = vop = v
        vin = left_sibling
        von = gh.leftmost_sibling(G, vip)
        sip = G.nodes[vip]['mod']
        sop = G.nodes[vop]['mod']
        sin = G.nodes[vin]['mod']
        son = G.nodes[von]['mod']

        nr = next_right(G, vin)
        nl = next_left(G, vip)

        while nr is not None and nl is not None:
            vin = nr
            vip = nl
            von = next_left(G, von)
            vop = next_right(G, vop)

            G.nodes[vop]['ancestor'] = v

            shift = (G.nodes[vin]['prelim'] + sin) - (G.nodes[vip]['prelim'] + sip) + SUBTREE_SPACING

            if shift > 0:
                move_subtree(G, ancestor(G, vin, v, default_ancestor), v, shift)
                sip += shift
                sop += shift

            sin += G.nodes[vin]['mod']
            sip += G.nodes[vip]['mod']
            son += G.nodes[von]['mod']
            sop += G.nodes[vop]['mod']

            nr = next_right(G, vin)
            nl = next_left(G, vip)

        if nr and not next_right(G, vop):
            G.nodes[vop]['threads'] = nr
            G.nodes[vop]['mod'] += sin - sop
        if nl and not next_left(G, von):
            G.nodes[von]['threads'] = nl
            G.nodes[von]['mod'] += sin - sop
            default_ancestor = v
    return default_ancestor


def next_left(G, v):
    child = gh.leftmost_child(G, v)
    if child:
        return child
    else:
        return G.nodes[v]['threads']


def next_right(G, v):
    child = gh.rightmost_child(G, v)
    if child:
        return child
    else:
        return G.nodes[v]['threads']


def move_subtree(G, wm, wp, shift):
    subtrees = G.nodes[wp]['order'] - G.nodes[wm]['order']
    G.nodes[wp]['change'] -= shift / subtrees
    G.nodes[wp]['shift'] += shift

    G.nodes[wm]['change'] += shift / subtrees
    G.nodes[wp]['prelim'] += shift

    G.nodes[wp]['mod'] += shift


def exec_shift(G, node):
    shift = 0
    change = 0

    for child in sorted(gh.children(G, node), key=lambda n: G.nodes[n]['order'], reverse=True):
        G.nodes[child]['prelim'] += shift
        G.nodes[child]['mod'] += shift
        change += G.nodes[child]['change']
        shift += G.nodes[child]['shift'] + change


def ancestor(G, v_i, node, default_ancestor):
    ancest = G.nodes[v_i]['ancestor']
    if gh._parent(G, ancest) == gh._parent(G, node):
        return ancest
    else:
        return default_ancestor


def secound_walk(G, node, m, pos, level=0):
    x = G.nodes[node]['prelim'] + m
    y = level
    pos[node] = (x, y)

    childs = sorted(gh.children(G, node), key=lambda n: G.nodes[n]['order'], reverse=False)

    if not childs:
        return pos
    else:
        for child in childs:
            pos = secound_walk(G, child, m + G.nodes[node]['mod'], pos, level - 10)
    return pos