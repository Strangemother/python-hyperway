from .packer import argspack
from .nodes import as_unit
from .ident import IDFunc


def make_edge(a, b, name=None, through=None, node_class=None):
    c = Connection(
            as_unit(a, node_class=node_class),
            as_unit(b, node_class=node_class),
            name=name, through=through)
    return c


def is_edge(unit):
    return isinstance(unit, Connection)


def wire_partial(func, *wire_a, **wire_kw):
    """Wire function that accepts a standard function, to 
    later execute as a wire function.

    This _partial_ variant acts like a funtools.partial, allowing
    pre-setting of arguments to the wire function.

        def my_wire_func(*a, **kw):
            print('WIRING:', a, kw)
            return argspack(*a, **kw)

        wire_partial(my_wire_func, 10, 20, foo=2, egg=True)
        my_wire_func(30, 40, foo=5)
        WIRING: (10, 20, 30, 40) {'foo': 5, 'egg': True}

    Allowing the developer to apply generic functions as a wire
    method without handling the argpack.
    
        c = make_edge(f.add_1, f.add_2, 
                through=wire(f.mul_5))
    """
    def wrapper(*a, **kw):
        """Wrapper wire function."""
        wire_kw.update(kw)
        result = func(*wire_a, *a, **wire_kw)
        return argspack(result)
    return wrapper


def wire(func, **wkw):
    """Wire function that accepts a standard function, to 
    later execute as a wire function

    Allowing the developer to apply generic functions as a wire
    method without handling the argpack.
    
        c = make_edge(f.add_1, f.add_2, 
                through=wire(f.mul_5))
    
    The wrapped function is called with all runtime args/kwargs, allowing
    it to work with its normal signature. Wire-setup kwargs (wkw) flow 
    through the ArgsPack for pipeline metadata.
    """
    def wrapper(*a, **kw):
        """Wrapper wire function."""
        result = func(*a, **kw)
        return argspack(result, **wkw)
    return wrapper


def as_connections(*items, graph=None):
    """Given a list of items, ensure each result object is a connection
    . If an item is a Connection, the original connection is given
    If an item is a node, any Connection(a=node) is returned.
    """
    res = ()

    for item in items:
        if is_edge(item):
            res += (item, )
            continue

        # resolve node
        unit = as_unit(item)
        conns = graph.resolve_node_connections(unit)
        res += conns
    return res


def get_connections(graph, unit, akw=None):
    """
    Given a graph and a unit (node or connection), return the connections from that unit.
    This function checks if the unit has a custom get_connections() method;
    if so, it uses that method to retrieve the connections. Otherwise, it looks up
    the connections in the graph using the unit's ID.

    The optional `akw` is pushed through to the unit.get_connections() if it exists.

    """
    # resolve the list of connections using the
    # id of the unit.
    # print('xx - Get for', unit)
    if hasattr(unit, 'get_connections'):
        # Is an edge.
        print('Using unit.get_connections')
        res = unit.get_connections(graph, akw=akw)
    else:
        res = graph.get(as_unit(unit).id(), None)

    if is_edge(unit):
        # the connection given, we want connection from this connection
        # as such, as can resoble id(unit[Connection].b) connections.
        # for the next - BUT as A callers.
        tip_connections = graph.get(unit.b.id())
        # return a callers.
        if tip_connections is not None:
            res = tuple(x.get_a() for x in tip_connections)
            print(f'.. returning A nodes of B nodes from the origin: {unit}')
        else:
            # No connections from edge.b - this is an end node
            res = None

    if res is None:
        print(f' C(0) "{unit}"')
        # print(f'NO Connections for Unit "{unit}"')

    return res


class Connection(IDFunc):
    """Represents a connection between A and B.
    + Lives on the graph at the node location
    + Returns the process function for the stepper caller.
    """
    def __init__(self, a, b, name=None, through=None, on=None):
        self.name = name
        self.a = a
        self.b = b
        self.through = through
        self.on = on
        self._resolver = None

    def __str__(self):
        return self.as_str()

    def __repr__(self):
        return f"<{self.as_str()}>"

    def __call__(self, *a, _graph=None, **kw):
        """Call this connection, returning the result of B.
        This will call A, then the through function (if any), then B."""
        g = self.on if _graph is None else _graph
        return self.get_a(g).process(*a, **kw)

    @property
    def merge_node(self):
        """If A is a merge node."""
        return self.get_a().merge_node

    def stepper_call(self, akw, stepper=None, **meta): # NOSONAR(S1172)
        """This function is called explicitly by the stepper to process
        this connection side A, returning the result for A.
        the extern `get_connections` function should yield the [W -> B] next
        step as a Partial.

        Call upon self.process with the given argspack. This will call the
        wire function, and then the B function, returning B result.
        """
        return self.get_a().process(*akw.a,**akw.kw)

    def half_call(self, akw, stepper=None, **meta): # NOSONAR(S1172)
        """Specifically call A and return its res, and the next caller.

        This is called by the stepper when iterating upon a Unit `call_one_unit`.
        Rather than call the given node, the connections are discovered, and
        each `connection.half_call` processes _its_ a-side and responds with
        a partial connection.
        """
        res = self.get_a().process(*akw.a, **akw.kw)
        return ( self.partial_instance(), argspack(res), )

    def partial_instance(self):
        """The 'half call' from the stepper needs a _thing_ to call (next caller)
        Here we return an instance of a PartialConnection, connecting the wire
        function to B. When 'get_connections' is called on the stepper stored `func`
        this child connection can return the correct connections from the sub node.
        """
        return PartialConnection(self)

    def as_str(self):
        through = ' '
        if self.through:
            f = self.through
            n = f.__name__ if hasattr(f, '__name__') else str(f)
            through = f' through="{n}"'

        return (f"{self.__class__.__name__}"
                f"({self.a}, {self.b},{through} name={self.name})")

    def call_through(self, *a, **kw):
        """Call the through() function with the given args.
        If the through function does not exist, return a argspack.
        """
        if self.through:
            print('Calling through ...')
            return self.through(*a, **kw)
        return argspack(*a, **kw)

    def get_a(self, graph=None):
        return self.get_node_key('a', graph)

    def get_b(self, graph=None):
        return self.get_node_key('b', graph)

    def get_node_key(self, key, graph=None):
        g = graph or self.on
        n = getattr(self, key)
        if g is None:
            return n
        resolve = self.get_resolver()
        return resolve(n, g)

    def get_resolver(self):
        if self._resolver is None:
            from .graph.base import resolve
            self._resolver = resolve
        return self._resolver

    def pluck(self, *a, **kw):
        """The pluck function receives values for node A, and also calls B
        with the A Result, returning the value of B.

        This is used for development to test a single connection (plucking one
        thread). Generally  processing through the graph will push data into the
        global event chain; and not procedural connections.

            add(divider, divider, through=argpack)
        """

        """
        ISSUE 01: Functional Return Sentinal
        """
        res = self.get_a().process(*a, **kw)
        return self.process(res)

    def process(self, *a, **kw):
        akw = self.call_through(*a, **kw)
        return self.b.process(*akw.args, **akw.kwargs)


class PartialConnection(IDFunc):

    def __init__(self, parent_connection, on=None, node=None):
        self.on = on
        self.node = node
        self.parent_connection = parent_connection

    def __call__(self, *a, _graph=None, **kw):
        r = self.process(*a, **kw)
        return r

    def __str__(self):
        return self.as_str()

    def __repr__(self):
        return f"<{self.as_str()}>"

    def as_str(self):
        return (f"{self.__class__.__name__} to "
                f"{self.b}")

    @property
    def merge_node(self):
        return self.b.merge_node

    @property
    def b(self):
        return self.parent_connection.get_b()

    def get_connections(self, graph, akw=None): # NOSONAR(S1172)
        """Return the connections from node B, as the next step.
        This is called by the stepper when processing this partial connection."""
        resolve = graph.resolve_node_connections
        b_next = resolve(self.parent_connection.b)
        return b_next

    def wb_pair(self):
        """Return the _wire_ and _node B_ function as a tuple pair."""
        pc = self.parent_connection
        return (pc.through, pc.b)

    def stepper_call(self, akw, stepper=None, **meta): # NOSONAR(S1172)
        """This function is called explicitly by the stepper to process
        this partial connection [W -> B].
        Call upon self.process with the given argspack. This will call the
        wire function, and then the B function, returning B result.
        """
        return self.process(*akw.a,**akw.kw)

    def process(self, *a, **kw):
        """A call upon self, should actuate the parent wire function to the
        B function.
        """
        pr = self.parent_connection
        return pr.process(*a, **kw)

    def graph_next_process_caller(self, _graph=None):
        g = _graph or self.on
        return self.node
