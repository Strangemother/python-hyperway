"""Advanced tests for stepper functionality in Hyperway.

These tests cover the less-common code paths and advanced features:
- row_concat and merge nodes
- concat_aware mode
- expand function variants
- StepperIterator behavior
- Edge cases and error conditions
- Helper functions (run_stepper, process_forward, etc.)
- Various call_one_* methods
- flush and peek operations
"""

import unittest
from unittest.mock import MagicMock, patch

from hyperway.graph import Graph
from hyperway.nodes import as_unit, Unit
from hyperway.packer import argspack
from hyperway.edges import make_edge, PartialConnection
from hyperway.stepper import (
    StepperC,
    StepperException,
    StepperIterator,
    run_stepper,
    process_forward,
    expand_tuple,
    expand_list,
    set_global_expand,
    stepper_c,
    is_merge_node,
    expand,
)
# from hyperway import stepper
from hyperway.packer import ArgsPack
from hyperway.stepper import expand_unified
from unittest.mock import Mock, patch
from hyperway.edges import Connection    


def multiply_by_2(v):
    """Multiply a value by 2."""
    return v * 2


def merger(*args):
    return sum(args)

assert merger(1,2,3) == 6

# Create a custom expand function
def custom_expand(items, second):
    return (('custom', second),)

assert custom_expand({}, 42) == (('custom', 42),)

from tiny_tools import add_n, passthrough, noop

class TestExpandFunctions(unittest.TestCase):
    """Test the expand functions that create row tuples."""

    def test_expand_tuple_simple(self):
        """Test expand_tuple with simple items."""
        items = ('a', 'b', 'c')
        second = 'x'
        
        result = expand_tuple(items, second)
        
        expected = (('a', 'x'), ('b', 'x'), ('c', 'x'))
        self.assertEqual(result, expected)

    def test_expand_tuple_nested(self):
        """Test expand_tuple with nested tuple items."""
        items = (('a', 'b'), 'c')
        second = 'x'
        
        result = expand_tuple(items, second)
        
        # Nested items should be expanded
        expected = (('a', 'x'), ('b', 'x'), ('c', 'x'))
        self.assertEqual(result, expected)

    def test_expand_list_simple(self):
        """Test expand_list with simple items."""
        items = ['a', 'b', 'c']
        second = 'y'
        
        result = expand_list(items, second)
        
        expected = (('a', 'y'), ('b', 'y'), ('c', 'y'))
        self.assertEqual(result, expected)

    def test_expand_list_nested(self):
        """Test expand_list with nested list items."""
        items = [['a', 'b'], 'c']
        second = 'y'
        
        result = expand_list(items, second)
        
        expected = (('a', 'y'), ('b', 'y'), ('c', 'y'))
        self.assertEqual(result, expected)

    def test_expand_tuple_with_none(self):
        """Test expand_tuple handles None gracefully (no connections case)."""
        items = None
        second = argspack(100)
        
        result = expand_tuple(items, second)
        
        # Should return empty tuple, not crash
        self.assertEqual(result, ())

    def test_expand_list_with_none(self):
        """Test expand_list handles None gracefully (no connections case)."""
        items = None
        second = argspack(200)
        
        result = expand_list(items, second)
        
        # Should return empty tuple, not crash
        self.assertEqual(result, ())

    def test_set_global_expand(self):
        """Test setting the global expand function."""
        # Store original
        from hyperway import stepper
        original_expand = stepper.expand
        
        set_global_expand(custom_expand)
        
        # Verify it changed
        self.assertEqual(stepper.expand, custom_expand)
        
        # Restore original
        set_global_expand(original_expand)


class TestExpandUnified(unittest.TestCase):
    """Test expand_unified function for unified initiation mode."""
    
    def test_expand_unified_calls_node_once(self):
        """expand_unified calls each node once and distributes result to connections."""        
        g = Graph()
        
        # Track how many times the node is called
        call_count = [0]
        
        def counting_func(x):
            call_count[0] += 1
            return x * 2
        
        unit_a = as_unit(counting_func)
        g.add(unit_a, multiply_by_2)
        g.add(unit_a, multiply_by_2)  # Two connections from unit_a
        
        stepper = StepperC(g)
        akw = argspack(10)
        
        rows = expand_unified(stepper, (unit_a,), akw)
        
        # Node should be called once, not twice
        self.assertEqual(call_count[0], 1)
        # Should return 2 rows (one per connection)
        self.assertEqual(len(rows), 2)
    
    def test_expand_unified_returns_partial_connections(self):
        """expand_unified returns PartialConnection instances."""
        g = Graph()
        unit_a = as_unit(multiply_by_2)
        g.add(unit_a, multiply_by_2)
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        rows = expand_unified(stepper, (unit_a,), akw)
        
        self.assertEqual(len(rows), 1)
        next_caller, result_akw = rows[0]
        self.assertIsInstance(next_caller, PartialConnection)
        # Result should be from calling the node once
        self.assertEqual(result_akw.args[0], 10)
    
    def test_expand_unified_handles_no_connections(self):
        """expand_unified handles leaf nodes with no connections."""
        from hyperway.stepper import expand_unified
        
        g = Graph()
        unit_a = as_unit(multiply_by_2)
        # No connections added - unit_a is a leaf
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        rows = expand_unified(stepper, (unit_a,), akw)
        
        # Leaf nodes return empty tuple by default
        self.assertEqual(rows, ())


class TestExpandUnifiedNodeCall(unittest.TestCase):
    """Test expand_unified if/else for is_unit check - lines 128-135 in stepper.py."""
    
    def test_is_unit_true_calls_process(self):
        """When is_unit(node) is True, calls node.process()."""
        g = Graph()
        unit_a = as_unit(multiply_by_2)
        g.add(unit_a, multiply_by_2)
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        rows = expand_unified(stepper, (unit_a,), akw)
        
        # Unit.process called: 5 * 2 = 10
        _, result_akw = rows[0]
        self.assertEqual(result_akw.args[0], 10)
    
    def test_is_unit_false_calls_directly(self):
        """When is_unit(node) is False, calls node directly (else branch)."""
        g = Graph()
        # Mock callable that is NOT a Unit
        mock_callable = Mock(return_value=42)
        mock_callable.__name__ = 'mock_func'
        
        unit_b = as_unit(multiply_by_2)
    
        # Manually create connection
        conn = Connection(mock_callable, unit_b)
        g.add_edge(conn)
        
        stepper = StepperC(g)
        akw = argspack(10, foo='bar')
        
        # Mock get_connections to return proper list
        with patch('hyperway.stepper.get_connections', return_value=[conn]):
            rows = expand_unified(stepper, (mock_callable,), akw)
        
        # Should call mock_callable directly (else branch: not .process)
        mock_callable.assert_called_once_with(10, foo='bar')
        _, result_akw = rows[0]
        self.assertEqual(result_akw.args[0], 42)
    
    def test_both_branches_return_argspack(self):
        """Both if and else branches wrap result in argspack."""
        g = Graph()
        unit_a = as_unit(multiply_by_2)
        g.add(unit_a, multiply_by_2)
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        rows = expand_unified(stepper, (unit_a,), akw)
        
        _, result_akw = rows[0]
        self.assertIsInstance(result_akw, ArgsPack)


class TestHelperFunctions(unittest.TestCase):
    """Test top-level helper functions."""

    def test_run_stepper(self):
        """Test run_stepper convenience function."""
        g = Graph()
        
        unit = as_unit(multiply_by_2)
        g.add(unit, passthrough)
        
        stepper, result = run_stepper(g, unit, 5)
        
        self.assertIsInstance(stepper, StepperC)
        self.assertIsNotNone(result)

    def test_process_forward(self):
        """Test process_forward function."""
        g = Graph()
        
        unit = as_unit(add_n(10))
        akw = argspack(5)
        
        stepper, result = process_forward(g, unit, akw)
        
        self.assertIsInstance(stepper, StepperC)

    def test_stepper_c(self):
        """Test stepper_c factory function."""
        g = Graph()
        
        unit = as_unit(passthrough)
        akw = argspack(10)
        
        stepper, result = stepper_c(g, unit, akw)
        
        self.assertIsInstance(stepper, StepperC)
        self.assertIsInstance(result, tuple)

    def test_is_merge_node_false(self):
        """Test is_merge_node returns False for regular callables."""
        self.assertFalse(is_merge_node(noop))

    def test_is_merge_node_true(self):
        """Test is_merge_node returns True when merge_node attribute is set."""
        unit = as_unit(lambda x: x)
        unit.merge_node = True
        
        self.assertTrue(is_merge_node(unit))

    def test_is_merge_node_false_explicit(self):
        """Test is_merge_node returns False when explicitly set to False."""
        unit = as_unit(lambda x: x)
        unit.merge_node = False
        
        self.assertFalse(is_merge_node(unit))


class TestStepperIterator(unittest.TestCase):
    """Test StepperIterator class."""

    def test_stepper_iterator_creation(self):
        """Test creating a StepperIterator."""
        g = Graph()
        stepper = StepperC(g)
        funcs = (lambda x: x,)
        akw = argspack(1)
        
        iterator = StepperIterator(stepper, funcs, akw)
        
        self.assertEqual(iterator.stepper, stepper)
        self.assertEqual(iterator.start_nodes, funcs)
        self.assertEqual(iterator.start_akw, akw)

    def test_stepper_iterator_iter(self):
        """Test __iter__ returns self."""
        g = Graph()
        stepper = StepperC(g)
        iterator = StepperIterator(stepper, (), argspack())
        
        self.assertIs(iter(iterator), iterator)

    def test_stepper_iterator_with_config(self):
        """Test StepperIterator with additional config."""
        g = Graph()
        stepper = StepperC(g)
        funcs = (lambda x: x,)
        akw = argspack(1)
        
        iterator = StepperIterator(stepper, funcs, akw, custom_key='value')
        
        self.assertEqual(iterator.config, {'custom_key': 'value'})


class TestRowConcat(unittest.TestCase):
    """Test row_concat functionality for merge nodes."""

    def test_row_concat_no_duplicates(self):
        """Test row_concat with no duplicate nodes."""
        g = Graph()
        
        ua = as_unit(passthrough)
        ub = as_unit(passthrough)
        
        stepper = StepperC(g)
        rows = (
            (ua, argspack(10)),
            (ub, argspack(20)),
        )
        
        result = stepper.row_concat(rows)
        
        # No duplicates, should return same rows
        self.assertEqual(len(result), 2)

    def test_row_concat_with_merge_node(self):
        """Test row_concat with a merge node that combines args."""
        g = Graph()
                
        merge_unit = as_unit(merger)
        merge_unit.merge_node = True
        
        stepper = StepperC(g)
        stepper.concat_aware = True
        
        # Multiple rows pointing to the same merge node
        rows = (
            (merge_unit, argspack(10)),
            (merge_unit, argspack(20)),
            (merge_unit, argspack(30)),
        )
        
        result = stepper.row_concat(rows)
        
        # Should reduce to one row with merged args
        self.assertEqual(len(result), 1)

    def test_row_concat_partial_connection(self):
        """Test row_concat with PartialConnection instances."""
        g = Graph()
        
        ua = as_unit(passthrough)
        ub = as_unit(passthrough)
        
        edge = make_edge(ua, ub)
        
        # Create partial connection (mocking for test)
        partial = PartialConnection(edge, None, ub)
        
        stepper = StepperC(g)
        rows = (
            (partial, argspack(10)),
        )
        
        result = stepper.row_concat(rows)
        
        # Should handle PartialConnection
        self.assertIsNotNone(result)

    def test_row_concat_flat_mode(self):
        """Test row_concat with concat_flat=True."""
        g = Graph()
        
        unit = as_unit(passthrough)
        
        stepper = StepperC(g)
        rows = (
            (unit, argspack(10)),
            (unit, argspack(20)),
        )
        
        result = stepper.row_concat(rows, concat_flat=True)
        
        # concat_flat should create one row per input call
        self.assertGreaterEqual(len(result), 1)


class TestCallOneMethods(unittest.TestCase):
    """Test the various call_one_* methods."""

    def test_call_one_with_none(self):
        """Test call_one with None func (bypass case)."""
        g = Graph()
        stepper = StepperC(g)
        stepper.stash_ends = False
        
        akw = argspack(10)
        result = stepper.call_one(None, akw)
        
        # Should call no_branch which returns rows with None
        self.assertIsInstance(result, tuple)
        self.assertGreater(len(result), 0)

    def test_call_one_fallthrough_2(self):
        """Test call_one_fallthrough for non-callable objects."""
        g = Graph()
        stepper = StepperC(g)
        
        # Pass a non-callable object
        thing = "not_a_function"
        akw = argspack(5)
        
        result = stepper.call_one_fallthrough(thing, akw)
        
        # Should return a row with None
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], None)

    def test_call_one_connection(self):
        """Test call_one_connection with an edge."""
        g = Graph()
        
        ua = as_unit(multiply_by_2)
        ub = as_unit(passthrough)
        
        edge = g.add(ua, ub)
        # Add a connection from ub so it has downstream connections
        g.add(ub, add_n(2))
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        result = stepper.call_one_connection(edge, akw)
        
        # Should return rows for next connections
        self.assertIsInstance(result, tuple)

    def test_call_one_callable_no_connections(self):
        """Test call_one_callable handles functions with no connections.
        
        This tests the bug fix where expand() now handles None gracefully.
        Previously this would crash with TypeError: 'NoneType' object is not iterable.
        """
        g = Graph()
        
        orphan_func = lambda v: v * 5
        
        stepper = StepperC(g)
        akw = argspack(10)
        
        # Call a function that has no connections in the graph
        # After the fix, this should return empty rows (end of branch)
        result = stepper.call_one_callable(orphan_func, akw)
        
        # Should return empty tuple (no next steps) instead of crashing
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 0)

    def test_call_one_connection_no_downstream(self):
        """Test call_one_connection when edge.b has no outgoing connections.
        
        This tests another case where expand() receives None.
        """
        g = Graph()
        
        ua = as_unit(multiply_by_2)
        ub = as_unit(passthrough)
        
        # Add edge but don't give func_b any outgoing connections
        edge = g.add(ua, ub)
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        result = stepper.call_one_connection(edge, akw)
        
        # Should handle the None case gracefully
        self.assertIsInstance(result, tuple)

    def test_call_one_fallthrough(self):
        """Test call_one_fallthrough for non-callable objects."""
        g = Graph()
        stepper = StepperC(g)
        
        # Pass a non-callable object
        thing = "not_a_function"
        akw = argspack(5)
        
        result = stepper.call_one_fallthrough(thing, akw)
        
        # Should return a row with None
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], None)

    def test_call_one_partial_connection_no_b_conns(self):
        """Test call_one_partial_connection when B has no connections."""
        g = Graph()
        
        ua = as_unit(passthrough)
        ub = as_unit(multiply_by_2)
        
        edge = make_edge(ua, ub)
        partial = PartialConnection(edge, None, ub)
        
        stepper = StepperC(g)
        akw = argspack(10)
        
        result = stepper.call_one_partial_connection(partial, akw)
        
        # When B has no connections, should call end_branch
        # With stash_ends=True, returns empty tuple
        self.assertIsInstance(result, tuple)

    def test_call_one_delegates_to_call_one_connection_for_edge(self):
        """Test that call_one delegates to call_one_connection when given an edge."""
        g = Graph()
        
        ua = as_unit(multiply_by_2)
        ub = as_unit(passthrough)
        edge = make_edge(ua, ub)
        
        stepper = StepperC(g)
        akw = argspack(5)
        
        with patch.object(stepper, 'call_one_connection', return_value=()) as mock_call:
            stepper.call_one(edge, akw)
            
            mock_call.assert_called_once_with(edge, akw)

    def test_call_one_delegates_to_call_one_callable_for_function(self):
        """Test that call_one delegates to call_one_callable when given a callable."""
        g = Graph()
        
        my_func = lambda v: v * 3
        
        stepper = StepperC(g)
        akw = argspack(10)
        
        with patch.object(stepper, 'call_one_callable', return_value=()) as mock_call:
            stepper.call_one(my_func, akw)
            
            mock_call.assert_called_once_with(my_func, akw)

    def test_call_one_delegates_to_call_one_fallthrough_for_non_callable(self):
        """Test that call_one delegates to call_one_fallthrough for non-callable objects."""
        g = Graph()
        
        thing = {}  # A dict is not callable
        stepper = StepperC(g)
        akw = argspack(5)
        
        with patch.object(stepper, 'call_one_fallthrough', return_value=()) as mock_call:
            stepper.call_one(thing, akw)
            
            mock_call.assert_called_once_with(thing, akw)


class TestStepperNextIterator(unittest.TestCase):
    """Test Stepper.next_iterator method."""

    def test_iter_no_rows(self):
        mock_stepper = MagicMock()
        mock_stepper.start.return_value = ()  # Empty rows triggers StopIteration
        akw = {'id': 1}
        start_nodes = (1,2,3,)
        
        st = StepperIterator(mock_stepper, start_nodes, akw=akw)
        gen = next(st)
        with self.assertRaises(RuntimeError):
            next(gen)
        mock_stepper.start.assert_called_once_with(*start_nodes, akw=akw)

    def test_iter_with_rows(self):
        """Test StepperIterator with rows that eventually exhaust."""
        mock_stepper = MagicMock()
        # First call returns 2 rows, second call returns empty (triggering StopIteration)
        mock_stepper.start.return_value = (
            (lambda x: x, argspack(10)),
            (lambda x: x, argspack(20)),
        )
        mock_stepper.call_rows.return_value = ()  # Empty on second iteration
        
        akw = {'id': 2}
        start_nodes = (4,5,)
        
        st = StepperIterator(mock_stepper, start_nodes, akw=akw)
        gen = next(st)  # Get the generator from __next__
        
        # First yield should return the initial rows
        first_result = next(gen)
        self.assertEqual(first_result, mock_stepper.start.return_value)
        
        # Second call should exhaust (call_rows returns empty, causing StopIteration)
        with self.assertRaises(RuntimeError):
            next(gen)
        
        mock_stepper.start.assert_called_once_with(*start_nodes, akw=akw)

    def test_iter_with_rows_already_set(self):
        """Test StepperIterator when rows are pre-set (bypassing initial start call).
        
        This covers the false branch of 'if self.rows is None' (line 117->119).
        When __next__ is called again after rows have been set, it should skip the start() call.
        """
        mock_stepper = MagicMock()
        
        # Set up start to return initial rows
        initial_rows = (
            (lambda x: x + 1, argspack(10)),
        )
        mock_stepper.start.return_value = initial_rows
        
        # Set up call_rows to return new rows on first call, empty on second
        second_rows = (
            (lambda x: x + 2, argspack(20)),
        )
        mock_stepper.call_rows.side_effect = [second_rows, ()]
        
        akw = argspack(99)
        start_nodes = (lambda x: x * 2,)
        
        # Create iterator
        st = StepperIterator(mock_stepper, start_nodes, akw=akw)
        
        # First call to __next__ - rows is None, so start() is called
        gen1 = next(st)
        first_result = next(gen1)
        self.assertEqual(first_result, initial_rows)
        
        # At this point, self.rows has been set by the while loop
        # Verify start was called once
        self.assertEqual(mock_stepper.start.call_count, 1)
        
        # Continue the generator - this will call call_rows and set self.rows to second_rows
        second_result = next(gen1)
        self.assertEqual(second_result, second_rows)
        
        # Now self.rows is second_rows (not None)
        # Call __next__ again - this should skip the 'if self.rows is None' block
        # and go directly to the while loop
        gen2 = next(st)
        
        # This should yield second_rows immediately without calling start() again
        third_result = next(gen2)
        self.assertEqual(third_result, second_rows)
        
        # start() should still only have been called once (from the first __next__)
        self.assertEqual(mock_stepper.start.call_count, 1)

class TestStepperEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_step_without_start_nodes_raises(self):
        """Test that stepping without start_nodes raises a StepperException."""
        g = Graph()
        stepper = StepperC(g)
        
        # Don't set start_nodes
        with self.assertRaises(StepperException) as context:
            stepper.step()
        
        self.assertIn('start_nodes is None', str(context.exception))

    def test_stepper_with_initial_rows(self):
        """Test creating a stepper with initial rows."""
        g = Graph()
        
        unit = as_unit(passthrough)
        initial_rows = ((unit, argspack(5)),)
        
        stepper = StepperC(g, rows=initial_rows)
        
        self.assertEqual(stepper.rows, initial_rows)

    def test_no_branch(self):
        """Test no_branch method."""
        g = Graph()
        stepper = StepperC(g)
        stepper.stash_ends = False
        
        akw = argspack(100)
        result = stepper.no_branch(None, akw)
        
        # Should delegate to end_branch
        self.assertIsInstance(result, tuple)

    def test_end_branch_with_stash_disabled(self):
        """Test end_branch when stash_ends is False."""
        g = Graph()
        stepper = StepperC(g)
        stepper.stash_ends = False
        
        akw = argspack(50)
        result = stepper.end_branch(None, akw)
        
        # Should return a row with None
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], None)

    def test_end_branch_with_stash_enabled(self):
        """Test end_branch when stash_ends is True."""
        g = Graph()
        stepper = StepperC(g)
        stepper.stash_ends = True
        
        func = noop
        
        akw = argspack(75)
        result = stepper.end_branch(func, akw)
        
        # Should add to stash and return empty tuple
        self.assertEqual(len(result), 0)
        self.assertIn(func, stepper.stash)

    def test_iterator_method(self):
        """Test the iterator() method creates StepperIterator."""
        g = Graph()
        
        unit = as_unit(passthrough)
        
        stepper = StepperC(g)
        stepper.prepare(unit, akw=argspack(10))
        
        iterator = stepper.iterator()
        
        self.assertIsInstance(iterator, StepperIterator)

    def test_iterator_with_explicit_params(self):
        """Test iterator() with explicit parameters."""
        g = Graph()
        
        unit = as_unit(passthrough)
        
        stepper = StepperC(g)
        akw = argspack(20)
        
        iterator = stepper.iterator(unit, akw=akw)
        
        self.assertIsInstance(iterator, StepperIterator)
        self.assertEqual(iterator.start_nodes, (unit,))


class TestFlushAndPeek(unittest.TestCase):
    """Test flush and peek operations on the stepper."""

    def test_flush_yields_stash_contents(self):
        """Test that flush yields all stash contents."""
        g = Graph()
        stepper = StepperC(g)
        
        # Manually populate stash
        func_a = lambda: None
        func_b = lambda: None
        
        stepper.stash[func_a] = (argspack(10), argspack(20))
        stepper.stash[func_b] = (argspack(30),)
        
        results = list(stepper.flush())
        
        # Should yield all entries
        self.assertEqual(len(results), 2)
        
        # After flush, stash should be reset
        self.assertEqual(len(stepper.stash), 0)

    def test_peek_yields_values(self):
        """Test that peek yields stash values without clearing."""
        g = Graph()
        stepper = StepperC(g)
        
        # Populate stash
        func_a = lambda: None
        func_b = lambda: None
        
        stepper.stash[func_a] = (argspack(10),)
        stepper.stash[func_b] = (argspack(20),)
        
        results = list(stepper.peek())
        
        # Should yield values
        self.assertEqual(len(results), 2)
        
        # Stash should still be populated (peek doesn't clear)
        self.assertEqual(len(stepper.stash), 2)

    def test_flush_empties_stash(self):
        """Test that flush clears the stash."""
        g = Graph()
        stepper = StepperC(g)
        
        func = lambda: None
        stepper.stash[func] = (argspack(100),)
        
        # Consume flush generator
        list(stepper.flush())
        
        # Stash should be empty
        self.assertEqual(len(stepper.stash), 0)


class TestConcatAware(unittest.TestCase):
    """Test concat_aware mode integration."""

    def test_call_rows_with_concat_aware(self):
        """Test that call_rows uses row_concat when concat_aware=True."""
        g = Graph()
        
        def merger(*args):
            return sum(args)
        
        merge_unit = as_unit(merger)
        merge_unit.merge_node = True
        
        stepper = StepperC(g)
        stepper.concat_aware = True
        
        # Multiple rows to same merge node
        rows = (
            (merge_unit, argspack(5)),
            (merge_unit, argspack(10)),
        )
        
        # This should trigger row_concat
        result = stepper.call_rows(rows)
        
        # Should process the rows
        self.assertIsInstance(result, tuple)

    def test_call_rows_without_concat_aware(self):
        """Test call_rows behavior when concat_aware=False."""
        g = Graph()
        
        unit = as_unit(passthrough)
        
        stepper = StepperC(g)
        stepper.concat_aware = False
        
        rows = (
            (unit, argspack(1)),
            (unit, argspack(2)),
        )
        
        result = stepper.call_rows(rows)
        
        # Should process normally without concat
        self.assertIsInstance(result, tuple)


class TestStepperDunderIter(unittest.TestCase):
    """Test the __iter__ method."""

    def test_stepper_iter(self):
        """Test that __iter__ calls iterator and returns a generator."""
        g = Graph()
        
        unit = as_unit(passthrough)
        
        stepper = StepperC(g)
        stepper.prepare(unit, akw=argspack(5))
        
        # __iter__ returns next(iterator()) which is a generator
        result = iter(stepper)
        
        # Result should be a generator from StepperIterator.__next__
        # The __iter__ method returns next(self.iterator()), which yields a generator
        self.assertIsNotNone(result)
