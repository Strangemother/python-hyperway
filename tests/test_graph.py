"""
Comprehensive tests for hyperway.graph.graph module.

Tests cover:
- Graph class: add_edge, add_edges, get_nodes, connect, add, resolve
- Stepper integration: stepper_prepare, stepper_prepare_many, stepper
- Writer integration: write method
- UndirectedGraph class: bidirectional edge management
"""

import unittest
from unittest.mock import patch, MagicMock

from hyperway.graph import Graph
from hyperway.graph.graph import UndirectedGraph, FORWARD, BACKWARD
from hyperway.graph.base import is_graph, GraphBase, pairwise
from hyperway.edges import make_edge, Connection
from hyperway.nodes import as_unit, Unit
from hyperway.packer import argspack
from hyperway.stepper import StepperC

from tiny_tools import add_n 
from tiny_tools import pass_attribute_error

# Reusable test functions to reduce redundancy
def func_a(v=None):
    """Standard test function A - returns None or passes through value."""
    if v is None:
        return None
    return v

assert func_a() is None
assert func_a(None) is None
assert func_a(5) == 5

def func_b(v=None):
    """Standard test function B - returns None or passes through value."""
    return func_a(v)

assert func_b() is None
assert func_b(1) == 1


func_c = add_n(3)


def wire_func(v, *args, **kwargs):
    """Wire function that doubles the value."""
    return argspack(v * 2, **kwargs)

assert wire_func(4).args[0] == 8
assert wire_func(7, foo=200).kwargs['foo'] == 200

class TestGraphBasics(unittest.TestCase):
    """Test basic Graph functionality."""
    
    def test_graph_instantiation(self):
        """Graph can be instantiated."""
        g = Graph()
        self.assertIsInstance(g, Graph)
    
    def test_graph_with_tuple_default(self):
        """Graph(tuple) creates defaultdict with tuple factory."""
        g = Graph(tuple)
        self.assertIsInstance(g, Graph)
        # Accessing missing key returns empty tuple
        self.assertEqual(g['nonexistent'], ())


class TestGraphAddEdge(unittest.TestCase):
    """Test add_edge method."""
    
    def test_add_edge_single(self):
        """add_edge adds a connection to the graph."""
        g = Graph()
        
        edge = make_edge(func_a, func_b)
        g.add_edge(edge)
        
        # Edge should be stored by edge.id() and edge.a.id()
        self.assertIn(edge, g[edge.id()])
        self.assertIn(edge, g[edge.a.id()])
    
    def test_add_edge_stores_by_edge_id(self):
        """add_edge stores edge by its id."""
        g = Graph()
        
        edge = make_edge(func_a, func_b)
        edge_id = edge.id()
        
        g.add_edge(edge)
        
        # Should find edge by its ID
        self.assertIn(edge, g[edge_id])
    
    def test_add_edge_stores_by_node_a_id(self):
        """add_edge stores edge by node A's id."""
        g = Graph()
        
        edge = make_edge(func_a, func_b)
        node_a_id = edge.a.id()
        
        g.add_edge(edge)
        
        # Should find edge by node A's ID
        self.assertIn(edge, g[node_a_id])


class TestGraphAddEdges(unittest.TestCase):
    """Test add_edges method."""
    
    def test_add_edges_multiple(self):
        """add_edges adds multiple edges."""
        g = Graph()
        
        edge1 = make_edge(func_a, func_b)
        edge2 = make_edge(func_b, func_c)
        
        g.add_edges([edge1, edge2])
        
        # Both edges should be in graph
        self.assertIn(edge1, g[edge1.id()])
        self.assertIn(edge2, g[edge2.id()])
    
    def test_add_edges_with_tuple(self):
        """add_edges works with tuple of edges."""
        g = Graph()
        
        edges = (make_edge(func_a, func_b),)
        g.add_edges(edges)
        
        self.assertIn(edges[0], g[edges[0].id()])
    
    def test_add_edges_empty_list(self):
        """add_edges handles empty list."""
        g = Graph()
        g.add_edges([])
        # Should not raise error
        self.assertTrue(True)


class TestGraphGetNodes(unittest.TestCase):
    """Test get_nodes method."""
    
    def test_get_nodes_returns_unique_nodes(self):
        """get_nodes returns all unique nodes."""
        g = Graph()
        
        # Use as_unit to ensure we have unique units
        unit_a = as_unit(func_a)
        unit_b = as_unit(func_b)
        unit_c = as_unit(func_c)
        
        edge1 = make_edge(unit_a, unit_b)
        edge2 = make_edge(unit_b, unit_c)
        
        g.add_edges([edge1, edge2])
        
        nodes = g.get_nodes()
        
        # Should have 3 unique nodes
        self.assertEqual(len(nodes), 3)
        self.assertIsInstance(nodes, tuple)
    
    def test_get_nodes_empty_graph(self):
        """get_nodes returns empty tuple for empty graph."""
        g = Graph()
        nodes = g.get_nodes()
        
        self.assertEqual(nodes, ())
    
    def test_get_nodes_includes_both_a_and_b(self):
        """get_nodes includes both edge.a and edge.b."""
        g = Graph()
        
        edge = make_edge(func_a, func_b)
        g.add_edge(edge)
        
        nodes = g.get_nodes()
        
        # Should contain both nodes
        self.assertIn(edge.a, nodes)
        self.assertIn(edge.b, nodes)


class TestGraphConnect(unittest.TestCase):
    """Test connect method (chain of nodes)."""
    
    def test_connect_two_nodes(self):
        """connect creates chain for two nodes."""
        g = Graph()
        
        connections = g.connect(func_a, func_b)
        
        # Should create one connection
        self.assertEqual(len(connections), 1)
        self.assertIsInstance(connections[0], Connection)
    
    def test_connect_three_nodes(self):
        """connect creates chain for three nodes (a→b, b→c)."""
        g = Graph()
        
        connections = g.connect(func_a, func_b, func_c)
        
        # Should create two connections
        self.assertEqual(len(connections), 2)
    
    def test_connect_with_through(self):
        """connect accepts through parameter for wire function."""
        g = Graph()
        
        connections = g.connect(func_a, func_b, through=wire_func)
        
        self.assertEqual(len(connections), 1)
        # Edge should have the wire function
        self.assertIsNotNone(connections[0].through)


class TestGraphAdd(unittest.TestCase):
    """Test add method (single edge)."""
    
    def test_add_creates_single_edge(self):
        """add creates a single edge between two nodes."""
        g = Graph()
        
        connection = g.add(func_a, func_b)
        
        self.assertIsInstance(connection, Connection)
    
    def test_add_with_through(self):
        """add accepts through parameter for wire function."""
        g = Graph()
        
        connection = g.add(func_a, func_b, through=wire_func)
        
        # Connection should have wire function
        self.assertIsNotNone(connection.through)
    
    def test_add_stores_in_graph(self):
        """add stores the connection in the graph."""
        g = Graph()
        
        connection = g.add(func_a, func_b)
        
        # Connection should be in graph
        self.assertIn(connection, g[connection.id()])


class TestGraphResolve(unittest.TestCase):
    """Test resolve method."""
    
    def test_resolve_calls_resolve_node(self):
        """resolve delegates to resolve_node method."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        # GraphBase doesn't have resolve_node by default,
        # but resolve calls it. This tests the delegation.
        # Just verify resolve doesn't crash
        pass_attribute_error(g.resolve, unit)


class TestGraphStepperPrepare(unittest.TestCase):
    """Test stepper_prepare method."""
    
    def test_stepper_prepare_stores_caller(self):
        """stepper_prepare stores the starting node."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        g.stepper_prepare(unit, 10)
        
        self.assertEqual(g._stepper_callers, unit)
    
    def test_stepper_prepare_stores_args(self):
        """stepper_prepare stores arguments as ArgsPack."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        g.stepper_prepare(unit, 5, 10, key='value')
        
        self.assertIsNotNone(g._stepper_args)
        self.assertEqual(g._stepper_args.args, (5, 10))
        self.assertEqual(g._stepper_args.kwargs, {'key': 'value'})
    
    def test_stepper_prepare_without_args(self):
        """stepper_prepare works with no arguments."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        g.stepper_prepare(unit)
        
        self.assertEqual(g._stepper_callers, unit)
        # Args should be empty ArgsPack
        self.assertEqual(g._stepper_args.args, ())
        self.assertEqual(g._stepper_args.kwargs, {})


class TestGraphStepperPrepareMany(unittest.TestCase):
    """Test stepper_prepare_many method."""
    
    def test_stepper_prepare_many_stores_rows(self):
        """stepper_prepare_many stores multiple (node, args) rows."""
        g = Graph()
        
        unit_a = as_unit(func_a)
        unit_b = as_unit(func_b)
        
        with patch('builtins.print'):
            g.stepper_prepare_many(
                (unit_a, 10),
                (unit_b, 20)
            )
        
        self.assertIsNotNone(g._stepper_rows)
        self.assertEqual(len(g._stepper_rows), 2)
    
    def test_stepper_prepare_many_creates_argspacks(self):
        """stepper_prepare_many wraps args in ArgsPacks."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        with patch('builtins.print'):
            g.stepper_prepare_many((unit, 5, 10))
        
        # Rows should have (node, ArgsPack) format
        node, args = g._stepper_rows[0]
        self.assertEqual(node, unit)
        self.assertEqual(args.args, (5, 10))


class TestGraphStepper(unittest.TestCase):
    """Test stepper method."""
    
    def test_stepper_returns_stepper_instance(self):
        """stepper returns a StepperC instance."""
        g = Graph()
        
        unit = as_unit(func_a)
        g.stepper_prepare(unit, 10)
        
        stepper = g.stepper()
        
        # Should be a StepperC instance
        self.assertIsInstance(stepper, StepperC)
    
    def test_stepper_with_connection(self):
        """stepper works with a simple connection."""
        g = Graph()
        
        # Create a connection
        g.connect(func_a, func_b)
        
        # Get first unit
        nodes = g.get_nodes()
        first_node = nodes[0]
        g.stepper_prepare(first_node, 10)
        
        stepper = g.stepper()
        
        # Stepper should be created
        self.assertIsInstance(stepper, StepperC)
    
    def test_stepper_with_direct_node_and_args(self):
        """stepper can be called with node and args directly."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        stepper = g.stepper(unit, 10)
        
        # Stepper should be created
        self.assertIsInstance(stepper, StepperC)
    
    def test_stepper_with_prepared_rows(self):
        """stepper uses rows from stepper_prepare_many."""
        g = Graph()
        
        unit = as_unit(func_a)
        
        with patch('builtins.print'):
            g.stepper_prepare_many((unit, 10))
        
        stepper = g.stepper()
        
        # Should be a StepperC
        self.assertIsInstance(stepper, StepperC)
    
    def test_stepper_get_stepper_class(self):
        """get_stepper_class returns StepperC."""
        g = Graph()
        
        stepper_class = g.get_stepper_class()
        
        self.assertEqual(stepper_class, StepperC)
    
    def test_stepper_class_cached(self):
        """get_stepper_class caches the class."""
        g = Graph()
        
        # Call twice
        class1 = g.get_stepper_class()
        class2 = g.get_stepper_class()
        
        # Should be same instance
        self.assertIs(class1, class2)


class TestGraphWrite(unittest.TestCase):
    """Test write method for graphviz output."""
    
    @patch('hyperway.writer.write_graphviz')
    def test_write_calls_writer(self, mock_write):
        """write delegates to writer.write_graphviz."""
        g = Graph()
        
        g.write('test_graph')
        
        # Should call writer with graph and name
        mock_write.assert_called_once_with(g, 'test_graph')
    
    @patch('hyperway.writer.write_graphviz')
    def test_write_passes_kwargs(self, mock_write):
        """write passes kwargs to writer."""
        g = Graph()
        
        g.write('test_graph', engine='circo', directory='renders')
        
        # Should pass all kwargs
        mock_write.assert_called_once_with(
            g, 'test_graph',
            engine='circo',
            directory='renders'
        )


class TestUndirectedGraphBasics(unittest.TestCase):
    """Test UndirectedGraph class."""
    
    def test_undirected_graph_instantiation(self):
        """UndirectedGraph can be instantiated."""
        ug = UndirectedGraph()
        self.assertIsInstance(ug, UndirectedGraph)
    
    def test_undirected_graph_has_two_graphs(self):
        """UndirectedGraph contains FORWARD and BACKWARD graphs."""
        ug = UndirectedGraph()
        
        self.assertIn(FORWARD, ug.graphs)
        self.assertIn(BACKWARD, ug.graphs)
        self.assertIsInstance(ug.graphs[FORWARD], Graph)
        self.assertIsInstance(ug.graphs[BACKWARD], Graph)
    
    def test_undirected_graph_getattr_forward(self):
        """UndirectedGraph.__getattr__ returns FORWARD graph."""
        ug = UndirectedGraph()
        
        forward = ug.__getattr__(FORWARD)
        self.assertIsInstance(forward, Graph)
    
    def test_undirected_graph_getattr_backward(self):
        """UndirectedGraph.__getattr__ returns BACKWARD graph."""
        ug = UndirectedGraph()
        
        backward = ug.__getattr__(BACKWARD)
        self.assertIsInstance(backward, Graph)
    
    def test_undirected_graph_getitem_forward(self):
        """UndirectedGraph[FORWARD] returns FORWARD graph."""
        ug = UndirectedGraph()
        
        forward = ug[FORWARD]
        self.assertIsInstance(forward, Graph)
        self.assertIs(forward, ug.graphs[FORWARD])
    
    def test_undirected_graph_getitem_backward(self):
        """UndirectedGraph[BACKWARD] returns BACKWARD graph."""
        ug = UndirectedGraph()
        
        backward = ug[BACKWARD]
        self.assertIsInstance(backward, Graph)
        self.assertIs(backward, ug.graphs[BACKWARD])


class TestUndirectedGraphAddEdge(unittest.TestCase):
    """Test UndirectedGraph add_edge method."""
    
    def test_add_edge_stores_in_both_graphs(self):
        """add_edge stores edge in both FORWARD and BACKWARD graphs."""
        ug = UndirectedGraph()
        
        edge = make_edge(func_a, func_b)
        ug.add_edge(edge)
        
        # Edge should be in both graphs by edge id
        edge_id = id(edge)
        self.assertIn(edge, ug.graphs[FORWARD][edge_id])
        self.assertIn(edge, ug.graphs[BACKWARD][edge_id])


class TestUndirectedGraphConnect(unittest.TestCase):
    """Test UndirectedGraph connect method."""
    
    def test_connect_creates_bidirectional_edges(self):
        """connect creates edges in both FORWARD and BACKWARD graphs."""
        ug = UndirectedGraph()
        
        result = ug.connect(func_a, func_b)
        
        # Should return tuple of connections
        self.assertIsInstance(result, tuple)
        # Forward: 1 edge (a->b), Backward: 1 edge (b->a)
        self.assertEqual(len(result), 2)
    
    def test_connect_three_nodes(self):
        """connect with three nodes creates edges in both directions."""
        ug = UndirectedGraph()
        
        result = ug.connect(func_a, func_b, func_c)
        
        # Forward: 2 edges (a->b, b->c)
        # Backward: 2 edges (c->b, b->a) - reversed order
        # Total: 4 edges
        self.assertEqual(len(result), 4)
    
    def test_connect_reverses_for_backward(self):
        """connect reverses node order for BACKWARD graph."""
        ug = UndirectedGraph()
        
        # Use as_unit to track specific nodes
        unit_a = as_unit(func_a)
        unit_b = as_unit(func_b)
        unit_c = as_unit(func_c)
        
        result = ug.connect(unit_a, unit_b, unit_c)
        
        # First two should be forward edges (a->b, b->c)
        # Last two should be backward edges (c->b, b->a)
        self.assertEqual(len(result), 4)
        
        # Verify forward edges
        self.assertEqual(result[0].a, unit_a)
        self.assertEqual(result[0].b, unit_b)
        self.assertEqual(result[1].a, unit_b)
        self.assertEqual(result[1].b, unit_c)
        
        # Verify backward edges (reversed)
        self.assertEqual(result[2].a, unit_c)
        self.assertEqual(result[2].b, unit_b)
        self.assertEqual(result[3].a, unit_b)
        self.assertEqual(result[3].b, unit_a)


class TestUndirectedGraphAdd(unittest.TestCase):
    """Test UndirectedGraph add method."""
    
    def test_add_creates_connection(self):
        """add creates a connection."""
        ug = UndirectedGraph()
        
        result = ug.add(func_a, func_b)
        
        # Should return a connection
        self.assertIsInstance(result, Connection)


class TestUndirectedGraphResolve(unittest.TestCase):
    """Test UndirectedGraph resolve method."""
    
    def test_resolve_delegates_to_base(self):
        """resolve calls base resolve function."""
        ug = UndirectedGraph()
        
        unit = as_unit(func_a)
        
        # Just verify it doesn't crash
        # (resolve_node is not implemented in base)
        # try:
        #     ug.resolve(unit)
        # except AttributeError:
        #     # Expected - resolve_node not implemented
        #     pass
        pass_attribute_error(ug.resolve, unit)


class TestGraphBaseUtilities(unittest.TestCase):
    """Test utility functions from hyperway.graph.base module."""
    
    def test_is_graph_with_graph_instance(self):
        """is_graph returns True for Graph instances."""
        
        g = Graph()
        
        # Should identify Graph instance
        self.assertTrue(is_graph(g))
    
    def test_is_graph_with_custom_type(self):
        """is_graph returns True for custom graph types passed as others."""
        
        class CustomGraph(GraphBase):
            pass
        
        cg = CustomGraph()
        
        # Should identify custom graph when passed in others
        self.assertTrue(is_graph(cg, CustomGraph))
    
    def test_is_graph_with_func_attribute(self):
        """is_graph returns True when object.func is a graph instance.
        
        This tests line 28 - the isinstance(u.func, types) branch.
        Some objects wrap graph instances in a .func attribute.
        """
        
        # Create a wrapper object with .func attribute
        class GraphWrapper:
            def __init__(self, graph):
                self.func = graph
        
        g = Graph()
        wrapper = GraphWrapper(g)
        
        # Should identify graph through .func attribute
        self.assertTrue(is_graph(wrapper))
    
    def test_is_graph_returns_false_for_non_graph(self):
        """is_graph returns False for non-graph objects."""
        
        # Regular objects should not be graphs
        self.assertFalse(is_graph("string"))
        self.assertFalse(is_graph(42))
        self.assertFalse(is_graph([]))
        
        # Object without .func should not trigger attribute error
        class PlainObject:
            pass
        
        self.assertFalse(is_graph(PlainObject()))
    
    def test_pairwise_function(self):
        """pairwise creates sliding window pairs from an iterable.
        
        This tests lines 65-67 - the pairwise() utility function.
        Given [1, 2, 3, 4], returns [(1,2), (2,3), (3,4)]
        """
        
        # Test with list
        result = list(pairwise([1, 2, 3, 4]))
        expected = [(1, 2), (2, 3), (3, 4)]
        self.assertEqual(result, expected)
        
        # Test with string
        result = list(pairwise("ABCD"))
        expected = [('A', 'B'), ('B', 'C'), ('C', 'D')]
        self.assertEqual(result, expected)
        
        # Test with empty iterable
        result = list(pairwise([]))
        self.assertEqual(result, [])
        
        # Test with single element
        result = list(pairwise([1]))
        self.assertEqual(result, [])
        
        # Test with two elements
        result = list(pairwise([1, 2]))
        expected = [(1, 2)]
        self.assertEqual(result, expected)

