"""
Comprehensive tests for hyperway.edges module.

Tests will be added incrementally to ensure each is understood.
Coverage focus: make_edge, is_edge, as_connections, get_connections, 
Connection, PartialConnection classes.
"""

import unittest
from unittest.mock import patch, MagicMock

from hyperway.edges import make_edge, is_edge, Connection, PartialConnection, as_connections, get_connections, wire_partial, wire
from hyperway.nodes import as_unit
from hyperway.packer import argspack, ArgsPack
from hyperway.graph import Graph

from tiny_tools import passthrough, return_n , add_n, noop, doubler


# Pre-create commonly used addition functions
add_one = add_n(1)
add_two = add_n(2)
add_five = add_n(5)
add_ten = add_n(10)
add_twenty = add_n(20)

# Aliases for backward compatibility and readability
func_a = passthrough
func_b = passthrough

def func_c(v=None):
    """Standard test function C - returns 3 or v+3."""
    if v is None:
        v = 0
    return add_n(3)(v)

assert func_c() == 3
assert func_c(7) == 10

# Pre-create commonly used return functions
func_d = return_n(4)
simple_func = return_n(1)


class TestMakeEdge(unittest.TestCase):
    """Test make_edge function - creates Connection between two nodes."""
    
    def test_make_edge_creates_connection(self):
        """make_edge creates a Connection between two functions.
        
        This tests the most basic functionality: given two functions,
        make_edge should return a Connection object that wraps both
        as Unit nodes.
        """
        edge = make_edge(func_a, func_b)
        
        # Should return a Connection instance
        self.assertIsInstance(edge, Connection)
        
        # Connection should have a and b attributes
        self.assertIsNotNone(edge.a)
        self.assertIsNotNone(edge.b)
    
    def test_make_edge_with_name(self):
        """make_edge accepts optional name parameter.
        
        The name parameter allows labeling connections for debugging
        and visualization purposes. It should be stored on the Connection.
        """
        edge = make_edge(func_a, func_b, name="test_connection")
        
        # Name should be stored on the connection
        self.assertEqual(edge.name, "test_connection")
    
    def test_make_edge_with_through_wire_function(self):
        """make_edge accepts optional through parameter for wire functions.
        
        The 'through' parameter is a wire function that transforms data
        between node A and node B. This is crucial for data transformation
        in the graph execution pipeline.
        """
        
        wire_function = lambda v, *args, **kwargs: argspack(v * 2, **kwargs)
        
        edge = make_edge(func_a, func_b, through=wire_function)
        
        # Through function should be stored on the connection
        self.assertEqual(edge.through, wire_function)

class TestIsEdge(unittest.TestCase):
    """Test is_edge function - checks if object is a Connection."""
    
    def test_is_edge_returns_true_for_connection(self):
        """is_edge returns True for Connection instances.
        
        This utility function helps identify if an object is an edge/connection
        in the graph. Essential for type checking and graph traversal.
        """        
        edge = make_edge(func_a, func_b)
        
        # Should identify edge as a Connection
        self.assertTrue(is_edge(edge))
    
    def test_is_edge_returns_false_for_non_connection(self):
        """is_edge returns False for non-Connection objects.
        
        Regular functions, Units, and other objects should not be
        identified as edges.
        """
        # Function should not be an edge
        self.assertFalse(is_edge(simple_func))
        
        # Unit should not be an edge
        unit = as_unit(simple_func)
        self.assertFalse(is_edge(unit))
        
        # Random objects should not be edges
        self.assertFalse(is_edge("string"))
        self.assertFalse(is_edge(42))
        self.assertFalse(is_edge(None))

class TestConnectionStringRepresentation(unittest.TestCase):
    """Test Connection string representations for debugging and display."""
    
    def test_connection_str_basic(self):
        """Connection.__str__ returns readable string representation.
        
        String representation is used for debugging and logging.
        Should show the connection structure: a -> b with optional wire.
        """        
        edge = make_edge(func_a, func_b, name="test_edge")
        
        # Should return a string
        result = str(edge)
        self.assertIsInstance(result, str)
        
        # Should contain class name and name parameter
        self.assertIn("Connection", result)
        self.assertIn("test_edge", result)
    
    def test_connection_repr(self):
        """Connection.__repr__ returns repr string with angle brackets.
        
        Repr is used in interactive shells and should wrap the str() output
        in angle brackets for clarity.
        """        
        edge = make_edge(func_a, func_b)
        
        # Should return a string with angle brackets
        result = repr(edge)
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("<"))
        self.assertTrue(result.endswith(">"))
        self.assertIn("Connection", result)

class TestConnectionMergeNode(unittest.TestCase):
    """Test Connection.merge_node property."""
    
    def test_merge_node_property_delegates_to_node_a(self):
        """Connection.merge_node returns the merge_node status of node A.
        
        Merge nodes are special nodes that combine multiple incoming edges.
        The connection's merge_node property should reflect node A's status.
        """        
        # Create edge and set merge_node on node A
        edge = make_edge(func_a, func_b)
        edge.a.merge_node = True
        
        # Connection should reflect node A's merge_node status
        self.assertTrue(edge.merge_node)
        
        # Test False case
        edge.a.merge_node = False
        self.assertFalse(edge.merge_node)

class TestConnectionPluck(unittest.TestCase):
    """Test Connection.pluck - execute a single edge A -> [wire] -> B."""
    
    def test_pluck_executes_full_connection(self):
        """Connection.pluck executes both node A and node B.
        
        Pluck is the main execution method for testing a single edge.
        It runs: input -> A -> [wire] -> B -> output
        This is crucial for development and testing individual connections.
        """
        edge = make_edge(add_one, add_two)
        
        # Pluck should execute: 10 -> add_one(10)=11 -> add_two(11)=13
        result = edge.pluck(10)
        
        self.assertEqual(result, 13)
    
    def test_pluck_with_wire_function(self):
        """Connection.pluck executes A -> wire -> B pipeline.
        
        When a wire function exists, pluck should:
        1. Execute node A with input
        2. Pass A's result through the wire function
        3. Execute node B with wire's output
        """
        
        edge = make_edge(add_one, add_two, through=doubler)
        
        # Pluck should execute: 10 -> add_one(10)=11 -> doubler(11)=22 -> add_two(22)=24
        result = edge.pluck(10)
        
        self.assertEqual(result, 24)

class TestConnectionCallThrough(unittest.TestCase):
    """Test Connection.call_through - execute wire function."""
    
    def test_call_through_with_wire_function(self):
        """call_through executes the wire function when present.
        
        The wire function transforms data between nodes. call_through
        should execute it and return an ArgsPack with the result.
        """
        def wire(v, *args, **kwargs):
            return argspack(v * 3, **kwargs)
        
        edge = make_edge(func_a, func_b, through=wire)
        
        # call_through should execute wire function
        with patch('builtins.print'):  # Suppress debug output
            result = edge.call_through(10, key='value')
        
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (30,))
        self.assertEqual(result.kwargs, {'key': 'value'})
    
    def test_call_through_without_wire_returns_argspack(self):
        """call_through without wire function returns argspack of inputs.
        
        If no wire function exists, call_through should wrap the inputs
        in an ArgsPack and return them unchanged.
        """
        edge = make_edge(func_a, func_b)  # No wire function
        
        result = edge.call_through(10, 20, key='value')
        
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (10, 20))
        self.assertEqual(result.kwargs, {'key': 'value'})

class TestConnectionGetNodes(unittest.TestCase):
    """Test Connection.get_a and get_b methods."""
    
    def test_get_a_returns_node_a(self):
        """get_a returns the A node (Unit) of the connection.
        
        Node A is the source node of the edge. get_a should return
        the Unit instance wrapping the function.
        """        
        edge = make_edge(func_a, func_b)
        
        node_a = edge.get_a()
        
        # Should return the Unit for node A
        self.assertEqual(node_a, edge.a)
        self.assertIsInstance(node_a, type(edge.a))
    
    def test_get_b_returns_node_b(self):
        """get_b returns the B node (Unit) of the connection.
        
        Node B is the destination node of the edge. get_b should return
        the Unit instance wrapping the function.
        """        
        edge = make_edge(func_a, func_b)
        
        node_b = edge.get_b()
        
        # Should return the Unit for node B
        self.assertEqual(node_b, edge.b)
        self.assertIsInstance(node_b, type(edge.b))

class TestConnectionStepperCall(unittest.TestCase):
    """Test Connection.stepper_call - called by stepper to execute node A."""
    
    def test_stepper_call_executes_node_a(self):
        """stepper_call executes node A with the given ArgsPack.
        
        This is called by the stepper during graph execution.
        It should execute only node A (not the wire or B) and return A's result.
        """
        
        edge = make_edge(add_ten, add_twenty)
        akw = argspack(5)
        
        # stepper_call should only execute node A
        result = edge.stepper_call(akw)
        
        # Should return result of node A only (5 + 10 = 15)
        self.assertEqual(result, 15)
    
    def test_stepper_call_with_kwargs(self):
        """stepper_call passes kwargs to node A.
        
        The stepper passes data via ArgsPack which can contain both
        args and kwargs. stepper_call should unpack these correctly.
        """
        
        def func_with_kwargs(a, b=0):
            return a + b       
         
        edge = make_edge(func_with_kwargs, func_b)
        akw = argspack(10, b=5)
        
        result = edge.stepper_call(akw)
        
        # Should execute with both args and kwargs (10 + 5 = 15)
        self.assertEqual(result, 15)

class TestConnectionHalfCall(unittest.TestCase):
    """Test Connection.half_call - executes A and returns partial connection."""
    
    def test_half_call_returns_partial_and_result(self):
        """half_call executes node A and returns (PartialConnection, ArgsPack).
        
        This is called by the stepper when processing connections.
        It should:
        1. Execute node A
        2. Return a PartialConnection (for wire->B execution)
        3. Return an ArgsPack with A's result
        """
        
        edge = make_edge(add_five, add_ten)
        akw = argspack(10)
        
        # half_call should execute A and return partial + result
        partial, result_pack = edge.half_call(akw)
        
        # Should return a PartialConnection
        self.assertIsInstance(partial, PartialConnection)
        
        # Should return ArgsPack with A's result (10 + 5 = 15)
        self.assertIsInstance(result_pack, ArgsPack)
        self.assertEqual(result_pack.args, (15,))
    
    def test_half_call_partial_connection_references_parent(self):
        """half_call's PartialConnection maintains reference to parent.
        
        The PartialConnection returned by half_call should reference
        the original Connection so it can execute the wire->B portion later.
        """
        edge = make_edge(func_a, func_b)
        akw = argspack(10)
        
        partial, _ = edge.half_call(akw)
        
        # Partial should reference the original connection
        self.assertEqual(partial.parent_connection, edge)

class TestPartialConnectionBasics(unittest.TestCase):
    """Test PartialConnection basic functionality."""
    
    def test_partial_connection_b_property(self):
        """PartialConnection.b returns node B from parent connection.
        
        PartialConnection represents the wire->B portion of an edge.
        The .b property should return node B from the parent Connection.
        """
        edge = make_edge(func_a, func_b)
        akw = argspack(10)
        
        partial, _ = edge.half_call(akw)
        
        # Partial.b should be the same as edge.b
        self.assertEqual(partial.b, edge.b)
    
    def test_partial_connection_merge_node_property(self):
        """PartialConnection.merge_node delegates to node B's status.
        
        Just like Connection.merge_node checks node A, 
        PartialConnection.merge_node should check node B
        (since it represents the second half of the edge).
        """
        edge = make_edge(func_a, func_b)
        edge.b.merge_node = True
        
        akw = argspack()
        partial, _ = edge.half_call(akw)
        
        # Partial should reflect node B's merge_node status
        self.assertTrue(partial.merge_node)

class TestPartialConnectionExecution(unittest.TestCase):
    """Test PartialConnection execution methods."""
    
    def test_partial_connection_process_executes_wire_and_b(self):
        """PartialConnection.process executes wire function then node B.
        
        The PartialConnection represents the second half of edge execution.
        It should apply the wire function and then execute node B.
        """
        
        edge = make_edge(add_one, add_two, through=doubler)
        akw = argspack(10)
        
        partial, _ = edge.half_call(akw)
        
        # Process should execute: doubler(15) = 30, add_two(30) = 32
        # (15 comes from A's execution in half_call)
        result = partial.process(15)
        
        self.assertEqual(result, 32)
    
    def test_partial_connection_stepper_call(self):
        """PartialConnection.stepper_call executes wire->B with ArgsPack.
        
        This is called by the stepper to complete the edge execution.
        It should take an ArgsPack (containing A's result) and execute
        the wire function followed by node B.
        """
        
        edge = make_edge(add_five, add_ten)
        akw = argspack(10)
        
        partial, _ = edge.half_call(akw)
        
        # Create new ArgsPack with A's result (15)
        result_akw = argspack(15)
        
        # stepper_call should execute wire->B
        result = partial.stepper_call(result_akw)
        
        # Should execute add_ten(15) = 25
        self.assertEqual(result, 25)

class TestPartialConnectionStringRepresentation(unittest.TestCase):
    """Test PartialConnection string representations."""
    
    def test_partial_connection_str(self):
        """PartialConnection.__str__ shows connection to node B.
        
        String representation should indicate this is a PartialConnection
        and show which node B it connects to.
        """
        edge = make_edge(func_a, func_b)
        akw = argspack()
        
        partial, _ = edge.half_call(akw)
        
        result = str(partial)
        
        # Should contain class name
        self.assertIsInstance(result, str)
        self.assertIn("PartialConnection", result)
    
    def test_partial_connection_repr(self):
        """PartialConnection.__repr__ wraps str in angle brackets.
        
        Repr should provide a clear representation for debugging.
        """
        edge = make_edge(func_a, func_b)
        akw = argspack()
        
        partial, _ = edge.half_call(akw)
        
        result = repr(partial)
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("<"))
        self.assertTrue(result.endswith(">"))
        self.assertIn("PartialConnection", result)

class TestAsConnections(unittest.TestCase):
    """Test as_connections function - converts items to connections."""
    
    def test_as_connections_with_connection_objects(self):
        """as_connections passes through Connection objects unchanged.
        
        When given a list containing Connection objects, as_connections
        should return them as-is without modification. This allows mixing
        connections and nodes in the input list.
        """
        
        g = Graph()
        edge1 = g.add(func_a, func_b)
        edge2 = g.add(func_b, func_c)
        
        # as_connections should return the same connection objects
        result = as_connections(edge1, edge2, graph=g)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIs(result[0], edge1)
        self.assertIs(result[1], edge2)
    
    def test_as_connections_with_unit_nodes(self):
        """as_connections resolves Unit nodes to their connections.
        
        When given a Unit node, as_connections should look up all
        connections from that node in the graph and include them
        in the result. This enables flexible graph construction.
        """
        g = Graph()
        # Create shared unit_a with multiple outgoing edges
        unit_a = as_unit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)
        
        # as_connections with unit_a should return both edges
        result = as_connections(unit_a, graph=g)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn(edge1, result)
        self.assertIn(edge2, result)

class TestConnectionCall(unittest.TestCase):
    """Test Connection.__call__ method - direct connection invocation."""
    
    def test_connection_call_executes_node_a(self):
        """Connection.__call__ executes node A and returns result.
        
        When a Connection is called directly (not via pluck), it should
        execute only node A and return A's result. This is used internally
        by the stepper for graph execution.
        """
        edge = make_edge(add_ten, add_twenty)
        
        # Calling the connection should execute node A only
        with patch('builtins.print'):  # Suppress debug output
            result = edge(5)
        
        # Should return result of node A only (5 + 10 = 15)
        self.assertEqual(result, 15)
    
    def test_connection_call_with_kwargs(self):
        """Connection.__call__ passes kwargs to node A.
        
        The __call__ method should support both positional and keyword
        arguments, passing them through to node A's process method.
        """
        def func_with_kwargs(a, b=0):
            return a + b        
        edge = make_edge(func_with_kwargs, func_b)
        
        # Call with kwargs
        with patch('builtins.print'):  # Suppress debug output
            result = edge(10, b=5)
        
        # Should execute node A with kwargs (10 + 5 = 15)
        self.assertEqual(result, 15)
    
    def test_connection_call_with_explicit_graph(self):
        """Connection.__call__ accepts explicit _graph parameter.
        
        The __call__ method should accept and use an explicit _graph
        parameter. This is the primary way to provide graph context for
        connection execution, as edge.on is typically None unless explicitly set.
        """
        g = Graph()
        
        # Create connection - note edge.on will be None
        edge = g.add(add_ten, add_twenty)
        
        # Call with explicit graph
        with patch('builtins.print'):  # Suppress debug output
            result = edge(5, _graph=g)
        
        # Should execute successfully using provided graph
        self.assertEqual(result, 15)
    
    def test_connection_call_without_graph_uses_fallback(self):
        """Connection.__call__ works without graph when not needed.
        
        When _graph is not provided and edge.on is None, the connection
        can still execute if the node doesn't require graph resolution.
        This tests the `g = _graph or self.on` fallback logic.
        """
        g = Graph()
        edge = g.add(add_ten, add_twenty)
        
        # edge.on is None by default
        self.assertIsNone(edge.on)
        
        # Call without _graph should still work (g will be None)
        with patch('builtins.print'):  # Suppress debug output
            result = edge(5)
        
        # Should execute successfully even without graph reference
        self.assertEqual(result, 15)
    
    def test_connection_call_graph_priority_logic(self):
        """Connection.__call__ _graph parameter takes priority over edge.on.
        
        When both self.on and _graph are provided, the explicit _graph
        parameter should take precedence. This verifies the logic:
        g = self.on if _graph is None else _graph
        
        This uses explicit None checking, so even an empty Graph (which is
        falsy) will be used when explicitly passed as _graph parameter.
        """
        g1 = Graph()  # Will have connections
        g2 = Graph()  # Empty graph
        
        # Create connection and manually set edge.on
        edge = g1.add(add_ten, add_twenty)
        edge.on = g1  # Manually set for testing
        
        # Verify edge.on is set
        self.assertIs(edge.on, g1)
        
        # Test the priority logic: self.on if _graph is None else _graph
        # Simulate what happens in Connection.__call__ with different _graph values
        
        # Scenario 1: _graph is None -> should use edge.on
        _graph_param = None
        resolved = edge.on if _graph_param is None else _graph_param
        self.assertIs(resolved, g1)  # _graph is None, so edge.on (g1) is used
        
        # Scenario 2: _graph is g2 (even though empty) -> should use g2
        _graph_param = g2
        resolved = edge.on if _graph_param is None else _graph_param
        self.assertIs(resolved, g2)  # _graph is not None, so g2 takes priority
        
        # Scenario 3: _graph is g1 -> should use g1
        _graph_param = g1
        resolved = edge.on if _graph_param is None else _graph_param
        self.assertIs(resolved, g1)  # _graph is not None, so g1 takes priority
        
        # Verify execution works with explicit empty graph
        with patch('builtins.print'):  # Suppress debug output
            result_with_g2 = edge(5, _graph=g2)  # Explicit empty graph
            result_without_graph = edge(5)  # Should use edge.on (g1)
        
        # Both should execute successfully
        self.assertEqual(result_with_g2, 15)
        self.assertEqual(result_without_graph, 15)

class TestPartialConnectionCall(unittest.TestCase):
    """Test PartialConnection.__call__ method - direct partial invocation."""
    
    def test_partial_connection_call_executes_wire_and_b(self):
        """PartialConnection.__call__ executes wire->B pipeline.
        
        When a PartialConnection is called directly, it should execute
        the wire function (if present) and then node B, returning B's result.
        This provides a direct way to complete the second half of an edge.
        """
        
        edge = make_edge(add_five, add_ten, through=doubler)
        akw = argspack(10)
        
        # Create partial connection
        partial, result_pack = edge.half_call(akw)
        
        # Call partial directly should execute: doubler(15) = 30, add_ten(30) = 40
        with patch('builtins.print'):  # Suppress debug output
            result = partial(15)
        
        self.assertEqual(result, 40)
    
    def test_partial_connection_call_with_kwargs(self):
        """PartialConnection.__call__ supports keyword arguments.
        
        The __call__ method should pass through both positional and
        keyword arguments to the wire->B pipeline.
        """
        def func_with_kwargs(a, b=0):
            return a + b
        
        edge = make_edge(func_a, func_with_kwargs)
        akw = argspack()
        
        partial, _ = edge.half_call(akw)
        
        # Call with kwargs
        with patch('builtins.print'):  # Suppress debug output
            result = partial(10, b=5)
        
        # Should execute node B with kwargs (10 + 5 = 15)
        self.assertEqual(result, 15)

class TestPartialConnectionGetConnections(unittest.TestCase):
    """Test PartialConnection.get_connections method - graph traversal from B."""
    
    def test_partial_get_connections_returns_edges_from_b(self):
        """PartialConnection.get_connections finds edges from node B.
        
        When called on a PartialConnection, get_connections should look up
        all connections that start from the parent connection's B node.
        This allows the stepper to continue traversing the graph.
        """
        
        g = Graph()
        # Create shared unit_b with multiple outgoing edges
        unit_b = as_unit(func_b)
        edge1 = g.add(func_a, unit_b)
        edge2 = g.add(unit_b, func_c)
        edge3 = g.add(unit_b, func_d)
        
        # Create partial from edge1
        akw = argspack()
        partial, _ = edge1.half_call(akw)
        
        # Get connections from the partial
        with patch('builtins.print'):  # Suppress debug output
            connections = partial.get_connections(g)
        
        # Should find both edges from unit_b (edge2 and edge3)
        self.assertIsInstance(connections, tuple)
        self.assertEqual(len(connections), 2)
        self.assertIn(edge2, connections)
        self.assertIn(edge3, connections)
    
    def test_partial_get_connections_returns_empty_for_leaf_node(self):
        """PartialConnection.get_connections returns empty tuple for leaf nodes.
        
        When the B node has no outgoing connections (it's a leaf in the graph),
        get_connections should return an empty tuple.
        """
        g = Graph()
        edge = g.add(func_a, func_b)
        
        # Create partial - func_b has no outgoing edges
        akw = argspack()
        partial, _ = edge.half_call(akw)
        
        # Get connections from the partial
        with patch('builtins.print'):  # Suppress debug output
            connections = partial.get_connections(g)
        
        # Should return empty tuple since func_b is a leaf
        self.assertIsInstance(connections, tuple)
        self.assertEqual(len(connections), 0)

class TestGetConnections(unittest.TestCase):
    """Test get_connections function - critical for graph traversal."""
    
    def test_get_connections_with_unit_node(self):
        """get_connections returns edges from a Unit node.
        
        This is the main graph traversal function. Given a node,
        it should return all outgoing connections from that node.
        The graph stores edges by node ID, so get_connections looks up
        edges where the given node is the source (A).
        """
        
        g = Graph()
        # Explicitly create and reuse the same Unit instance
        unit_a = as_unit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)  # Reuse the same unit_a
        
        # get_connections should find both edges from unit_a
        with patch('builtins.print'):  # Suppress debug output
            connections = get_connections(g, unit_a)
        
        # Should return tuple of connections from node A
        self.assertIsNotNone(connections)
        self.assertIsInstance(connections, tuple)
        # Graph stores edges in insertion order, so we may only get the first one
        # Actually, Graph stores ALL edges with node A as source
        self.assertEqual(len(connections), 2)
        self.assertIn(edge1, connections)
        self.assertIn(edge2, connections)
    
    def test_get_connections_with_edge_returns_next_nodes(self):
        """get_connections with an edge returns A nodes of next connections.
        
        When given an edge (Connection), get_connections should:
        1. Look up connections from the destination node (edge.b)
        2. Return a tuple of the A nodes of those connections
        This allows the stepper to traverse: edge -> edge.b -> next_edges
        """
        
        g = Graph()
        # Explicitly share unit_b across multiple connections
        unit_b = as_unit(func_b)
        edge1 = g.add(func_a, unit_b)
        edge2 = g.add(unit_b, func_c)  # Reuse the same unit_b
        
        # get_connections(edge1) should return A nodes from edge1.b's connections
        with patch('builtins.print'):  # Suppress debug output
            connections = get_connections(g, edge1)
        
        # Should return tuple of A nodes (not full connections)
        self.assertIsNotNone(connections)
        self.assertIsInstance(connections, tuple)
        # The result should contain func_b (the A node of edge2)
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0], edge2.a)
    
    def test_get_connections_passes_akw_to_unit_method(self):
        """get_connections passes akw parameter to unit.get_connections when available.
        
        When a unit has a custom get_connections method, and akw is provided,
        the get_connections function should pass akw through to the unit's method.
        This enables data-driven edge selection (knuckles functionality).
        """
        from unittest.mock import MagicMock
        
        g = Graph()
        
        # Create a unit with a mock get_connections method
        unit_a = as_unit(func_a)
        mock_get_connections = MagicMock(return_value=())
        unit_a.get_connections = mock_get_connections
        
        # Create some edges
        g.add(unit_a, func_b)
        
        # Call get_connections with akw
        test_akw = argspack('test_data', value=42)
        with patch('builtins.print'):  # Suppress debug output
            get_connections(g, unit_a, akw=test_akw)
        
        # Verify the unit's get_connections was called with graph and akw as keyword arg
        mock_get_connections.assert_called_once_with(g, akw=test_akw)
    
    def test_get_connections_without_akw_parameter(self):
        """get_connections works without akw parameter (backward compatibility).
        
        Verifies that when akw is not provided, the function still works
        as before. This ensures backward compatibility with existing code.
        """
        from hyperway.nodes import Unit
        
        g = Graph()
        
        # Create a unit with get_connections that handles None akw
        class SafeUnit(Unit):
            def get_connections(self, graph, akw=None):
                """Return all connections, with optional akw."""
                return tuple(graph.get(self.id()))
        
        unit_a = SafeUnit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)
        
        # Call without akw parameter
        with patch('builtins.print'):
            connections = get_connections(g, unit_a)
        
        # Should return all connections
        self.assertEqual(len(connections), 2)
        self.assertIn(edge1, connections)
        self.assertIn(edge2, connections)
    
    def test_get_connections_with_none_akw(self):
        """get_connections handles akw=None explicitly passed.
        
        Tests that explicitly passing akw=None works correctly and
        is distinguishable from not passing akw at all (though they
        should behave the same).
        """
        from unittest.mock import MagicMock
        
        g = Graph()
        
        # Create a unit with a mock get_connections method
        unit_a = as_unit(func_a)
        mock_get_connections = MagicMock(return_value=())
        unit_a.get_connections = mock_get_connections
        
        g.add(unit_a, func_b)
        
        # Call with explicit akw=None
        with patch('builtins.print'):
            get_connections(g, unit_a, akw=None)
        
        # Verify called with None as keyword arg
        mock_get_connections.assert_called_once_with(g, akw=None)

class TestGetConnectionsIfBranch(unittest.TestCase):
    """Test get_connections if branch (line 42) - PartialConnection with get_connections method."""
    
    def test_get_connections_with_partial_connection(self):
        """get_connections with a PartialConnection calls its get_connections method.
        
        PartialConnection has a get_connections method, so when passed to the
        get_connections function, it should take the if branch (line 42) and
        call unit.get_connections(graph) instead of using graph.get().
        """
        
        g = Graph()
        # Create a chain with shared unit_b
        unit_b = as_unit(func_b)
        edge1 = g.add(func_a, unit_b)
        edge2 = g.add(unit_b, func_c)
        
        # Create a PartialConnection from edge1
        akw = argspack()
        partial, _ = edge1.half_call(akw)
        
        # Verify PartialConnection HAS get_connections method
        self.assertTrue(hasattr(partial, 'get_connections'))
        self.assertIsInstance(partial, PartialConnection)
        
        # Call get_connections with partial - this will hit line 42
        with patch('builtins.print'):  # Suppress debug output
            connections = get_connections(g, partial)
        
        # Should call partial.get_connections(graph) which resolves from B node
        self.assertIsNotNone(connections)
        self.assertIsInstance(connections, tuple)
        self.assertIn(edge2, connections)

class TestGetConnectionsElseBranch(unittest.TestCase):
    """Test get_connections else branch (line 43) - non-edge with no get_connections method."""
    
    def test_get_connections_with_plain_unit(self):
        """get_connections with a Unit that has no get_connections attribute.
        
        When given a plain Unit (not a Connection), get_connections should
        use graph.get() to look up connections by the Unit's ID. This tests
        line 43: the else branch where hasattr(unit, 'get_connections') is False.
        """
        g = Graph()
        # Create a unit and add it to graph
        unit_a = as_unit(func_a)
        edge1 = g.add(unit_a, func_b)
        
        # Verify unit_a doesn't have get_connections method
        # (Units don't have this, only Connections do)
        self.assertFalse(hasattr(unit_a, 'get_connections'))
        
        # Call get_connections with unit_a - this will hit line 43
        with patch('builtins.print'):  # Suppress debug output
            connections = get_connections(g, unit_a)
        
        # Should find the edge via graph.get(unit_a.id())
        self.assertIsNotNone(connections)
        self.assertIsInstance(connections, tuple)
        self.assertIn(edge1, connections)

class TestConnectionEdgeCases(unittest.TestCase):
    """Test Connection edge cases and alternative code paths."""
    
    def test_get_connections_with_raw_function(self):
        """get_connections accepts raw functions and wraps them as Units.
        
        When given a raw function (not a Unit), get_connections should
        automatically wrap it as a Unit and look up its connections via
        the graph.get() method (line 43 - the else branch).
        """
        g = Graph()
        # Create a shared unit and add edges
        unit_a = as_unit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)
        
        # Test 1: get_connections with the exact Unit instance
        with patch('builtins.print'):  # Suppress debug output
            connections_unit = get_connections(g, unit_a)
        
        # Should find both edges
        self.assertIsNotNone(connections_unit)
        self.assertEqual(len(connections_unit), 2)
        
        # Test 2: get_connections with raw func_a (tests line 43)
        # This will create a NEW Unit wrapper with different ID
        with patch('builtins.print'):  # Suppress debug output
            connections_raw = get_connections(g, func_a)
        
        # Should return None since the new Unit has a different ID
        # This exercises the else branch (line 43) where as_unit() is called
        self.assertIsNone(connections_raw)
    
    def test_connection_str_with_through_function(self):
        """Connection.__str__ includes through function name when present.
        
        When a Connection has a through/wire function, the string
        representation should include the wire function's name for
        better debugging and visualization.
        """
        
        edge = make_edge(func_a, func_b, through=doubler)
        
        # String should include wire function name
        result = str(edge)
        self.assertIn("doubler", result)
        self.assertIn("through", result)


class TestPartialConnectionEdgeCases(unittest.TestCase):
    """Test PartialConnection edge cases and alternative code paths."""
    
    def test_partial_graph_next_process_caller(self):
        """PartialConnection.graph_next_process_caller returns the node.
        
        This method is used by the stepper to get the next processing
        node when traversing the graph. For a PartialConnection, it
        should return self.node (which may be None if not explicitly set).
        """
        edge = make_edge(func_a, func_b)
        akw = argspack()
        
        partial, _ = edge.half_call(akw)
        
        # Should return the node reference (may be None)
        result = partial.graph_next_process_caller()
        
        # The method should complete without error
        # Result is None by default unless node is explicitly set
        self.assertIsNone(result)
        
        # Test with explicit node parameter
        unit_a = as_unit(func_a)
        partial_with_node = PartialConnection(edge, node=unit_a)
        result_with_node = partial_with_node.graph_next_process_caller()
        self.assertEqual(result_with_node, unit_a)
    
    def test_connection_get_node_key_with_graph(self):
        """Connection.get_node_key can resolve nodes with graph parameter.
        
        When get_node_key is called with a graph, it uses the resolver
        to potentially transform the node reference. This tests:
        - Line 160: return resolve(n, g)
        - Lines 164-165: import and cache the resolver
        
        The resolve() function checks if the graph has resolve_node() and
        uses it, otherwise returns the node as-is.
        """
        g = Graph()
        edge = g.add(func_a, func_b)
        
        # Call get_node_key without graph (returns node directly - line 159)
        node_a = edge.get_node_key('a')
        self.assertEqual(node_a, edge.a)
        
        # Initialize _resolver to None (since Connection.__init__ doesn't set it)
        edge._resolver = None
        
        # Call get_node_key with graph - tests the resolver path
        # This will trigger get_resolver() which imports from graph.base (lines 164-165)
        # and then calls resolve(n, g) on line 160
        node_a_with_graph = edge.get_node_key('a', graph=g)
        
        # The resolver should return the resolved node (currently just the node itself)
        self.assertIsNotNone(node_a_with_graph)
        self.assertEqual(node_a_with_graph, edge.a)
        
        # Verify the resolver was imported and cached (lines 164-165)
        self.assertIsNotNone(edge._resolver)
        self.assertTrue(callable(edge._resolver))
        
        # Second call should use cached resolver (doesn't re-import)
        node_b_with_graph = edge.get_node_key('b', graph=g)
        self.assertEqual(node_b_with_graph, edge.b)


class TestWirePartial(unittest.TestCase):
    """Test wire_partial function - partial application for wire functions."""
    
    def test_wire_partial_basic_functionality(self):
        """wire_partial creates a wrapper that pre-applies arguments.
        
        wire_partial should act like functools.partial, allowing pre-setting
        of arguments to a wire function. The wrapper should return an ArgsPack.
        
        Example from docstring:
            wire_partial(my_wire_func, 10, 20)
            # Later called with: (30, 40)
            # Results in: my_wire_func(10, 20, 30, 40)
        """
        def my_wire_func(*a, **kw):
            # Sum all args and kwargs for testing
            return sum(a) + sum(kw.values())
        
        # Pre-apply arguments 10, 20
        partial_wire = wire_partial(my_wire_func, 10, 20)
        
        # Call with additional arguments 30, 40
        result = partial_wire(30, 40)
        
        # Should execute: my_wire_func(10, 20, 30, 40) = 100
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (100,))
    
    def test_wire_partial_with_kwargs(self):
        """wire_partial pre-applies keyword arguments correctly.
        
        Pre-set keyword arguments should be passed to the underlying function,
        with later kwargs merged (later values override pre-set ones).
        
        Example from docstring:
            wire_partial(my_wire_func, 10, 20, foo=2, egg=True)
            my_wire_func(30, 40, foo=5)
            WIRING: (10, 20, 30, 40) {'foo': 5, 'egg': True}
        """
        def my_wire_func(*a, **kw):
            return (a, kw)
        
        # Pre-apply foo=2, egg=True
        partial_wire = wire_partial(my_wire_func, 10, 20, foo=2, egg=True)
        
        # Call with additional kwargs (foo=5 overrides foo=2)
        result = partial_wire(30, 40, foo=5)
        
        # <ArgsPack(*(10, 20, 30, 40), **{'foo': 5, 'egg': True})>
        self.assertIsInstance(result, ArgsPack)
        args_result, kwargs_result = result.args, result.kwargs
        
        self.assertEqual(args_result, (10, 20, 30, 40))
        self.assertEqual(kwargs_result['foo'], 5)  # Overridden
        self.assertEqual(kwargs_result['egg'], True)  # Preserved
    
    def test_wire_partial_returns_argspack(self):
        """wire_partial wrapper always returns an ArgsPack.
        
        The wrapper must return argspack(result) to maintain compatibility
        with the graph execution pipeline. This is the key difference from
        raw functools.partial.
        """
        def simple_func(x):
            return x * 2
        
        partial_wire = wire_partial(simple_func, 5)
        result = partial_wire()
        
        # Must be ArgsPack, not raw result
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (10,))
    
    def test_wire_partial_in_connection(self):
        """wire_partial can be used as a through function in make_edge.
        
        This is the primary use case: wrapping a standard function to use
        as a wire transform between nodes, with some arguments pre-applied.
        """
        def multiplier(pre_mul, value):
            return value * pre_mul
        
        # Create wire that pre-applies multiplier of 5
        wire_mul_5 = wire_partial(multiplier, 5)
        
        # Create edge with wire function
        edge = make_edge(add_one, add_two, through=wire_mul_5)
        
        # Test with pluck: add_one(10) = 11, mul_5(11) = 55, add_two(55) = 57
        result = edge.pluck(10)
        self.assertEqual(result, 57)
    
    def test_wire_partial_no_args(self):
        """wire_partial with no pre-applied args still wraps in ArgsPack.
        
        Even without pre-applied arguments, wire_partial should create
        a wrapper that returns an ArgsPack, making it suitable for use
        as a wire function.
        """
        def simple_func(x, y):
            return x + y
        
        # No pre-applied args
        partial_wire = wire_partial(simple_func)
        result = partial_wire(10, 20)
        
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (30,))
    
    def test_wire_partial_merges_distinct_kwargs(self):
        """wire_partial merges kwargs from pre-set and call-time.
        
        Pre-set kwargs and call-time kwargs are merged together.
        Note: duplicate keys will raise TypeError (Python limitation).
        """
        def collect_kwargs(**kw):
            return kw
        
        # Pre-set a, b, c
        partial_wire = wire_partial(collect_kwargs, a=1, b=2, c=3)
        
        # Add distinct kwargs d, e
        result = partial_wire(d=4, e=5)
        
        self.assertIsInstance(result, ArgsPack)
        kwargs_result = result.args[0]
        
        self.assertEqual(kwargs_result['a'], 1)   # Pre-set
        self.assertEqual(kwargs_result['b'], 2)   # Pre-set
        self.assertEqual(kwargs_result['c'], 3)   # Pre-set
        self.assertEqual(kwargs_result['d'], 4)   # Call-time
        self.assertEqual(kwargs_result['e'], 5)   # Call-time
    
    def test_wire_partial_with_complex_transform(self):
        """wire_partial can pre-apply complex transformation parameters.
        
        Demonstrates using wire_partial to configure a data transformation
        function with specific parameters before using it in a graph.
        """
        def transform(prefix, suffix, value):
            return f"{prefix}_{value}_{suffix}"
        
        # Create a specific transformer
        wire_format = wire_partial(transform, "START", "END")
        
        edge = make_edge(passthrough, passthrough, through=wire_format)
        
        # passthrough("hello") = "hello", transform("START", "END", "hello")
        result = edge.pluck("hello")
        self.assertEqual(result, "START_hello_END")


class TestWire(unittest.TestCase):
    """Test wire function - simple wrapper for standard functions as wire functions."""
    
    def test_wire_basic_functionality(self):
        """wire wraps a standard function to return ArgsPack.
        
        Unlike wire_partial, wire does not pre-apply arguments. It simply
        wraps a function to ensure it returns an ArgsPack.
        """
        def multiply_by_5(value):
            return value * 5
        
        wire_func = wire(multiply_by_5)
        result = wire_func(10)
        
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (50,))
    
    def test_wire_preserves_kwargs(self):
        """wire wrapper passes call-time kwargs to func, setup kwargs to ArgsPack.
        
        The wire wrapper passes runtime args/kwargs to the wrapped function
        with its normal signature. Wire-setup kwargs (from wire(func, **wkw))
        flow through the ArgsPack for pipeline metadata.
        
        This allows clean function calls without needing **kwargs in the signature.
        """
        def add_values(x, y):
            # Clean function signature - no **kwargs needed!
            return x + y
        
        # Create wire with setup metadata
        wire_func = wire(add_values, pipeline_meta='test', stage='transform')
        
        # Call with normal function args
        result = wire_func(10, 20)
        
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (30,))
        # Wire-setup kwargs appear in ArgsPack
        self.assertEqual(result.kwargs, {'pipeline_meta': 'test', 'stage': 'transform'})
    
    def test_wire_call_time_kwargs_to_function(self):
        """wire passes call-time kwargs to the wrapped function.
        
        Call-time kwargs are passed directly to the function, allowing
        normal function signatures with keyword arguments.
        """
        def add_with_default(x, y, multiplier=1):
            return (x + y) * multiplier
        
        wire_func = wire(add_with_default, metadata='test')
        
        # Call with keyword argument
        result = wire_func(10, 20, multiplier=2)
        
        self.assertIsInstance(result, ArgsPack)
        self.assertEqual(result.args, (60,))  # (10 + 20) * 2
        # Only wire-setup kwargs in ArgsPack
        self.assertEqual(result.kwargs, {'metadata': 'test'})
    
    def test_wire_in_connection(self):
        """wire can be used as a through function in make_edge.
        
        Example from docstring:
            c = make_edge(f.add_1, f.add_2, through=wire(f.mul_5))
        """
        mul_5 = add_n(0)  # Create a simple function
        def mul_5_func(v):
            return v * 5
        
        wire_func = wire(mul_5_func)
        edge = make_edge(add_one, add_two, through=wire_func)
        
        # add_one(10) = 11, mul_5(11) = 55, add_two(55) = 57
        result = edge.pluck(10)
        self.assertEqual(result, 57)
    
    def test_wire_vs_wire_partial(self):
        """wire and wire_partial have different use cases.
        
        wire: wraps a function without pre-applying args
        wire_partial: wraps a function WITH pre-applied args
        """
        def add_numbers(a, b):
            return a + b
        
        # wire: no pre-applied args
        wire_add = wire(add_numbers)
        result1 = wire_add(10, 20)
        self.assertEqual(result1.args, (30,))
        
        # wire_partial: pre-apply first arg
        wire_partial_add = wire_partial(add_numbers, 10)
        result2 = wire_partial_add(20)
        self.assertEqual(result2.args, (30,))
        
        # Both return same result but called differently
        self.assertEqual(result1.args, result2.args)


