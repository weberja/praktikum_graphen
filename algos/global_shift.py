#  Copyright (c) 2021 Jan Westerhoff
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from copy import deepcopy
from enum import Enum
from multiprocessing import Process
from pathlib import Path

import networkx as nx
from matplotlib import pyplot as plt

from digraph import DiGraph, BlockList, Block


class Direction(Enum):
    UP = '-'
    DOWN = '+'


def global_shifting(G: DiGraph, shifting_rounds=20, name='', path=Path.cwd()):
    print()
    inner_step = outer_step = 0
    B = G.get_block_list()
    for _ in range(0, shifting_rounds):
        for A in list(B):
            B = sifting_step(G, B, A)
            print('\r' + f"{name}_{outer_step}_{inner_step}", end='')
            # p = Process(target=_draw_step, args=(G, B), kwargs={'step':f"{outer_step}_{inner_step}",
            # 'name':'INNER', 'figsize':(40,20)}) p.start() _draw_step(G, B, step=f"{outer_step}_{inner_step}",
            # name='INNER')
            inner_step += 1
        p = Process(target=_draw_step, args=(G, B),
                    kwargs={'step': f"{outer_step}", 'name': f'{name}_SHIFTING_ROUNDS', 'figsize': (80, 10),
                            'path': path.joinpath('shifting_rounds')})
        p.start()
        outer_step += 1
        inner_step = 0

    for v in G.nodes:
        G.nodes[v]['pi'] = B.pi(G.block(v))

    return G


def _draw_step(G: DiGraph, B: BlockList, figsize=(20, 20), step="-1", name='DEBUG', path=Path.cwd()):
    path.mkdir(parents=True, exist_ok=True)

    colors = [G[u][v]['color'] for u, v in G.edges()]
    fig = plt.figure(figsize=figsize)

    pos = {}
    for node in G.nodes:
        y = -G.nodes[node]['level']
        x = B.pi(G.block(node))
        pos[node] = (x, y)

    nx.draw(G, pos=pos, edge_color=colors, with_labels=False)

    plt.savefig(path.joinpath(f'{step}_cycle_removed.png'))
    plt.close(fig)


def sort_adjacencies(G: DiGraph, B: BlockList) -> None:
    for block in B:
        # B.move(B[i], i) # PI ist so oder so an die pos geknüpft -> muss nicht geupdatet werden
        block.clear()

    debug_counter = 0

    p = dict()  # defaultdict(lambda: -1)
    for A in B:
        for edge in [(u, v) for u, v in G.in_edges if v == A.upper]:
            u, v = edge
            block_u = B.block_from_id(G.block(u))

            j = len(block_u.n_p)
            block_u.n_p.append(v)
            block_u.i_p.append(-1)

            if B.pi(A.id) < B.pi(block_u.id):
                p[(u, v)] = j
            else:
                block_u.i_p[j] = p[edge]
                A.i_n[p[edge]] = j

            debug_counter += 1

        for edge in [(w, x) for w, x in G.out_edges if w == A.lower]:

            w, x = edge
            block_x = B.block_from_id(G.block(x))

            j = len(block_x.n_n)
            block_x.n_n.append(w)
            block_x.i_n.append(-1)

            if B.pi(A.id) < B.pi(block_x.id):
                p[edge] = j
            else:
                block_x.i_n[j] = p[edge]
                A.i_p[p[edge]] = j

            debug_counter += 1

    # if (res := check_index(G, B)) is not None: # sanitise check
    #     print(res)


def check_index(G: DiGraph, B: BlockList):
    for block in B:
        for node in block.n_p:
            index = block.i_p[block.n_p.index(node)]
            other_block = B.block_from_id(G.block(node))
            other_node = other_block.n_n[index]
            if node == other_node:
                return node, other_node

        for node in block.n_n:
            index = block.i_n[block.n_n.index(node)]
            other_block = B.block_from_id(G.block(node))
            other_node = other_block.n_p[index]
            if node == other_node:
                return node, other_node


def sifting_step(G: DiGraph, B: BlockList, A: Block) -> BlockList:
    B_ = deepcopy(B)
    B_.move(A, 0)
    sort_adjacencies(G, B_)
    A = B_.block_from_id(A.id)

    x = x_best = p_best = 0

    for p in range(1, len(B_)):
        x += sifting_swap(G, A, B_[p], B_)

        if x < x_best:
            x_best = x
            p_best = p

    B_.move(A, p_best)
    return B_


def sifting_swap(G: DiGraph, A: Block, B: Block, B_: BlockList) -> int:
    def uswap(n_a: list[str], n_b: list[str]):

        i = j = c = 0
        s = len(n_b)
        r = len(n_a)
        while i < r and j < s:
            if B_.pi(G.block(n_a[i])) < B_.pi(G.block(n_b[j])):
                c += s - j
                i += 1
            elif B_.pi(G.block(n_a[i])) > B_.pi(G.block(n_b[j])):
                c -= r - i
                j += 1
            else:
                c += s - j - r - i
                i += 1
                j += 1
        return c

    l = set()
    delta = 0

    if G.phi(A.upper) in B.levels:
        l.add((G.phi(A.upper), '-'))
    if G.phi(A.lower) in B.levels:
        l.add((G.phi(A.lower), '+'))
    if G.phi(B.upper) in A.levels:
        l.add((G.phi(B.upper), '-'))
    if G.phi(B.lower) in A.levels:
        l.add((G.phi(B.lower), '+'))

    for level, order in l:
        # _nodes_on_same_level(G, level, A, B)
        if order == '-':
            delta += uswap(A.n_n, B.n_n)
            update_adjacencies(A, B, A.n_n, B.n_n, B_, G, Direction.UP)
        else:
            delta += uswap(A.n_p, B.n_p)
            update_adjacencies(A, B, A.n_p, B.n_p, B_, G, Direction.DOWN)
    B_.swap_pos(A.id, B.id)

    return delta


def swap_adjecenties(block_n_x: list[str], block_i_x: list[int], neighbours_a_i_x: list[int],
                     neighbours_b_i_x: list[int], i: int, j: int):
    index_a = neighbours_a_i_x[i]
    index_b = neighbours_b_i_x[j]

    temp = block_n_x[index_a]
    block_n_x[index_a] = block_n_x[index_b]
    block_n_x[index_b] = temp

    temp = block_i_x[index_a]
    block_i_x[index_a] = block_i_x[index_b]
    block_i_x[index_b] = temp

    neighbours_a_i_x[i] = index_b
    neighbours_b_i_x[j] = index_a


def update_adjacencies(A: Block, B: Block, x, y, B_: BlockList, G: DiGraph, direction: Direction):
    i = j = 0
    while i < len(x) and j < len(y):
        if B_.pi(G.block(x[i])) < B_.pi(G.block(y[j])):
            i += 1
        elif B_.pi(G.block(x[i])) > B_.pi(G.block(y[j])):
            j += 1
        else:
            z = B_.block_from_id(G.block(x[i]))
            if direction == Direction.UP:  # d == '-' ==> -d == '+'
                swap_adjecenties(z.n_p, z.i_p, A.i_n, B.i_n, i, j)
            else:  # d == '+' => -d == '-'
                swap_adjecenties(z.n_n, z.i_n, A.i_p, B.i_p, i, j)

            i += 1
            j += 1


def _level(G: DiGraph, node: str):
    return G.nodes[node]['level']


def _nodes_on_same_level(G: DiGraph, level: int, A: Block, B: Block):
    for a in A.nodes:
        for b in B.nodes:
            if level == _level(G, a) == _level(G, b):
                return a, b
    raise RuntimeError('Blöcke haben keine gemeinsame Ebene!')


# Ablauf:
# - cycle removal
# - layer assignment
# - crossing reduction
# - x-coordinate assignment
# DONE
def run(path, graph_key, figsize):
    file_name = Path(path).stem

    result_path = Path.cwd().joinpath(f'result/global_shifting/{Path(path).stem}/{graph_key}/')
    result_path.mkdir(parents=True, exist_ok=True)
    # G = gh.load_file(path, key=graph_key)
    G = DiGraph()
    G.add_edges_from([('1', '6'), ('2', '4'), ('2', '7'), ('3', '4'), ('4', '5'), ('5', '6'), ('5', '7')])
    nx.set_edge_attributes(G, 'b', 'color')
    print("\rCycle removal...", end='')
    G_cycle_removed = G.greedy_cycle_removal()
    print(f"\rLayer assignment and crossing reduction | {graph_key}", end='')
    G_cycle_removed = global_shifting(G_cycle_removed, name=file_name, path=result_path)
    print("\rx-coordinate assigment...", end='')

    pos = {}
    # p = 0
    for node in G_cycle_removed.nodes:
        y = -G_cycle_removed.nodes[node]['level']
        x = G_cycle_removed.nodes[node]['pi']
        pos[node] = (x, y)

    colors_loaded_graph = [G[u][v]['color'] for u, v in G.edges()]
    colors = [G_cycle_removed[u][v]['color'] for u, v in G_cycle_removed.edges()]

    print("\rDrawing...", end='')
    plt.figure(figsize=figsize)
    nx.draw(G, edge_color=colors_loaded_graph, with_labels=False)

    print("\rWriting to file...", end='')
    plt.savefig(result_path.joinpath(f'{file_name}_original.png'))

    print("\rDrawing 2...", end='')
    plt.figure(figsize=figsize)

    nx.draw(G_cycle_removed, pos=pos, edge_color=colors, with_labels=False)

    print("\rWriting to file 2...", end='')
    plt.savefig(result_path.joinpath(f'{file_name}.png'))
    nx.readwrite.write_gpickle(G_cycle_removed, result_path.joinpath('graph.dat'))
    print(f"\rDone! {file_name}", end='\n')


def load_results(file_name, graph_key):
    result_path = Path.cwd().joinpath(f'result/global_shifting/{Path(file_name).stem}/{graph_key}/graph.dat')
    if not result_path.exists():
        raise FileNotFoundError(result_path)

    return nx.readwrite.read_gpickle(result_path)
