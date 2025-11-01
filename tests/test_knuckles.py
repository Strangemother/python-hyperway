"""
Tests for the knuckles pattern - custom edge selection via unit.get_connections().

The knuckles pattern allows nodes to dynamically control which edges are traversed
based on runtime data (akw). This is implemented by defining a custom get_connections()
method on a Unit subclass that filters connections based on the akw parameter.
"""

import unittest
from unittest.mock import patch

from hyperway.edges import get_connections
from hyperway.nodes import Unit, as_unit
from hyperway.packer import argspack
from hyperway.graph import Graph

from tiny_tools import passthrough


# Test functions
func_a = passthrough
func_b = passthrough

def func_c(v=None):
    """Standard test function C."""
    if v is None:
        v = 0
    return v + 3


class TestKnucklesPattern(unittest.TestCase):
    """Test the knuckles pattern - data-driven edge selection."""
    
    def test_custom_get_connections_filters_by_name(self):
        """Unit with custom get_connections can filter edges by connection name.
        
        This is the core knuckles pattern: a node decides which edges to traverse
        based on data in the akw parameter. Here we filter by connection name.
        """
        
        g = Graph()
        
        # Create a custom unit that filters connections by name
        class SelectiveUnit(Unit):
            def get_connections(self, graph, akw=None):
                """Return connections filtered by akw data."""
                all_connections = tuple(graph.get(self.id()))
                
                if akw is None or not akw.args:
                    return all_connections
                
                # Filter by target name in akw
                target = akw.args[0] if akw.args else None
                filtered = tuple(c for c in all_connections if c.name == target)
                return filtered if filtered else all_connections
        
        # Create unit and named connections
        unit_a = SelectiveUnit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)
        
        edge1.name = 'path_b'
        edge2.name = 'path_c'
        
        # Test filtering to path_b
        akw_b = argspack('path_b')
        with patch('builtins.print'):
            connections = get_connections(g, unit_a, akw=akw_b)
        
        self.assertEqual(len(connections), 1)
        self.assertIn(edge1, connections)
        self.assertNotIn(edge2, connections)
        
        # Test filtering to path_c
        akw_c = argspack('path_c')
        with patch('builtins.print'):
            connections = get_connections(g, unit_a, akw=akw_c)
        
        self.assertEqual(len(connections), 1)
        self.assertIn(edge2, connections)
        self.assertNotIn(edge1, connections)
    
    def test_custom_get_connections_returns_all_when_no_akw(self):
        """Custom get_connections falls back to all edges when akw is None."""
        
        g = Graph()
        
        class SelectiveUnit(Unit):
            def get_connections(self, graph, akw=None):
                all_connections = tuple(graph.get(self.id()))
                
                if akw is None or not akw.args:
                    return all_connections
                
                target = akw.args[0] if akw.args else None
                filtered = tuple(c for c in all_connections if c.name == target)
                return filtered if filtered else all_connections
        
        unit_a = SelectiveUnit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)
        
        edge1.name = 'path_b'
        edge2.name = 'path_c'
        
        # Without akw, should return all connections
        with patch('builtins.print'):
            connections = get_connections(g, unit_a)
        
        self.assertEqual(len(connections), 2)
        self.assertIn(edge1, connections)
        self.assertIn(edge2, connections)
    
    def test_custom_get_connections_with_dict_routing(self):
        """Knuckles pattern with dictionary-based routing data.
        
        Demonstrates using a dictionary in akw to make routing decisions,
        showing flexibility beyond simple string matching.
        """
        
        g = Graph()
        
        class DictRoutingUnit(Unit):
            def get_connections(self, graph, akw=None):
                all_connections = tuple(graph.get(self.id()))
                
                if akw is None or not akw.kwargs:
                    return all_connections
                
                # Route based on 'target' key in kwargs
                target = akw.kwargs.get('target')
                if target is None:
                    return all_connections
                
                filtered = tuple(c for c in all_connections if c.name == target)
                return filtered if filtered else all_connections
        
        unit_a = DictRoutingUnit(func_a)
        edge1 = g.add(unit_a, func_b)
        edge2 = g.add(unit_a, func_c)
        
        edge1.name = 'option_1'
        edge2.name = 'option_2'
        
        # Route using kwargs
        akw = argspack(target='option_1')
        with patch('builtins.print'):
            connections = get_connections(g, unit_a, akw=akw)
        
        self.assertEqual(len(connections), 1)
        self.assertIn(edge1, connections)
        self.assertNotIn(edge2, connections)


if __name__ == '__main__':
    unittest.main()
