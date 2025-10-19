"""
Comprehensive tests for hyperway.edges module.

Tests will be added incrementally to ensure each is understood.
Coverage focus: make_edge, is_edge, as_connections, get_connections, 
Connection, PartialConnection classes.
"""

import unittest
from unittest.mock import patch, MagicMock

from hyperway.edges import make_edge, is_edge, Connection
from hyperway.nodes import as_unit


class TestMakeEdge(unittest.TestCase):
    """Test make_edge function - creates Connection between two nodes."""
    
    def test_make_edge_creates_connection(self):
        """make_edge creates a Connection between two functions.
        
        This tests the most basic functionality: given two functions,
        make_edge should return a Connection object that wraps both
        as Unit nodes.
        """
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
        edge = make_edge(func_a, func_b, name="test_connection")
        
        # Name should be stored on the connection
        self.assertEqual(edge.name, "test_connection")
    
    def test_make_edge_with_through_wire_function(self):
        """make_edge accepts optional through parameter for wire functions.
        
        The 'through' parameter is a wire function that transforms data
        between node A and node B. This is crucial for data transformation
        in the graph execution pipeline.
        """
        from hyperway.packer import argspack
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
        def wire_function(v, *args, **kwargs):
            # Wire function doubles the value
            return argspack(v * 2, **kwargs)
        
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
        edge = make_edge(func_a, func_b)
        
        # Should identify edge as a Connection
        self.assertTrue(is_edge(edge))
    
    def test_is_edge_returns_false_for_non_connection(self):
        """is_edge returns False for non-Connection objects.
        
        Regular functions, Units, and other objects should not be
        identified as edges.
        """
        def func():
            return 1
        
        # Function should not be an edge
        self.assertFalse(is_edge(func))
        
        # Unit should not be an edge
        unit = as_unit(func)
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        def add_one(v):
            return v + 1
        
        def add_two(v):
            return v + 2
        
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
        from hyperway.packer import argspack
        
        def add_one(v):
            return v + 1
        
        def add_two(v):
            return v + 2
        
        def doubler(v, *args, **kwargs):
            # Wire function doubles the value
            return argspack(v * 2, **kwargs)
        
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
        from hyperway.packer import argspack, ArgsPack
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
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
        from hyperway.packer import ArgsPack
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        from hyperway.packer import argspack
        
        def add_ten(v):
            return v + 10
        
        def add_twenty(v):
            return v + 20
        
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
        from hyperway.packer import argspack
        
        def func_with_kwargs(a, b=0):
            return a + b
        
        def func_b():
            return 0
        
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
        from hyperway.packer import argspack, ArgsPack
        from hyperway.edges import PartialConnection
        
        def add_five(v):
            return v + 5
        
        def add_ten(v):
            return v + 10
        
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
        from hyperway.packer import argspack
        from hyperway.edges import PartialConnection
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
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
        from hyperway.packer import argspack
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
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
        from hyperway.packer import argspack
        
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        from hyperway.packer import argspack
        
        def add_one(v):
            return v + 1
        
        def add_two(v):
            return v + 2
        
        def doubler(v, *args, **kwargs):
            return argspack(v * 2, **kwargs)
        
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
        from hyperway.packer import argspack
        
        def add_five(v):
            return v + 5
        
        def add_ten(v):
            return v + 10
        
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
        from hyperway.packer import argspack
        
        def func_a():
            return 1
        
        def func_b():
            return 2
        
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
        from hyperway.packer import argspack
        
        def func_a():
            return 1
        
        def func_b():
            return 2
        
        edge = make_edge(func_a, func_b)
        akw = argspack()
        
        partial, _ = edge.half_call(akw)
        
        result = repr(partial)
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("<"))
        self.assertTrue(result.endswith(">"))
        self.assertIn("PartialConnection", result)


class TestGetConnections(unittest.TestCase):
    """Test get_connections function - critical for graph traversal."""
    
    def test_get_connections_with_unit_node(self):
        """get_connections returns edges from a Unit node.
        
        This is the main graph traversal function. Given a node,
        it should return all outgoing connections from that node.
        The graph stores edges by node ID, so get_connections looks up
        edges where the given node is the source (A).
        """
        from hyperway.graph import Graph
        from hyperway.edges import get_connections
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
        def func_c(v):
            return v + 3
        
        g = Graph()
        edge1 = g.add(func_a, func_b)
        edge2 = g.add(func_a, func_c)  # func_a has two outgoing edges
        
        # get_connections should find both edges from func_a
        with patch('builtins.print'):  # Suppress debug output
            connections = get_connections(g, edge1.a)
        
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
        from hyperway.graph import Graph
        from hyperway.edges import get_connections
        
        def func_a(v):
            return v + 1
        
        def func_b(v):
            return v + 2
        
        def func_c(v):
            return v + 3
        
        g = Graph()
        edge1 = g.add(func_a, func_b)
        edge2 = g.add(func_b, func_c)  # Connection from B to C
        
        # get_connections(edge1) should return A nodes from edge1.b's connections
        with patch('builtins.print'):  # Suppress debug output
            connections = get_connections(g, edge1)
        
        # Should return tuple of A nodes (not full connections)
        self.assertIsNotNone(connections)
        self.assertIsInstance(connections, tuple)
        # The result should contain func_b (the A node of edge2)
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0], edge2.a)


if __name__ == '__main__':
    unittest.main()
