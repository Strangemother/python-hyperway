from collections import defaultdict
from pprint import pprint as pp

from .packer import argspack, merge_akws
from .nodes import is_unit
from .edges import (Connection, as_connections,
                    is_edge, PartialConnection, get_connections)
from .graph.base import is_graph
from .constants import INITIATE_DISTRIBUTED, INITIATE_UNIFIED


class StepperException(Exception):
    """Exception raised when stepper encounters an error during execution."""
    pass


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


def expand_distributed(stepper, start_nodes, start_akw):
    """Expand for distributed initiation: call each start node once per connection.
    
    This is the standard edge-centric expansion mode where each outgoing
    connection from a start node results in a separate call to that node.
    
    Args:
        stepper: The StepperC instance
        start_nodes: Tuple of start node(s)
        start_akw: Initial argument pack
    Returns:    

        Tuple of (Connection, argspack) pairs ready for the next step
    """
    return expand(start_nodes, start_akw)

def expand_unified(stepper, start_nodes, akw):
    """Expand for unified initiation: call each start node once, then fan out to connections.
    
    This is an alternative to the standard expand() that implements node-centric
    initialization. Instead of calling the node once per connection, this calls
    the node once and distributes the result to all outgoing connections.
    
    Args:
        stepper: The StepperC instance
        start_nodes: Tuple of start node(s)
        akw: Initial argument pack
        
    Returns:
        Tuple of (PartialConnection, argspack) pairs ready for the next step
    """
    all_rows = ()
    
    for node in start_nodes:
        # Get connections for this node
        conns = get_connections(stepper.graph, node, akw=akw)
        
        if conns is None:
            # No connections - handle as leaf
            all_rows += node.leaf(stepper, akw)
            continue
        
        # Call node ONCE
        if is_unit(node):
            result = node.process(*akw.a, **akw.kw)
        else:
            # For raw callables
            result = node(*akw.a, **akw.kw)
        
        result_akw = argspack(result)
        
        # Create rows for each connection using the shared result
        # Each connection's wire function will receive the same result
        for conn in conns:
            # Create a PartialConnection (skipping the A call since we already did it)
            # The PartialConnection represents the [wire]->B portion
            partial = PartialConnection(conn)
            all_rows += ((partial, result_akw),)
    
    return all_rows


def stepper_c(graph, start_node, argspack):
    stepper = StepperC(graph)
    res = stepper.start(start_node, akw=argspack)

    return stepper, res


def stream(stepper, unwrap=True):
    """Stream results as they become available during stepper execution.
    
    Functional-style streaming that yields results immediately as branches
    complete, without waiting for full graph execution. Results are POPPED
    from stash as they're yielded, preventing memory buildup in looped graphs.
    
    IMPORTANT: Only yields when new results are added to stash (i.e., when
    execution reaches a leaf node or branch end). Does NOT yield during
    intermediate node execution.
    
    Args:
        stepper: A StepperC instance to stream from
        unwrap: If True (default), extract values using ArgsPack.flat().
    
    Yields:
        Result values as they become available. Order depends on
        execution path and may not be deterministic.
    
    Note:
        Results are removed from stash after yielding. This prevents
        memory growth in looped/cyclic graphs. After streaming completes,
        stash will be empty unless execution is interrupted.
    
    Example:
        >>> # Functional style
        >>> s = g.stepper()
        >>> for result in stream(s):
        ...     print(f"Got: {result}")
        
        >>> # OOP style (using StepperC.stream())
        >>> for result in s.stream():
        ...     print(f"Got: {result}")
    """
    ok = 1 
    while ok:
        # Execute one step
        rows = stepper.step()
    
        # Check if any new results appeared in stash
        if len(stepper.stash) == 0:
            continue

        # Pop all current results from stash (use .pop() for efficiency)
        # Create snapshot of nodes to avoid dict size change during iteration
        for node in tuple(stepper.stash.keys()):
            # Pop the entire tuple of results for this node
            akw_tuple = stepper.stash.pop(node)  
            # Yield each result for this node
            for akw in akw_tuple:
                value = akw.flat() if unwrap else akw
                yield value
        # Stop when no more rows to process
        ok = len(rows)


class StepperIterator(object):
    """Iterator wrapper for StepperC that enables Python iteration protocol.
    
    Yields successive row sets from the stepper until the graph execution
    completes (rows become empty). Each yielded value is a tuple of 
    (next_caller, argspack) pairs representing the current execution frontier.
    
    Example:
        >>> g = Graph()
        >>> g.connect(f.add_1, f.add_2, f.add_3)
        >>> s = g.stepper()
        >>> s.prepare(f.add_1, akw=argspack(10))
        >>> for rows in s.iterator():
        ...     print(len(rows))  # prints row count per step
    """
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
    # When True, enables row_concat() to merge multiple incoming rows targeting the same merge_node
    concat_aware = False  
    # When True, stores branch-end results in stash; when False, returns rows with None as next caller
    stash_ends = True
    initiate = INITIATE_DISTRIBUTED  # INITIATE_DISTRIBUTED (default) or INITIATE_UNIFIED

    def __init__(self, graph, rows=None):
        self.graph = graph
        self.run = 1

        self.reset_stash()

        self.start_nodes = None
        self.start_akw = None
        self.rows = rows

    def reset_stash(self):
        self.stash = defaultdict(tuple) 

    def prepare(self, *funcs, akw, initiate=INITIATE_DISTRIBUTED):
        """Prepare the stepper with the start nodes and the initial argument
        pack. Next iterations will yield steps.
        
        Args:
            *funcs: Start node(s) for execution
            akw: Initial argument pack
            initiate: Initial execution mode
                INITIATE_DISTRIBUTED (default) - Call start node once per connection (edge-centric)
                INITIATE_UNIFIED - Call start node once, then distribute result to all connections
        """
        self.start_nodes = funcs
        self.start_akw = akw
        self.initiate = initiate

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
            raise StepperException('start_nodes is None')
        
        # Initialize rows if needed - check initiate mode for first step
        if rows is None and self.rows is None:
            # First step - use appropriate expansion based on initiate mode
            func = expand_unified if self.initiate == INITIATE_UNIFIED else expand_distributed
            # Default INITIATE_DISTRIBUTED mode - standard edge-centric expansion
            self.rows = func(self, st_nodes, self.start_akw)
        else:
            self.rows = rows or self.rows

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

    def call_one_fallthrough(self, thing, akw): # NOSONAR(S1172)
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
        a_to_b_conns = get_connections(self.graph, edge, akw=akw)
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
        a_to_b_conns = get_connections(self.graph, func, akw=akw)
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
        b_conns = get_connections(self.graph, partial_conn.b, akw=akw)

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
        a_to_b_conns = get_connections(self.graph, unit, akw=akw)

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
        """The end_branch method is default hanlder when no branches exist on the stepper chain.
        This captures the result from the last call, and stores it in the stash for later retrieval.

        return an empty tuple if the stash branch stash ends, else return a tuple of tuples (a row set)
        with no destination node. 
        """
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

    def get_results(self, unwrap=True):
        """Get all results as a flat list.
        
        This method provides a simple way to access all results from the stash
        without manually unwrapping ArgsPack objects or iterating through the
        defaultdict structure.
        
        Args:
            unwrap: If True (default), extract values using ArgsPack.flat().
                   If False, return ArgsPack objects directly.
        
        Returns:
            List of result values. When unwrap=True, uses ArgsPack.flat() which returns:
            - Single positional arg: the value itself
            - Multiple positional args: tuple of args
            - Only kwargs: dict
            - Both args and kwargs: tuple of (args, kwargs)
            - Nothing: None
        
        Example:
            >>> s = g.stepper(node, 10)
            >>> while s.step(): pass
            >>> s.get_results()
            [60, 42, 100]
        """
        results = []
        for akw_tuple in self.stash.values():
            for akw in akw_tuple:
                v = akw.flat() if unwrap else akw
                results.append(v)
        return results

    def get_result(self, unwrap=True, default=None):
        """Get the first result (for single-endpoint graphs).
        
        Convenience method for the common case where you expect a single result
        from graph execution. Returns the first available result or a default value.
        
        Args:
            unwrap: If True (default), extract value using ArgsPack.flat().
            default: Value to return if no results exist (default: None).
        
        Returns:
            The first result value (unwrapped via .flat() if unwrap=True), 
            or default if no results exist.
        
        Example:
            >>> s = g.stepper(node, 10)
            >>> while s.step(): pass
            >>> result = s.get_result()
            60
        """
        results = self.get_results(unwrap=unwrap)
        return results[0] if results else default

    def get_results_dict(self, key='name', unwrap=True):
        """Get results organized by node attribute.
        
        Useful for graphs with multiple endpoints where you want to distinguish
        which node produced which results. Results are grouped by a node attribute.
        
        Args:
            key: Node attribute to use as dict key ('name', 'id', or callable).
                 If callable, will be called with the node to generate the key.
            unwrap: If True (default), extract values using ArgsPack.flat().
                   If False, return ArgsPack objects directly.
        
        Returns:
            Dict mapping node key to list of results from that node.
            When unwrap=True, results are extracted via ArgsPack.flat().
        
        Example:
            >>> s = g.stepper(node, 10)
            >>> while s.step(): pass
            >>> s.get_results_dict()
            {'add_30': [60], 'handler_a': [42], 'handler_b': [100]}
            
            >>> s.get_results_dict(key='id')
            {140234567890: [60], 140234567891: [42]}
            
            >>> s.get_results_dict(key=lambda n: n.func.__name__)
            {'add_30': [60], 'handler': [42, 100]}
        """
        results_dict = {}
        for node, akw_tuple in self.stash.items():
            # Handle both Unit and PartialConnection objects
            actual_node = getattr(node, 'b', node)
            
            # Get node key
            node_key = key(actual_node) if callable(key) else getattr(actual_node, key, str(actual_node))
            
            # Extract results for this node
            node_results = [akw.flat() if unwrap else akw for akw in akw_tuple]
            results_dict[node_key] = node_results
            
        return results_dict

    def has_results(self):
        """Check if any results exist in the stash.
        
        Returns:
            True if stash contains results, False otherwise.
        
        Example:
            >>> s = g.stepper(node, 10)
            >>> s.has_results()
            False
            >>> while s.step(): pass
            >>> s.has_results()
            True
        """
        return len(self.stash) > 0

    def result_count(self):
        """Count total number of results across all nodes.
        
        Returns:
            Total number of result values in the stash.
        
        Example:
            >>> s = g.stepper(node, 10)
            >>> while s.step(): pass
            >>> s.result_count()
            3
        """
        count = 0
        for akw_tuple in self.stash.values():
            count += len(akw_tuple)
        return count

    def stream(self, unwrap=True):
        """Stream results as they become available during execution.
        
        This is a convenience method that delegates to the standalone stream()
        function. Results are yielded immediately as branches complete, without
        waiting for full graph execution. Results are POPPED from stash as
        they're yielded, preventing memory buildup in looped graphs.
        
        IMPORTANT: Only yields when new results are added to stash (i.e., when
        execution reaches a leaf node or branch end). Does NOT yield during
        intermediate node execution.
        
        Args:
            unwrap: If True (default), extract values using ArgsPack.flat().
        
        Yields:
            Result values as they become available. Order depends on
            execution path and may not be deterministic.
        
        Note:
            Results are removed from stash after yielding. This prevents
            memory growth in looped/cyclic graphs. After streaming completes,
            stash will be empty unless execution is interrupted.
        
        Example:
            >>> for result in s.stream():
            ...     print(f"Got: {result}")
        """
        return stream(self, unwrap=unwrap)
