from collections import defaultdict
from pprint import pprint as pp

from .packer import argspack, merge_akws
from .nodes import is_unit
from .edges import (Connection, as_connections,
                    is_edge, PartialConnection, get_connections)
from .graph.base import is_graph

def run_stepper(g, unit_a, val):
    """Here we can _run_ the graph, executing the chain of connections
    from A to Z. The _result_ is the end attribute. This may be a graph of
    results.
    """

    return process_forward(g, unit_a, argspack(val))


def process_forward(graph, start_node, argspack):
    print('\n---Run from A', start_node, argspack, '\n---\n')
    """
    This runs a _Stepper_, the unit to process a vertical stack in a forward
    bar process. Each function execution through the condition is waited through
    a forever stepper.

    A each _node_ resolves _connections_, the connection is partial called

      res = edge.a(...res) -> wait -> edge.continue(res) -> res ...

    This allows pausing, and alterations of the stepper.
    """

    return stepper_c(graph, start_node, argspack)


def expand_tuple(items, second):
    """Expand items into rows paired with second.
    
    Args:
        items: Iterable of connections/callables, or None if no connections exist
        second: The argspack to pair with each item
        
    Returns:
        Tuple of (item, second) pairs. Returns empty tuple if items is None.
    """
    if items is None:
        # No connections - return empty rows (end of branch)
        return ()
    res = ()
    for conn in items:
        if isinstance(conn, (tuple,list)):
            for c in conn:
                res += ((c, second),)
            continue
        res += ((conn, second),)
    return res


def expand_list(items, second):
    """Alternative expand implementation using a list accumulator.

    Builds rows with list append/extend and converts to a tuple at the end.
    The return shape matches the original expand().
    
    Args:
        items: Iterable of connections/callables, or None if no connections exist
        second: The argspack to pair with each item
        
    Returns:
        Tuple of (item, second) pairs. Returns empty tuple if items is None.
    """
    if items is None:
        # No connections - return empty rows (end of branch)
        return ()
    
    res_list = []
    for conn in items:
        if isinstance(conn, (tuple, list)):
            res_list.extend((c, second) for c in conn)
        else:
            res_list.append((conn, second))
    return tuple(res_list)


expand = expand_tuple  # Choose which expand implementation to use

def set_global_expand(expand_func):
    """Set the global expand function used by the StepperC class.

    Args:
        expand_func: A function that matches the signature of expand_list/expand_tuple.
    """
    global expand
    expand = expand_func    

def stepper_c(graph, start_node, argspack):
    stepper = StepperC(graph)
    res = stepper.start(start_node, akw=argspack)

    return stepper, res


class StepperIterator(object):

    def __init__(self, stepper, funcs, akw, **config):
        self.stepper = stepper
        self.start_nodes = funcs
        self.start_akw = akw
        self.config = config
        self._iterplace = None
        self.rows = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.rows is None:
            self.rows = self.stepper.start(*self.start_nodes, akw=self.start_akw)
        while len(self.rows) > 0:
            yield self.rows
            self.rows = self.stepper.call_rows(self.rows)
        raise StopIteration


def is_merge_node(next_caller):
    r = False
    if hasattr(next_caller, 'merge_node'):
        r = next_caller.merge_node
    # print('next_caller', next_caller, 'is_merge_node', r)
    return r


class StepperC(object):
    """This stepper will work with functions - or just callers, and argpacks
    """
    concat_aware = False

    def __init__(self, graph, rows=None):
        self.graph = graph
        self.run = 1

        self.stash_ends = True
        self.reset_stash()

        self.start_nodes = None
        self.start_akw = None
        self.rows = rows

    def reset_stash(self):
        self.stash = defaultdict(tuple) 

    def prepare(self, *funcs, akw):
        """Prepare the stepper with the start nodes and the initial argument
        pack. Next iterations will yield steps.
        """
        self.start_nodes = funcs
        self.start_akw = akw

    def __iter__(self):
        """Call upon an iterator to yield the stepper per next() interaction:

            generator = iter(Stepper(graph))
            rows = next(generator)
        """
        return next(self.iterator())

    def iterator(self, *funcs, akw=None, **iter_opts):
        if len(funcs) == 0:
            funcs = self.start_nodes
        akw = akw or self.start_akw
        return StepperIterator(self, funcs, akw, **iter_opts)

    def step(self, rows=None, count=1):
        """
        Run _one step_ of the stepper. Similar to next(iter(stepper()))

            s = graph.stepper(node, 999, foo=2)
            rows = s.step()
            (
                (next, argspack,)
            )

        Also available:

            s = iter(graph)
            s = graph.iterator()

            rows = next(s)
        """
        c = 0
        st_nodes = self.start_nodes
        if st_nodes is None:
            # Start node must be something...
            raise Exception('start_nodes is None')
        self.rows = rows or self.rows or expand(st_nodes, self.start_akw,)

        while c < count:
            c += 1
            self.rows = self.call_rows(self.rows)
        return self.rows

    def start(self, *funcs, akw):
        """An exposed caller for the `call_many` function
        """
        return self.call_many(*funcs, akw=akw)

    def call_many(self, *funcs, akw):
        """Call many callers (Units or nodes) with the same argument pack:

            call_many(func_a, func_b, func_c, akw=argspack(200))

        is synonymous with:

            func_a(200)
            func_b(200)
            func_c(200)

        This calls `call_one` for every function

            ...
            call_one(func_a, argspack(200))
        """
        all_rows = ()
        for func in funcs:
            all_rows += self.call_one(func, akw)
        return all_rows

    def call_rows(self, rows):
        """Call many _rows_, each row being a (callable, argspack).
        This is similar to call_many, however with this method, each row has a
        unique argspack:

            res = (
                (func_a, argspack(100),),
                (func_b, argspack(100),),
                (func_c, argspack(200),),
            )

            rows = call_rows(res)

        The result is `call_rows` compatible.
        This calls `call_one` for every function

        Synonymous to:

            res = ()
            for func, akw in rows:
                add_rows = self.call_one(func, akw)
                res += add_rows
            return res
        """

        if self.concat_aware:
            rows = self.row_concat(rows)

        all_rows = ()
        for func, akw in rows:
            all_rows += self.call_one(func, akw)
        return all_rows

    def row_concat(self, rows, concat_flat=False):
        """Given a list of expanded rows, discover any events heading for
        the same destination node. If matches occur, the argspack is concatenated
        and the multiple calls to the one node, becomes _one_ call with multiple
        arguments.
        """
        items = set()
        _args = defaultdict(tuple)

        """Iterate the rows, unpacking the _next_ function.
        This is required as some items (e.g. a PartialConnection) shadow
        the outbound node.
        """
        for i, (next_caller, akw) in enumerate(rows):
            uniquable = next_caller
            if isinstance(next_caller, PartialConnection):
                """Refering to the wire function here ensures the call is unqiue
                when one (of many) partial connections is heading to the same
                node B.

                for example, the following is considered `2` unique connections,

                    (
                        # wire, node
                        (None, node_b,),
                        (None, node_b,),
                        (though, node_b,),
                    )
                """
                uniquable = next_caller.wb_pair()

            items.add(uniquable)
            """Assign to a reverse match. When reversed, the values become
            the rows.
            """
            addr = uniquable if is_merge_node(next_caller) else (uniquable, i)

            _args[addr] += ( (next_caller, akw,), )

        if len(items) == len(rows):
            return rows

        new_rows = ()
        # For each item, recreate the argspack and restack the row.
        for uniquable, calls in _args.items():
            akws = ()
            for next_caller, akw in calls:
                akws += (akw,)

            # concat_flat to reapply the same count of rows _out_, 
            # as was given.
            if concat_flat:
                # Then reiterate, applying each caller with the new args
                for next_caller, _ in calls:
                    new_rows += ( (next_caller, merge_akws(*akws)), )
                continue

            # Because we need only _one_ row, we can cheat here, using
            # the dangling reference from the previous loop.
            new_rows += ( (next_caller, merge_akws(*akws)), )
        return new_rows

    def call_one(self, func, akw):
        """
        Given a function, call it with the given argspack. Returns a tuple
        of tuples, each row being the _next_ function to call with the respective
        functions. The _next_ functions are collected through the connections.

            rows = call_one(my_func, argspack(100, foo=1))

        The rows results is compatible with a call_rows call.

        Each is a _*future_ call for the stepper, as-in, the callable and the
        expected arguments for that callable is a row.

        Returns _many_ rows:

            (
                (callable, argspack(100),),
                ...
                (callable, argspack(100),),
            )
        """
        if func is None:
            # Bypass
            print('call_one blank next. - bypass')
            return self.no_branch(func, akw)

        if isinstance(func, PartialConnection):
            return self.call_one_partial_connection(func, akw)

        if is_unit(func):
            return self.call_one_unit(func, akw)

        if is_edge(func):
            return self.call_one_connection(func, akw)

        ## Future implementation consideration:
        # if is_graph(func, self.graph.__class__):
        #     return self.call_one_graph(func, akw)

        if callable(func):
            return self.call_one_callable(func, akw)

        return self.call_one_fallthrough(func, akw)

    def call_one_fallthrough(self, thing, akw):
        """
        The given function is not A Connection, PartialConnection, Unit, or
        function (a callable). The last-stage action should occur.

        In the base form, this applies "None" as the _next_ items, and will
        be captured by the next call to this row entry.

        If unhandled, the result will fall-through indefinately.
        """
        print(' -- Falling through call...')
        return ( (None, akw,),)

    def call_one_connection(self, edge, akw):
        """The given callable is an Connect (edge) or a callable function
        (such as the raw function).

        We collect the next connections and _call_ the callable unit.
        If an edge (Such as Connection()), it'll do an A (return wire->B)
        call.
        If a function, the _result_ is pushed into the future call stack.
        """
        a_to_b_conns = get_connections(self.graph, edge)
        raw_res = edge.stepper_call(akw, stepper=self)
        res_akw = argspack(raw_res)

        return expand(a_to_b_conns, res_akw)

    def call_one_callable(self, func, akw):
        """The given callable is an Connect (edge) or a callable function
        (such as the raw function).

        We collect the next connections and _call_ the callable unit.
        If an edge (Such as Connection()), it'll do an A (return wire->B)
        call.
        If a function, the _result_ is pushed into the future call stack.
        """
        a_to_b_conns = get_connections(self.graph, func)
        raw_res = func(*akw.a,**akw.kw)
        res_akw = argspack(raw_res)

        return expand(a_to_b_conns, res_akw)

    def call_one_partial_connection(self, partial_conn, akw):
        """A Partial connection is Connection [Wire] to B.
        This yields when asking for the _next_ node from a connection [A].

        The partial connection process the wire function and B node,
        returning the B node raw result.
        """
        wire_raw_res = partial_conn.stepper_call(akw, stepper=self)
        b_conns = get_connections(self.graph, partial_conn.b)

        # The raw wire result here, is the wire -> B result (as the
        # Therefore collect the B node connections(.A), for the next calls
        wire_akw = argspack(wire_raw_res)

        if b_conns is None:
            # If no connections the B node is the end.
            return self.end_branch(partial_conn, wire_akw)

        next_callables = tuple(x.b for x in b_conns)
        return expand(next_callables, wire_akw)

    def call_one_unit(self, unit, akw):
        """The given callable is a Unit instance, and we consider this the
        A node of a connection.

        Collect the A to B connections, _call_ the connection of which
        calls A, and return the next callable - a _wire_ function of
        the connection; [wire] -> B
        """
        # where unit == a
        a_to_b_conns = get_connections(self.graph, unit)

        if a_to_b_conns is None:
            # This node call has no connection, assume an end;
            return unit.leaf(self, akw)

        """Rather than call the given unit, we discover the connections
        and call each connection. The `half_call` calls side A, and returns
        [W -> B] PartialConnection.

        This is to ensure a single _connection_ can respond to the activation
        (it may be on a different graph, therefore the nodes may be different)
        however it may be prudent to call the unit _before_ the iteration,
        essentially performing get_a().process _once_.

        """

        # Run each edge, returning the mid-point.
        res = ()
        for conn in a_to_b_conns:
            # Call A, return W.
            # row = (next_caller, result)
            row = conn.half_call(akw, stepper=self)
            res += (row,)
        return res

    def no_branch(self, func, akw):
        return self.end_branch(func, akw)

    def end_branch(self, func, akw):
        # print(' ... Connections end ...', akw)
        # A tuple of rows
        if self.stash_ends:
            self.stash[func] += (akw,)
            # return nothing to contine.
            return ()

        return (
                ( None , akw,),
            )

    def flush(self):
        for caller, akw in self.stash.items():
            yield caller, akw
        self.reset_stash()

    def peek(self):
        for akw in self.stash.values():
            yield akw
