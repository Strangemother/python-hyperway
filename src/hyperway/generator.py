
from .nodes import as_units
from .edges import make_edge


def fully_connected(*nodes, **node_kwargs):
    """Return a tuple of edges, connecting edge node to every other node.
    Note this will produce _two_ edges for a connection between two units.
    """
    units = as_units(*nodes, **node_kwargs)
    u_s = set(units)
    res = ()
    for u in units:
        others = u_s ^ {u}
        for other in others:
            e = make_edge(u, other)
            res += (e,)
    return res