"""Tests for node connection introspection methods.

Tests get_outbound_connections and get_inbound_connections methods
on Unit nodes to verify they correctly query graph topology.
"""

import pytest
from hyperway.graph import Graph
from hyperway.nodes import as_unit, Unit
from hyperway.tools import factory as f


class TestGetOutboundConnections:
    """Test get_outbound_connections method."""

    def test_outbound_connections_linear_chain(self):
        """Outbound connections in a linear chain."""
        g = Graph(tuple)
        chain = g.connect(f.add_10, f.add_20, f.add_30)
        
        start = chain[0].a
        middle = chain[1].a
        end = chain[-1].b
        
        # Start node has one outbound connection
        outbound = start.get_outbound_connections(g)
        assert outbound is not None
        assert len(outbound) == 1
        assert outbound[0].b.get_name() == 'P_add_20.0'
        
        # Middle node has one outbound connection
        outbound = middle.get_outbound_connections(g)
        assert len(outbound) == 1
        assert outbound[0].b.get_name() == 'P_add_30.0'
        
        # End node has no outbound connections
        outbound = end.get_outbound_connections(g)
        assert outbound is None or len(outbound) == 0

    def test_outbound_connections_with_branches(self):
        """Outbound connections when node splits into multiple branches."""
        g = Graph(tuple)
        
        start = as_unit(f.add_10)
        branch_a = as_unit(f.add_20)
        branch_b = as_unit(f.add_30)
        
        g.add(start, branch_a)
        g.add(start, branch_b)
        
        # Start node should have two outbound connections
        outbound = start.get_outbound_connections(g)
        assert len(outbound) == 2
        
        # Verify both branches are present
        branch_names = {edge.b.get_name() for edge in outbound}
        assert 'P_add_20.0' in branch_names
        assert 'P_add_30.0' in branch_names

    def test_outbound_connections_empty_graph(self):
        """Outbound connections for node not in graph."""
        g = Graph(tuple)
        node = as_unit(f.add_10)
        
        outbound = node.get_outbound_connections(g)
        assert outbound is None


class TestGetInboundConnections:
    """Test get_inbound_connections method."""

    def test_inbound_connections_linear_chain(self):
        """Inbound connections in a linear chain - no duplicates."""
        g = Graph(tuple)
        chain = g.connect(f.add_10, f.add_20, f.add_30)
        
        start = chain[0].a
        middle = chain[1].a
        end = chain[-1].b
        
        # Start node has no inbound connections
        inbound = start.get_inbound_connections(g)
        assert len(inbound) == 0
        
        # Middle node has exactly one inbound connection (not duplicated)
        inbound = middle.get_inbound_connections(g)
        assert len(inbound) == 1
        assert inbound[0].a.get_name() == 'P_add_10.0'
        
        # End node has exactly one inbound connection
        # chain is: add_10 → add_20 → add_30, so end (add_30) comes from add_20
        inbound = end.get_inbound_connections(g)
        assert len(inbound) == 1
        assert inbound[0].a.get_name() == 'P_add_20.0'

    def test_inbound_connections_with_merge(self):
        """Inbound connections when multiple branches merge to one node."""
        g = Graph(tuple)
        
        branch_a = as_unit(f.add_10)
        branch_b = as_unit(f.add_20)
        merge = as_unit(f.add_30)
        
        g.add(branch_a, merge)
        g.add(branch_b, merge)
        
        # Merge node should have two inbound connections
        inbound = merge.get_inbound_connections(g)
        assert len(inbound) == 2
        
        # Verify both branches are present
        source_names = {edge.a.get_name() for edge in inbound}
        assert 'P_add_10.0' in source_names
        assert 'P_add_20.0' in source_names

    def test_inbound_connections_no_duplicates(self):
        """Verify inbound connections are deduplicated.
        
        The graph stores each edge twice internally (by edge ID and by node A ID),
        but get_inbound_connections should return each unique edge only once.
        """
        g = Graph(tuple)
        a = as_unit(f.add_10)
        b = as_unit(f.add_20)
        
        edge = g.add(a, b)
        
        # Verify the edge is stored twice in the graph (implementation detail)
        edge_count_in_graph = 0
        for edges in g.values():
            for e in edges:
                if e.id() == edge.id():
                    edge_count_in_graph += 1
        assert edge_count_in_graph == 2, "Edge should be stored twice in graph"
        
        # But get_inbound_connections should return it only once
        inbound = b.get_inbound_connections(g)
        assert len(inbound) == 1
        assert inbound[0].id() == edge.id()

    def test_inbound_connections_empty_graph(self):
        """Inbound connections for node not in graph."""
        g = Graph(tuple)
        node = as_unit(f.add_10)
        
        inbound = node.get_inbound_connections(g)
        assert len(inbound) == 0


class TestConnectionIntrospectionIntegration:
    """Integration tests combining both inbound and outbound."""

    def test_complex_topology(self):
        """Test connection methods on a complex graph."""
        g = Graph(tuple)
        
        # Build: n1 → n2 → n4
        #         ↓    ↓     ↑
        #        n3 → n5 ----+
        n1 = as_unit(f.add_1, name="n1")
        n2 = as_unit(f.add_2, name="n2")
        n3 = as_unit(f.add_3, name="n3")
        n4 = as_unit(f.add_4, name="n4")
        n5 = as_unit(f.add_5, name="n5")
        
        g.add(n1, n2)
        g.add(n1, n3)
        g.add(n2, n4)
        g.add(n2, n5)
        g.add(n3, n5)
        g.add(n5, n4)
        
        # n1: 0 in, 2 out
        assert len(n1.get_inbound_connections(g)) == 0
        assert len(n1.get_outbound_connections(g)) == 2
        
        # n2: 1 in, 2 out
        assert len(n2.get_inbound_connections(g)) == 1
        assert len(n2.get_outbound_connections(g)) == 2
        
        # n3: 1 in, 1 out
        assert len(n3.get_inbound_connections(g)) == 1
        assert len(n3.get_outbound_connections(g)) == 1
        
        # n4: 2 in, 0 out (leaf)
        assert len(n4.get_inbound_connections(g)) == 2
        outbound = n4.get_outbound_connections(g)
        assert outbound is None or len(outbound) == 0
        
        # n5: 2 in, 1 out (hub)
        assert len(n5.get_inbound_connections(g)) == 2
        assert len(n5.get_outbound_connections(g)) == 1

    def test_graph_analysis_helpers(self):
        """Test using connection methods for graph analysis."""
        g = Graph(tuple)
        
        nodes = [as_unit(func, name=f"node_{i}") 
                 for i, func in enumerate([f.add_1, f.add_2, f.add_3, f.add_4])]
        
        n1, n2, n3, n4 = nodes
        
        g.connect(n1, n2, n3)
        g.add(n2, n4)
        g.add(n3, n4)
        
        # Find root nodes (no inbound)
        roots = [n for n in nodes if len(n.get_inbound_connections(g)) == 0]
        assert len(roots) == 1
        assert roots[0] == n1
        
        # Find leaf nodes (no outbound)
        leaves = [n for n in nodes 
                  if n.get_outbound_connections(g) is None 
                  or len(n.get_outbound_connections(g)) == 0]
        assert len(leaves) == 1
        assert leaves[0] == n4
        
        # Find hub nodes (3+ total connections)
        # n1 (0 in + 1 out = 1), n2 (1 in + 2 out = 3), n3 (1 in + 1 out = 2), n4 (2 in + 0 out = 2)
        hubs = [n for n in nodes 
                if len(n.get_inbound_connections(g)) + 
                   len(n.get_outbound_connections(g) or []) >= 3]
        assert len(hubs) == 1
        assert hubs[0] == n2

    def test_connection_identity(self):
        """Verify inbound and outbound refer to same connection objects."""
        g = Graph(tuple)
        
        a = as_unit(f.add_10)
        b = as_unit(f.add_20)
        
        edge = g.add(a, b)
        
        # Get outbound from a
        outbound = a.get_outbound_connections(g)
        assert len(outbound) == 1
        outbound_edge = outbound[0]
        
        # Get inbound to b
        inbound = b.get_inbound_connections(g)
        assert len(inbound) == 1
        inbound_edge = inbound[0]
        
        # They should be the same connection object
        assert outbound_edge.id() == inbound_edge.id()
        assert outbound_edge.id() == edge.id()
