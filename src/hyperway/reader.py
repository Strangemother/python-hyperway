from collections import defaultdict
from .nodes import as_unit


def thin_graph(graph):
    res = defaultdict(tuple)
    for conns in graph.values():
        for conn in conns:
            res[conn.a.id()] += (conn.b.id(),)
    return res


def flat_graph(graph):
    res = ()
    thin = thin_graph(graph)
    for node_a, b_nodes in thin.items():
        for node_b in b_nodes:
            res += ((node_a, node_b),)
    return res


def get_nodes_edges(graph):
    """Return node names, and all edges as a tuple and a tuple of tuples."""
    nodes = set()
    edges = set()
    for name, connections in graph.items():
        for connection in connections:
            ia = str(connection.a.id())
            ib = str(connection.b.id())
            edges.add( (ia, ib), )
            nodes.add((ia, connection.a.get_name()))
            nodes.add((ib, connection.b.get_name()))
    return nodes, edges


def read_linear_chain(graph, node, with_through=True): # divider(100)
    """Read forward each connection

    When reading, we can opt for adding _through_ functions. The tuple coupling
    defines _when_ a through node is called. Initially these seems counter
    intuitive:

    with `read_linear_chain(g, a)` where A -> B has a through function, the
    function returns the through function within the initial set of the _next_
    tuple.

        read_linear_chain(g, a)
        (
            (<Unit(func=divider)>,),
            (<function doubler at 0x00000000025A8700>, <Unit(func=subtract)>),
            (<Unit(func=P_mul)>,),
            (<Unit(func=P_add)>,)
        )

    However if we start from `b`, the through function is not applied:

        read_linear_chain(g, a, with_through=False)
        read_linear_chain(g, b)
        (
            (<Unit(func=subtract)>,),
            (<Unit(func=P_mul)>,),
            (<Unit(func=P_add)>,)
        )

    This is because the A -> B _though_ function only occurs if the input
    recieves from node A. Other calls (starting from node B), aren't pulled in
    from the edge.

    ---

    Note: this isn't helpful for parallel chains, as nodes as flattened per
    execution step and won't present the correct paths.
    """
    unit = as_unit(node)
    conns = graph.resolve_node_connections(unit)
    run = len(conns) > 0
    res = (
            (unit,),
        )

    while run:
        next_conns = ()
        b_row = ()
        for c in conns:
            if with_through and c.through:
                b_row += (c.through,)
            b = c.b
            b_row += (b,)
            next_conns += graph.resolve_node_connections(b)

        res += ( b_row,)
        conns = next_conns
        run = len(conns) > 0

    return res


def read_tree_chain(graph, node, *items, with_through=True):
    """
    (   <Unit(func=P_mul_2.0)>,
        (   <Unit(func=P_mul_3.0)>,
            <Unit(func=P_truediv_10.0)>,
            <Unit(func=P_mul_0.5)>,
            <Unit(func=P_sub_10.0)>,
            <Unit(func=P_mul_3.0)>),
        (   <Unit(func=P_add_5.0)>,
            <Unit(func=P_mul_2.0)>,
            (   <Unit(func=P_sub_100.0)>,
                <Unit(func=P_mul_4.0)>,
                <Unit(func=P_truediv_3.0)>),
            (   <Unit(func=P_sub_50.0)>,
                <Unit(func=P_mul_2.0)>,
                <Unit(func=P_add_7.0)>)))
    """
    unit = as_unit(node)
    conns = graph.resolve_node_connections(unit)
    res = (unit,) + items
    l1 = len(conns) == 1
    for unit_conn in conns:
        row = conn_b_chain(graph, unit_conn, with_through)
        res += row if l1 else (row,)
    return res


def conn_b_chain(graph, conn, with_through):
    p_part = (conn.through,) if with_through and conn.through else ()
    return p_part + read_tree_chain(graph, conn.b, with_through=with_through)