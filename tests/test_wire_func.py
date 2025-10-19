"""Test wire functions (through functions) in Hyperway.

Wire functions (or "through" functions) allow you to transform data as it flows
between connected nodes in a graph. They act as data transformation middleware
between the output of one node and the input of the next.

Basic Flow:
    Node A → through function → Node B
    
The through function receives the result from Node A and returns an argspack
that will be passed to Node B.
"""

import unittest

from hyperway.tools import factory as f
from hyperway.edges import make_edge
from hyperway.packer import argspack


class TestWireFunc(unittest.TestCase):
    """Validate that wire functions (through functions) properly transform data between nodes.
    
    Wire functions enable data transformation between connected nodes in a graph.
    When creating an edge with make_edge(a, b, through=func), the through function
    receives the output from node 'a' and transforms it before passing to node 'b'.
    """

    def test_basic_through_with_argspack(self):
        """Test basic edge connection using argspack as the through function.
        
        Flow: input → add_1 (+1) → argspack (pass-through) → add_2 (+2)
        Result: input + 1 + 2 = input + 3
        """
        connection = make_edge(f.add_1, f.add_2, through=argspack)
        
        # Test various inputs
        self.assertEqual(connection.pluck(1), 4)    # 1 + 1 + 2 = 4
        self.assertEqual(connection.pluck(5), 8)    # 5 + 1 + 2 = 8
        self.assertEqual(connection.pluck(10), 13)  # 10 + 1 + 2 = 13
        self.assertEqual(connection.pluck(77), 80)  # 77 + 1 + 2 = 80

    def test_custom_wire_function(self):
        """Test custom wire function that adds 9 to the intermediate value.
        
        Flow: input → add_1 (+1) → wire_func (+9) → add_2 (+2)
        Result: input + 1 + 9 + 2 = input + 12
        """
        def wire_func(v, *a, **kw):
            """Custom wire function that adds 9 to the value."""
            return argspack(v + 9, **kw)
        
        connection = make_edge(f.add_1, f.add_2, through=wire_func)
        
        # Test various inputs
        self.assertEqual(connection.pluck(1), 13)   # 1 + 1 + 9 + 2 = 13
        self.assertEqual(connection.pluck(5), 17)   # 5 + 1 + 9 + 2 = 17
        self.assertEqual(connection.pluck(10), 22)  # 10 + 1 + 9 + 2 = 22
        self.assertEqual(connection.pluck(77), 89)  # 77 + 1 + 9 + 2 = 89

    def test_wire_function_with_multiplication(self):
        """Test wire function that multiplies the intermediate value.
        
        Demonstrates that wire functions can perform any transformation,
        not just addition.
        """
        def multiply_by_2(v, *a, **kw):
            """Wire function that doubles the value."""
            return argspack(v * 2, **kw)
        
        connection = make_edge(f.add_1, f.add_2, through=multiply_by_2)
        
        # Flow: 5 → add_1 = 6 → multiply_by_2 = 12 → add_2 = 14
        self.assertEqual(connection.pluck(5), 14)
        
        # Flow: 10 → add_1 = 11 → multiply_by_2 = 22 → add_2 = 24
        self.assertEqual(connection.pluck(10), 24)

    def test_wire_function_preserves_kwargs(self):
        """Test that wire functions can preserve and pass through keyword arguments."""
        def wire_with_kwargs(v, *a, **kw):
            """Wire function that modifies value but preserves kwargs."""
            # Add a new kwarg and preserve existing ones
            kw['transformed'] = True
            return argspack(v + 5, **kw)
        
        def node_with_kwargs(v, transformed=False):
            """Node that uses keyword arguments."""
            if transformed:
                return v * 10
            return v
        
        connection = make_edge(
            f.add_1, 
            node_with_kwargs, 
            through=wire_with_kwargs
        )
        
        # Flow: 1 → add_1 = 2 → wire_func = 7 (transformed=True) → node = 70
        result = connection.pluck(1)
        self.assertEqual(result, 70)

    def test_wire_function_without_through(self):
        """Test that edges work without a through function (default behavior).
        
        When no through function is specified, the output from node A is
        passed directly to node B using the default argspack behavior.
        """
        connection = make_edge(f.add_1, f.add_2)  # No through parameter
        
        # Should still work like through=argspack
        self.assertEqual(connection.pluck(1), 4)
        self.assertEqual(connection.pluck(10), 13)

    def test_wire_function_can_change_argument_count(self):
        """Test that wire functions can change the number of arguments passed.
        
        Wire functions can expand or reduce the number of arguments,
        allowing flexible data transformation between nodes.
        """
        def expand_args(v, *a, **kw):
            """Wire function that creates multiple arguments from one."""
            return argspack(v, v + 1, v + 2)
        
        def sum_three(a, b, c):
            """Node that expects three arguments."""
            return a + b + c
        
        connection = make_edge(f.add_1, sum_three, through=expand_args)
        
        # Flow: 1 → add_1 = 2 → expand_args = (2, 3, 4) → sum_three = 9
        self.assertEqual(connection.pluck(1), 9)
        
        # Flow: 5 → add_1 = 6 → expand_args = (6, 7, 8) → sum_three = 21
        self.assertEqual(connection.pluck(5), 21)


class TestWireFuncEdgeCases(unittest.TestCase):
    """Test edge cases and advanced wire function scenarios."""

    def test_wire_function_with_subtraction(self):
        """Test wire function that performs subtraction transformation."""
        def subtract_five(v, *a, **kw):
            """Wire function that subtracts 5 from the value."""
            return argspack(v - 5, **kw)
        
        connection = make_edge(f.add_10, f.add_1, through=subtract_five)
        
        # Flow: 10 → add_10 = 20 → subtract_five = 15 → add_1 = 16
        self.assertEqual(connection.pluck(10), 16)

    def test_chained_transformations(self):
        """Test that multiple transformations can be composed.
        
        While this test uses a single wire function, it demonstrates
        how complex transformations can be built.
        """
        def complex_transform(v, *a, **kw):
            """Wire function with multiple operations."""
            result = (v + 10) * 2 - 5
            return argspack(result, **kw)
        
        connection = make_edge(f.add_1, f.add_2, through=complex_transform)
        
        # Flow: 5 → add_1 = 6 → complex = ((6+10)*2-5) = 27 → add_2 = 29
        self.assertEqual(connection.pluck(5), 29)

    def test_wire_function_with_conditional_logic(self):
        """Test wire function that applies conditional transformation."""
        def conditional_transform(v, *a, **kw):
            """Wire function that transforms based on value."""
            if v > 10:
                return argspack(v * 2, **kw)
            else:
                return argspack(v + 10, **kw)
        
        connection = make_edge(f.add_1, f.add_2, through=conditional_transform)
        
        # Small value: 5 → add_1 = 6 → conditional = 16 → add_2 = 18
        self.assertEqual(connection.pluck(5), 18)
        
        # Large value: 15 → add_1 = 16 → conditional = 32 → add_2 = 34
        self.assertEqual(connection.pluck(15), 34)


