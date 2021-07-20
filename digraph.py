from __future__ import annotations

import copy

import networkx as nx

from helper_functions import graph_helper_functions as gh


class Block:
    def __init__(self, nodes: list[str], levels: list[int], predecessors: list[str], successors: list[str], id=-1):
        self.id = id
        self.nodes = nodes
        self._upper = nodes[0]
        self._lower = nodes[-1]
        self.levels = levels
        self._predecessors = predecessors
        self._successors = successors
        self.i_p = []
        self.i_n = []
        pass

    @property
    def upper(self) -> str:
        return self._upper

    @property
    def lower(self) -> str:
        return self._lower

    @property
    def n_n(self) -> list[str]:
        return self._predecessors

    @n_n.setter
    def n_n(self, value: list[str]) -> None:
        self._predecessors = value

    @property
    def n_p(self) -> list[str]:
        return self._successors

    @n_p.setter
    def n_p(self, value: list[str]) -> None:
        self._successors = value

    def clear(self):
        self.i_n.clear()
        self.i_p.clear()
        self._predecessors.clear()
        self._successors.clear()

    def __str__(self):
        return f"id: {self.id}, nodes{self.nodes}"


class BlockList:
    def __init__(self):
        self.blocks: dict[int, Block] = {}
        self.block_order: list[int] = []

    def add_block(self, B: Block) -> int:
        block = len(self.block_order)
        B.id = block
        self.blocks[block] = B
        self.block_order.append(block)
        return block

    def new_block_number(self) -> int:
        return len(self.block_order)

    def pi(self, block: int):
        return self.block_order.index(block)

    def move(self, block: Block, pi):
        old_pos = self.block_order.index(block.id)
        self.block_order.remove(block.id)

        if pi > old_pos:
            pi = pi - 1

        self.block_order.insert(pi, block.id)

    def swap_pos(self, id_A: int, id_b: int):
        pos_a = self.block_order.index(id_A)
        pos_b = self.block_order.index(id_b)

        self.block_order[pos_a] = id_b
        self.block_order[pos_b] = id_A

    def __len__(self):
        return len(self.block_order)

    def block_from_id(self, id: int) -> Block:
        return self.blocks[id]

    def block_from_pos(self, pos: int) -> Block:
        return self.blocks[self.block_order[pos]]

    def __getitem__(self, pos):
        return self.block_from_pos(pos)

    def __str__(self):
        # return str(self.blocks)
        return ''


class DiGraph(nx.DiGraph):
    _dummy_root = "DUMMY_ROOT"

    def __init__(self):
        super(DiGraph, self).__init__()
        self.blocks = BlockList()
        self._dummy_node_number = 0

    def get_block_list(self) -> BlockList:
        self.longest_path_layering()
        return self.blocks

    def longest_path_layering(self):
        nx.set_node_attributes(self, None, 'level')
        m = len(self.nodes)

        sinks = [u for u, d in self.out_degree() if d == 0]

        for sink in sinks:
            block_id = self.blocks.add_block(Block([sink], [m], list(self.predecessors(sink)), []))
            self.nodes[sink]['level'] = m
            self.nodes[sink]['block'] = block_id

        nodes = [u for u in self.nodes if self.nodes[u]['level'] is None]

        while nodes:
            node = nodes.pop()

            layers_neighbors = []

            for neighbor in list(self.successors(node)):
                if self.nodes[neighbor]['level'] is not None:
                    layers_neighbors.append(self.nodes[neighbor]['level'])
                else:
                    # if not all neighbors(from with he is the parent) have a layer, insert the node again and try a
                    # other one and DON'T set the layer of the node!
                    nodes.insert(0, node)  # .append would in combination with .pop result in a endless loop
                    break
            else:  # If loop runs trow all neighbors with out a 'break' -> set the new layer for node
                n = min(layers_neighbors) - 1
                self.nodes[node]['level'] = n

                for neighbor in list(self.successors(node)):
                    if self.nodes[neighbor]['level'] - n > 1:
                        self._insert_dummy_edges_and_blocks(node, neighbor)

                block = self.blocks.add_block(
                    Block([node], [n], list(self.predecessors(node)), list(self.successors(node))))

                self.nodes[node]['block'] = block

    def greedy_cycle_removal(self):
        copy_graph = copy.deepcopy(self)

        s1 = []
        s2 = []

        while list(copy_graph.nodes):

            sinks = [v for v, d in copy_graph.out_degree() if d == 0]
            while sinks:
                sink = sinks.pop()
                s2.insert(0, sink)
                copy_graph.remove_node(sink)

                sinks = [v for v, d in copy_graph.out_degree() if d == 0]

            sources = [v for v, d in copy_graph.in_degree() if d == 0]
            while sources:
                source = sources.pop()
                s1.append(source)
                copy_graph.remove_node(source)

                sources = [v for v, d in copy_graph.in_degree() if d == 0]

            if copy_graph.nodes:
                delta = self._edge_delta(copy_graph)
                v = max(delta, key=delta.get)
                copy_graph.remove_node(v)
                s1.append(v)
        s = []
        s.extend(s1)
        s.extend(s2)

        # Create new Graph with changed edges
        _cycle_removed = copy.deepcopy(self)

        for u, v in self.edges:
            if s.index(u) > s.index(v):
                # Edge from u to v is in the wrong direction
                _cycle_removed.remove_edge(u, v)
                _cycle_removed.add_edge(v, u, color='r')
            if s.index(u) == s.index(v):
                _cycle_removed.remove_edge(u, v)

        return _cycle_removed

    # region global_crossing_reduction

    def phi(self, node: str) -> int:
        return self.nodes[node]['level']

    def block(self, node: str) -> int:
        return self.nodes[node]['block']

    def _insert_dummy_edges_and_blocks(self, u, v):
        level_u = self.nodes[u]['level']
        level_v = self.nodes[v]['level']

        if level_v - level_u >= 1:
            self.remove_edge(u, v)  # remove old edge

            block = self.blocks.new_block_number()
            last_node = u
            edges_in_block = []
            levels = []

            # from one layer 'u' to one layer under 'v' add a node and add it to a block
            for level in range(level_u + 1, level_v):
                current_node = f'DUMMY_NODE{self._dummy_node_number}'
                self._dummy_node_number += 1

                self.add_node(current_node, level=level, block=block, dummy=True)
                edges_in_block.append(current_node)
                levels.append(level)

                self.add_edge(last_node, current_node, color='y', dummy=True)
                last_node = current_node

            self.add_edge(last_node, v, color='y')
            self.blocks.add_block(Block(edges_in_block, levels, [u], [v]))

    # endregion
    @staticmethod
    def load(path):
        return nx.readwrite.read_gpickle(path)

    @staticmethod
    def _edge_delta(G):
        results = {}
        for node in G.nodes:
            results[node] = G.out_degree(node) - G.in_degree(node)

        return results

    # region Tree

    def to_tree(self) -> tuple[DiGraph, str]:
        return self.as_tree(self)

    def insert_dummy_root(self):
        root_nodes = [n for n, d in self.in_degree() if d == 0]

        self._is_dummy_root = True

        self.add_node(self._dummy_root)
        for v in root_nodes:
            self.add_edge(self._dummy_root, v, color='y')
        return self._dummy_root

    def remove_dummy_root(self):
        self.remove_node(self._dummy_root)

    @staticmethod
    def as_tree(G):
        def set_order_in_layers(G, root):
            parent_node = root
            child_nodes = gh.children(G, parent_node)
            new_childs = []
            order = 0
            while child_nodes:
                child_node = child_nodes.pop()

                G.nodes[child_node]['order'] = order

                new_childs.extend(gh.children(G, child_node))
                order += 1
                if not child_nodes:
                    parent_node = child_node
                    order = 0
                    child_nodes = list(dict.fromkeys(new_childs))
                    new_childs = []
            return G

        G.remove_edges_from(list(nx.selfloop_edges(G)))

        root_nodes = [n for n, d in G.in_degree() if d == 0]
        root_node = None

        # No node with 0 in edges
        if len(root_nodes) == 0:
            return G, None

        elif len(root_nodes) > 1:
            root_node = G.insert_dummy_root()
        else:
            root_node = root_nodes[0]

        # G = set_order_in_layers(G, root_node)

        return G, root_node
    # endregion
