from itertools import tee
from collections import defaultdict

from ..edges import make_edge, is_edge
from ..nodes import as_unit, as_units


class GraphBase(defaultdict):

    def __init__(self, *a, **kw):
        super().__init__(tuple)

    def resolve_node_connections(self, other):
        print('Resolve', other)
        res = self.get(other.id(), None) or ()
        if len(res) == 0:
            print('no res', other)
            return self.resolve_node_to_nowhere(other)
        return res

    def resolve_node_to_nowhere(self, other): # NOSONAR(S1172)
        """Given a node with no connections, return a connection to nowhere.
        Override in subclasses to provide custom behaviour."""
        return ()


def is_graph(u, *others):
    types = (GraphBase,) + others
    return isinstance(u, types) or (hasattr(u, 'func') and isinstance(u.func, types))


def add(graph, unit, other, name=None, through=None, node_class=None):
    """Build a connection from unit to other, into the given graph.
    return the new connection[s].
    """
    c = make_edge(unit, other, name, through, node_class=node_class)
    put(graph, c)
    return c


def connect(graph, *nodes, through=None, node_class=None):
    """Perform add for many nodes, if through given, each node to node
    receives a single wire function
    """
    res = ()
    _units = as_units(*nodes, node_class=node_class)
    _pairs = pairs(_units)

    for a, b in _pairs:
        # print('Bridging', a, b, f"{through=}")
        c = add(graph, a, b, through=through, node_class=node_class)
        res += (c,)
    return res


def pairs(input_list):
    res = ()
    for i in range(len(input_list) - 1):
        r = (input_list[i], input_list[i + 1])
        res += (r, )
    return res


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def put(graph, edge):
    """Build a connection from unit to other, into the given graph.
    return the new connection[s].
    """
    # # id of the _edge_
    # graph[id(edge)] += (edge, )
    # # Store the ID of node A, to resolve this edge.
    # graph[id(edge.a)] += (edge, )

    graph.add_edge(edge)
    # graph.add_edge(edge.a, edge)


def resolve(node, graph):
    """Given the node (ID), return the Unit from the graph.
    
    This is a standalone resolver that checks if the graph has a custom
    resolve_node method. If not, it returns the node as-is.
    """
    # Check if graph has a resolve_node method (avoid circular dependency)
    if hasattr(graph, 'resolve_node'):
        # Use the graph's custom resolver
        return graph.resolve_node(node)
    
    # Fallback: nodes are not stored separately, return as-is
    return node

