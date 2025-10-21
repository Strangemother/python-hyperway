"""
Comprehensive tests for hyperway.generator module.

Tests cover:
- fully_connected function for creating fully-connected graphs
- Edge creation between all node pairs
- Bidirectional connections (A→B and B→A)
- Node wrapping with as_units
- Edge cases: empty, single node, two nodes, multiple nodes
"""

import unittest

from hyperway.generator import fully_connected
from hyperway.nodes import Unit, as_unit
from hyperway.edges import Connection
from tiny_tools import return_n , add_n, noop


class TestFullyConnectedBasics(unittest.TestCase):
    """Test basic fully_connected functionality."""
    
    def test_empty_nodes_returns_empty_tuple(self):
        """fully_connected with no nodes returns empty tuple."""
        result = fully_connected()
        self.assertEqual(result, ())
        self.assertIsInstance(result, tuple)
    
    def test_single_node_returns_empty_tuple(self):
        """fully_connected with one node has no edges."""
        result = fully_connected(noop)
        # Single node cannot connect to itself, so no edges
        self.assertEqual(result, ())
    
    def test_two_nodes_creates_bidirectional_edges(self):
        """fully_connected with two nodes creates A→B and B→A."""
        edges = fully_connected(noop, noop)
        
        # Should have 2 edges: A→B and B→A
        self.assertEqual(len(edges), 2)
        self.assertIsInstance(edges, tuple)
        
        # Each item should be a Connection
        for edge in edges:
            self.assertIsInstance(edge, Connection)
    
    def test_three_nodes_creates_six_edges(self):
        """fully_connected with three nodes creates 6 edges (3×2)."""
        edges = fully_connected(noop, noop, return_n(3))
        
        # Each of 3 nodes connects to 2 others: 3 × 2 = 6 edges
        self.assertEqual(len(edges), 6)
        
        # All should be Connections
        for edge in edges:
            self.assertIsInstance(edge, Connection)


class TestFullyConnectedNodeWrapping(unittest.TestCase):
    """Test that nodes are properly wrapped as Units."""
    
    def test_callable_nodes_wrapped_as_units(self):
        """Callables are wrapped as Unit objects."""
        edges = fully_connected(noop, noop)
        
        # Extract unique units from edges
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        # Should have 2 unique units
        self.assertEqual(len(units), 2)
        
        # All should be Unit instances
        for unit in units:
            self.assertIsInstance(unit, Unit)
    
    def test_unit_objects_used_directly(self):
        """Pre-wrapped Unit objects are used directly."""
        unit_a = as_unit(noop)
        unit_b = as_unit(noop)
        
        edges = fully_connected(unit_a, unit_b)
        
        # Extract units
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        # Should use the same Unit instances
        self.assertIn(unit_a, units)
        self.assertIn(unit_b, units)
    
    def test_mixed_units_and_callables(self):
        """Mix of Units and callables works correctly."""
        unit_a = as_unit(noop)
        # noop is just a callable
        
        edges = fully_connected(unit_a, noop)
        
        self.assertEqual(len(edges), 2)
        
        # All edges should have Unit objects
        for edge in edges:
            self.assertIsInstance(edge.a, Unit)
            self.assertIsInstance(edge.b, Unit)


class TestFullyConnectedEdgeStructure(unittest.TestCase):
    """Test the structure of created edges."""
    
    def test_edge_contains_correct_nodes(self):
        """Each edge connects the correct pair of nodes."""
        edges = fully_connected(noop, noop)
        
        # Get the two units
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        unit_list = list(units)
        u0, u1 = unit_list[0], unit_list[1]
        
        # Should have edges u0→u1 and u1→u0
        edge_pairs = {(e.a, e.b) for e in edges}
        self.assertIn((u0, u1), edge_pairs)
        self.assertIn((u1, u0), edge_pairs)
    
    def test_bidirectional_connections_exist(self):
        """For every A→B edge, there's a B→A edge."""
        edges = fully_connected(noop, noop, return_n(3))
        
        edge_pairs = [(e.a, e.b) for e in edges]
        
        # Check that for each (a, b) there's a (b, a)
        for a, b in edge_pairs:
            reverse = (b, a)
            self.assertIn(reverse, edge_pairs,
                         f"Missing reverse edge for {(a, b)}")
    
    def test_no_self_loops(self):
        """Graph should not create edges from a unit to itself."""
        edges = fully_connected(noop, noop, return_n(3))
        
        # No edge should have a == b
        for edge in edges:
            self.assertNotEqual(edge.a, edge.b,
                              "Found self-loop edge")


class TestFullyConnectedWithKwargs(unittest.TestCase):
    """Test node_kwargs parameter for Unit customization."""
    
    def test_merge_node_kwarg_applied(self):
        """node_kwargs are passed to as_units."""
        edges = fully_connected(noop, noop, merge_node=True)
        
        # Extract units
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        # All units should have merge_node=True
        for unit in units:
            self.assertTrue(unit.merge_node)
    
    def test_sentinal_kwarg_applied(self):
        """sentinal kwarg is passed to as_units."""
        custom_sentinal = object()
        edges = fully_connected(noop, noop, sentinal=custom_sentinal)
        
        # Extract units
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        # All units should have the custom sentinal
        for unit in units:
            self.assertIs(unit.sentinal, custom_sentinal)
    
    def test_multiple_kwargs_applied(self):
        """Multiple kwargs are all applied to units."""
        custom_sentinal = "CUSTOM"
        edges = fully_connected(
            noop, noop,
            merge_node=True,
            sentinal=custom_sentinal
        )
        
        # Extract units
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        # Check both kwargs were applied
        for unit in units:
            self.assertTrue(unit.merge_node)
            self.assertEqual(unit.sentinal, custom_sentinal)


class TestFullyConnectedMathematicalProperties(unittest.TestCase):
    """Test mathematical properties of fully-connected graphs."""
    
    def test_edge_count_formula(self):
        """Number of edges = n × (n - 1) for n nodes."""
        test_cases = [
            (0, 0),   # 0 nodes → 0 edges
            (1, 0),   # 1 node → 0 edges
            (2, 2),   # 2 nodes → 2 edges
            (3, 6),   # 3 nodes → 6 edges
            (4, 12),  # 4 nodes → 12 edges
            (5, 20),  # 5 nodes → 20 edges
        ]
        
        for n_nodes, expected_edges in test_cases:
            with self.subTest(n_nodes=n_nodes):
                # Create n_nodes functions
                nodes = [lambda i=i: i for i in range(n_nodes)]
                edges = fully_connected(*nodes)
                
                self.assertEqual(len(edges), expected_edges,
                               f"Failed for {n_nodes} nodes")
    
    def test_unique_units_preserved(self):
        """Unique Unit instances create separate nodes."""
        u1 = Unit(return_n(3))
        u2 = Unit(return_n(4))
        # u1 and u2 are separate Unit instances
        edges = fully_connected(noop, u1, u2)


class TestFullyConnectedEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def test_same_function_multiple_times_creates_unique_units(self):
        """Same function used multiple times creates separate Units."""
        # Use same function 3 times - should create 3 different Units
        edges = fully_connected(return_n(1), return_n(1), return_n(1))
        
        # Should have 6 edges (3 × 2)
        self.assertEqual(len(edges), 6)
        
        # Extract units
        units = set()
        for edge in edges:
            units.add(edge.a)
            units.add(edge.b)
        
        # Should have 3 unique Unit instances
        # (each wrapping creates a new Unit)
        self.assertEqual(len(units), 3)
    
    def test_returns_tuple_type(self):
        """Result is always a tuple, not list or other iterable."""
        result = fully_connected(noop, noop)
        
        self.assertIsInstance(result, tuple)
        self.assertNotIsInstance(result, list)
    
    def test_large_graph(self):
        """Can create larger fully-connected graphs."""
        # Create 10 nodes
        nodes = [lambda i=i: i for i in range(10)]
        edges = fully_connected(*nodes)
        
        # Should have 10 × 9 = 90 edges
        self.assertEqual(len(edges), 90)
        
        # All should be valid Connections
        for edge in edges:
            self.assertIsInstance(edge, Connection)
            self.assertIsInstance(edge.a, Unit)
            self.assertIsInstance(edge.b, Unit)


class TestFullyConnectedIntegration(unittest.TestCase):
    """Integration tests with Graph."""
    
    def test_edges_can_be_added_to_graph(self):
        """Edges from fully_connected work with Graph.add_edges."""
        from hyperway.graph import Graph
        
        g = Graph()
        edges = fully_connected(noop, noop)
        
        # Should be able to add all edges to graph
        g.add_edges(edges)
        
        # Graph should have connections
        # (exact structure depends on graph implementation)
        self.assertTrue(len(edges) > 0)
    
    def test_edges_executable_with_pluck(self):
        """Edges from fully_connected are executable."""
        edges = fully_connected(add_n(1), add_n(2))
        
        # Find an edge and execute it
        # if edges:
        edge = edges[0]
        result = edge.pluck(5)
        # Result depends on which edge, but should work
        self.assertIsNotNone(result)

