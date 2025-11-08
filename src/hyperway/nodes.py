from .packer import argspack, test_argpack
from .ident import IDFunc


def as_unit(u, node_class=None, **node_kwargs):
    if is_unit(u, node_class):
        return u
    return (node_class or Unit)(u,**node_kwargs)


def as_units(*items, node_class=None, **node_kwargs):
    r = ()
    for item in items:
        r += (as_unit(item, node_class=node_class, **node_kwargs),)
    return r


def is_unit(u, node_class=None):
    types = (Unit,)
    if node_class is not None:
        types += (node_class,)

    return isinstance(u, types)

CACHE = {}

class UnsetSentinal:
    pass

UNSET = UnsetSentinal()


def get_edge_func():
    r = CACHE.get('make_edge')
    if r:
        return r

    from .edges import make_edge

    CACHE['make_edge'] = make_edge
    return make_edge


class Unit(IDFunc):

    merge_node = False
    name = None
    sentinal = UNSET

    def __init__(self, func, **node_kwargs):
        self.func = func
        self.__dict__.update(node_kwargs)

    def __str__(self):
        return self.as_str()

    def __repr__(self):
        return f"<{self.as_str()}>"

    def as_str(self):
        n = self.get_name()
        return f"{self.__class__.__name__}(func={n})"

    def get_name(self):
        f = self.func
        n = self.name or (f.__name__ if hasattr(f, '__name__') else str(f))
        return n
    
    def get_outbound_connections(self, graph):
        """Return all outbound connections from this node in the given graph."""
        connections = graph.get(self.id(), None)
        return connections

    def get_inbound_connections(self, graph):
        """Return all inbound connections to this node in the given graph.
        
        Note: The graph stores each edge twice (once by edge ID, once by node A ID),
        so we deduplicate by edge ID to return unique connections only.
        """
        seen = set()
        inbound = []
        for edges in graph.values():
            for edge in edges:
                edge_id = edge.id()
                if edge.b.id() == self.id() and edge_id not in seen:
                    seen.add(edge_id)
                    inbound.append(edge)
        return inbound

    def input(self, a, kw):
        """Run the function through the graph, events will propogate into
        the event tree.
        """
        # Put the result into the event tree.
        return self.process(a, kw)

    def leaf(self, stepper, akw):
        """The stepper hit the tip of a branch and this node was the leaf
        Capture "end" events and return a row result.

        In this case the leaf hasn't been processed yet. This is because
        "process" is done through a Connection.A call, or a PartialConnection
        call.
        As such, perform any final processing, such as executing the
        process() function, and update the result ready for the next _stash_
        event.

        To follow the stepper path, return the result with no destination (default)
        return connections to continue this path.

            def leaf(self, stepper, akw):
                rows = (
                        (None, argspack(akw))
                    )

                return rows
        """
        res = argspack(self.process(*akw.a,**akw.kw))
        return stepper.end_branch(self, res)

    def process(self, *a, **kw):
        """Run the function without the strings.
        """
        is_nully = len(a) == 1 and a[0] is self.sentinal
        return self.func(*(() if is_nully else a), **kw)


class Nodes(Unit):

    def process(self, *a, **kw):
        """Run the function without the strings.
        """
        return self.func(*a, **kw)
