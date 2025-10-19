import unittest

from hyperway.graph import Graph
from hyperway.tools import factory as f
from hyperway.tools import doubler
from hyperway import reader
from hyperway.nodes import as_unit


class TestReaderThinAndFlat(unittest.TestCase):
    def test_thin_graph_simple_chain(self):
        g = Graph()
        chain = g.connect(f.add_1, f.add_2, f.add_4)

        a = chain[0].a
        b = chain[0].b
        c = chain[1].b

        thin = reader.thin_graph(g)

        # Compare as sets to ignore internal duplication from graph storage
        self.assertEqual(set(thin[a.id()]), {b.id()})
        self.assertEqual(set(thin[b.id()]), {c.id()})

    def test_flat_graph_edges(self):
        g = Graph()
        chain = g.connect(f.add_1, f.add_2, f.add_4)

        a = chain[0].a
        b = chain[0].b
        c = chain[1].b

        flat = reader.flat_graph(g)
        # Convert to set of pairs for stable comparison
        self.assertEqual(set(flat), {(a.id(), b.id()), (b.id(), c.id())})


class TestReaderNodesEdges(unittest.TestCase):
    def test_get_nodes_edges(self):
        g = Graph()
        chain = g.connect(f.add_1, f.add_2, f.add_4)

        a = chain[0].a
        b = chain[0].b
        c = chain[1].b

        nodes, edges = reader.get_nodes_edges(g)

        # Edges are stringified ids
        self.assertEqual(
            edges,
            {(str(a.id()), str(b.id())), (str(b.id()), str(c.id()))},
        )

        # Nodes include id and display name (function name)
        names = {name for (_id, name) in nodes}
        self.assertTrue({a.get_name(), b.get_name(), c.get_name()} <= names)


class TestReaderLinearChain(unittest.TestCase):
    def test_read_linear_chain_with_and_without_through(self):
        g = Graph()
        # Pre-wrap units to ensure identity is preserved across edges
        a = as_unit(f.add_1)
        b = as_unit(f.add_2)
        c = as_unit(f.add_4)

        # a -(doubler)-> b -> c
        g.add(a, b, through=doubler)
        g.add(b, c)

        rows_with = reader.read_linear_chain(g, a)
        # Expected: ( (a,), (doubler, b), (c,) )
        self.assertEqual(rows_with[0], (a,))
        self.assertEqual(rows_with[1][0], doubler)
        self.assertEqual(rows_with[1][1], b)
        self.assertEqual(rows_with[2], (c,))

        rows_without = reader.read_linear_chain(g, a, with_through=False)
        # Expected: ( (a,), (b,), (c,) )
        self.assertEqual(rows_without, ((a,), (b,), (c,)))

        # Starting from b should not include the a->b through
        rows_from_b = reader.read_linear_chain(g, b)
        self.assertEqual(rows_from_b, ((b,), (c,)))


class TestReaderTreeChain(unittest.TestCase):
    def test_read_tree_chain_branching(self):
        g = Graph()
        # Build a small branching graph with shared Unit instances
        a = as_unit(f.add_1)
        b = as_unit(f.add_2)
        c = as_unit(f.add_4)
        d = as_unit(f.add_5)
        e = as_unit(f.add_10)

        # a -(doubler)-> b -> d
        # a -----------> c -(doubler)-> e
        g.add(a, b, through=doubler)
        g.add(a, c)
        g.add(b, d)
        g.add(c, e, through=doubler)

        tree_with = reader.read_tree_chain(g, a, with_through=True)
        # Expect: (a, (doubler, b, d), (c, doubler, e))
        self.assertEqual(tree_with[0], a)
        self.assertEqual(tree_with[1], (doubler, b, d))
        self.assertEqual(tree_with[2], (c, doubler, e))

        tree_without = reader.read_tree_chain(g, a, with_through=False)
        # Expect: (a, (b, d), (c, e))
        self.assertEqual(tree_without, (a, (b, d), (c, e)))

    def test_conn_b_chain_helper(self):
        g = Graph()
        c = g.connect(f.add_1, f.add_2, through=doubler)[0]
        a = c.a
        b = c.b

        row_with = reader.conn_b_chain(g, c, with_through=True)
        self.assertEqual(row_with, (doubler, b))

        row_without = reader.conn_b_chain(g, c, with_through=False)
        self.assertEqual(row_without, (b,))

