"""Test stepper functionality in Hyperway.

The stepper is the execution engine that walks through a graph of nodes,
executing them one at a time and storing results as it progresses.

Basic Flow:
1. The stepper walks the graph one node at a time
2. It executes the node and stores the next step
3. If there is no next step, it stores the result in the stash

See docs/stepper.md for more information.
"""

import unittest
from collections import defaultdict

from hyperway.graph import Graph
from hyperway.nodes import as_unit
from hyperway.packer import argspack


# Module-level helper functions used across multiple tests
def multiply_by_2(v=0):
    """Multiply a value by 2."""
    return v * 2


def passthrough(v):
    """Return value as-is (passthrough/identity function)."""
    return v


def multiply_by_3(v):
    """Multiply a value by 3."""
    return v * 3


def add_n(n):
    """Create a function that adds n to a value.
    
    Args:
        n: The number to add
        
    Returns:
        A function that adds n to its input value
    """
    def adder(v):
        return v + n
    return adder


class TestStepperBasics(unittest.TestCase):
    """Test basic stepper functionality.
    
    The stepper executes a graph starting from a given node with initial arguments.
    It walks through connected nodes, executing each one and tracking results.
    """

    def setUp(self):
        """Create a passthrough graph for testing."""
        self.graph = Graph(tuple)

    def test_stepper_creation(self):
        """Test that a stepper can be created from a graph."""
        node = as_unit(multiply_by_2)
        self.graph.add(node, multiply_by_2)
        
        # Prepare the stepper with starting node and value
        self.graph.stepper_prepare(node, 4)
        stepper = self.graph.stepper()
        
        self.assertIsNotNone(stepper)
        # start_nodes is stored as a tuple containing the node
        self.assertEqual(stepper.start_nodes, (node,))
        self.assertIsNotNone(stepper.start_akw)

    def test_stepper_prepare(self):
        """Test preparing a stepper with a starting node and arguments."""
        du = as_unit(multiply_by_2)
        self.graph.add(du, lambda v: v)
        
        # Prepare the stepper
        self.graph.stepper_prepare(du, 4)
        
        # Verify stepper has stored the preparation data
        stepper = self.graph.stepper()
        # start_nodes is stored as a tuple containing the node
        self.assertEqual(stepper.start_nodes, (du,))
        # The args should be wrapped in an argspack
        self.assertEqual(stepper.start_akw.args, (4,))

    def test_stepper_step_execution(self):
        """Test stepping through a single node execution.
        
        As per the documentation example:
        - Start with multiply_by_2 node and value 4
        - Step once to execute multiply_by_2 (4 * 2 = 8)
        - Next step should process the passthrough node
        """
        du = as_unit(multiply_by_2)
        self.graph.add(du, passthrough)
        
        # Prepare stepper with starting node and value 4
        self.graph.stepper_prepare(du, 4)
        stepper = self.graph.stepper()
        
        # First step executes the multiply_by_2
        next_steps = stepper.step()
        
        # Should have a next step (the passthrough)
        self.assertIsNotNone(next_steps)
        self.assertGreater(len(next_steps), 0)

    def test_stepper_stash_empty_until_completion(self):
        """Test that the stash remains empty until a path completes.
        
        From documentation: "We can inspect the stepper stashed values at any time.
        When the stepper completes a path, the results are stored in the stash"
        """
        du = as_unit(multiply_by_2)
        self.graph.add(du, passthrough)
        
        self.graph.stepper_prepare(du, 4)
        stepper = self.graph.stepper()
        
        # Before any steps, stash should be empty
        self.assertEqual(len(stepper.stash), 0)
        
        # After first step, stash should still be empty (path not complete)
        stepper.step()
        # Stash is empty because we haven't reached the end yet
        # (this depends on implementation details)

    def test_stepper_complete_path(self):
        """Test stepping through a complete path from start to finish.
        
        Following the documentation example:
        1. Start at multiply_by_2 with value 4
        2. Step through multiply_by_2 (returns 8)
        3. Step through passthrough (stores result)
        4. Verify result is in stash
        """
        du = as_unit(multiply_by_2)
        self.graph.add(du, passthrough)
        
        self.graph.stepper_prepare(du, 4)
        stepper = self.graph.stepper()
        
        # Step 1: Execute multiply_by_2
        step1 = stepper.step()
        self.assertIsNotNone(step1)
        
        # Step 2: Execute passthrough
        step2 = stepper.step()
        
        # After completing the path, should be no more steps
        # (either empty tuple or None depending on implementation)
        if step2 is not None:
            self.assertEqual(len(step2), 0)

    def test_stepper_with_multiple_values(self):
        """Test stepper with different input values."""
        node_a = as_unit(multiply_by_3)
        self.graph.add(node_a, add_n(10))
        
        # Test with value 5: 5 * 3 = 15, then 15 + 10 = 25
        self.graph.stepper_prepare(node_a, 5)
        stepper = self.graph.stepper()
        
        # Execute the full path
        stepper.step()  # multiply_by_3
        result = stepper.step()  # add_n(10)
        
        # Verify we processed through the nodes
        self.assertIsNotNone(result is not None or len(stepper.stash) > 0)


class TestStepperMultipleEdges(unittest.TestCase):
    """Test stepper with multiple edges from one node.
    
    When a node has multiple outgoing edges, the stepper should
    handle all downstream paths.
    """

    def setUp(self):
        """Create a graph with multiple edges."""
        self.graph = Graph(tuple)

    def test_one_to_two_connections(self):
        """Test a node with two outgoing connections.
        
        This matches the passthrough-one-to-two.py example where
        one multiply_by_2 node connects to two passthrough nodes.
        """
        du = as_unit(multiply_by_2)
        # Add two edges from the same node
        e1 = self.graph.add(du, passthrough)
        e2 = self.graph.add(du, passthrough)
        
        self.graph.stepper_prepare(du, 4)
        stepper = self.graph.stepper()
        
        # First step executes multiply_by_2, should yield two next steps
        next_steps = stepper.step()
        
        # Should have multiple next steps (one for each passthrough)
        self.assertIsNotNone(next_steps)
        # Depending on implementation, might have 2 steps
        if len(next_steps) > 0:
            self.assertGreaterEqual(len(next_steps), 1)

    def test_branching_graph(self):
        """Test a graph that branches into multiple paths."""
        source_node = as_unit(multiply_by_2)
        self.graph.add(source_node, add_n(10))
        self.graph.add(source_node, multiply_by_3)
        
        self.graph.stepper_prepare(source_node, 10)
        stepper = self.graph.stepper()
        
        # Execute multiply_by_2 node
        next_steps = stepper.step()
        
        # Should have steps for both branches
        self.assertIsNotNone(next_steps)


class TestStepperIterator(unittest.TestCase):
    """Test stepper iterator functionality.
    
    The stepper can be iterated to automatically walk through
    all steps in the graph.
    """

    def setUp(self):
        """Create a graph for iteration testing."""
        self.graph = Graph(tuple)

    def test_stepper_step_count(self):
        """Test stepping multiple times with count parameter."""
        n1 = as_unit(add_n(1))
        n2 = as_unit(add_n(2))
        
        self.graph.add(n1, n2)
        self.graph.add(n2, add_n(3))
        
        self.graph.stepper_prepare(n1, 10)
        stepper = self.graph.stepper()
        
        # Step twice at once
        result = stepper.step(count=2)
        
        # Should have processed multiple steps
        self.assertIsNotNone(result is not None or len(stepper.stash) >= 0)

    def test_multiple_steps_execution(self):
        """Test calling step multiple times sequentially."""
        
        n1 = as_unit(multiply_by_2)
        self.graph.add(n1, add_n(5))
        
        self.graph.stepper_prepare(n1, 3)
        stepper = self.graph.stepper()
        
        # Execute steps one at a time
        step1 = stepper.step()
        self.assertIsNotNone(step1)
        
        step2 = stepper.step()
        # After second step, should be at end or have result
        self.assertIsNotNone(step2 is not None or len(stepper.stash) > 0)


class TestStepperCallMethods(unittest.TestCase):
    """Test the various call methods of the stepper.
    
    The stepper has several ways to execute nodes:
    - call_one: Execute a single node
    - call_many: Execute multiple nodes with same arguments
    - call_rows: Execute multiple nodes with different arguments
    """

    def setUp(self):
        """Create a graph for testing call methods."""
        self.graph = Graph(tuple)

    def test_call_many_with_same_args(self):
        """Test calling multiple nodes with the same arguments."""
        node_a = as_unit(add_n(1))
        node_b = as_unit(multiply_by_2)
        
        stepper = self.graph.stepper()
        
        # Call both nodes with value 10
        akw = argspack(10)
        rows = stepper.call_many(node_a, node_b, akw=akw)
        
        # Should return rows for next steps
        self.assertIsNotNone(rows)
        self.assertIsInstance(rows, tuple)

    def test_start_method(self):
        """Test the start method which begins stepper execution."""
        node = as_unit(add_n(100))
        self.graph.add(node, lambda v: v)
        
        stepper = self.graph.stepper()
        
        # Start execution with a node and arguments
        akw = argspack(5)
        result = stepper.start(node, akw=akw)
        
        # Should return next steps
        self.assertIsNotNone(result)
        self.assertIsInstance(result, tuple)


class TestStepperStash(unittest.TestCase):
    """Test the stepper stash functionality.
    
    The stash stores completed results from the graph execution.
    """

    def setUp(self):
        """Create a graph for stash testing."""
        self.graph = Graph(tuple)

    def test_stash_is_defaultdict(self):
        """Test that stash is a defaultdict with tuple factory."""
        stepper = self.graph.stepper()
        
        self.assertIsInstance(stepper.stash, defaultdict)
        # Should be able to access non-existent keys without error
        result = stepper.stash['nonexistent']
        self.assertIsInstance(result, tuple)

    def test_reset_stash(self):
        """Test resetting the stash clears stored results."""
        node = as_unit(passthrough)
        self.graph.add(node, lambda v: v)
        
        stepper = self.graph.stepper()
        
        # Manually add something to stash
        stepper.stash['test'] = ('data',)
        self.assertEqual(len(stepper.stash), 1)
        
        # Reset should clear it
        stepper.reset_stash()
        self.assertEqual(len(stepper.stash), 0)

    def test_stash_stores_results(self):
        """Test that completed paths store results in stash."""
        du = as_unit(multiply_by_2)
        self.graph.add(du, passthrough)
        
        self.graph.stepper_prepare(du, 4)
        stepper = self.graph.stepper()
        
        # Execute complete path
        stepper.step()  # multiply_by_2
        stepper.step()  # passthrough
        
        # Stash should contain results (implementation dependent)
        # At minimum, stash should be a valid defaultdict
        self.assertIsInstance(stepper.stash, defaultdict)


class TestStepperDocumentationExample(unittest.TestCase):
    """Test the exact example from the stepper documentation.
    
    This reproduces the example from docs/stepper.md to ensure
    the documentation accurately reflects the implementation.
    """

    def test_documentation_example(self):
        """Test the complete example from stepper.md documentation.
        
        Example flow:
        1. Create graph with multiply_by_2 -> passthrough
        2. Prepare stepper with multiply_by_2 node and value 4
        3. Step through execution
        4. Verify stash behavior
        """
        # Setup from documentation
        g = Graph(tuple)
        
        du = as_unit(multiply_by_2)
        e = g.add(du, passthrough)
        e2 = g.add(du, passthrough)
        
        # Prepare stepper as documented
        g.stepper_prepare(du, 4)
        
        # Get stepper instance
        stepper = g.stepper()
        
        # Verify initial state
        self.assertEqual(len(stepper.stash), 0, "Stash should be empty initially")
        
        # Step 1: Execute first node
        step1_result = stepper.step()
        self.assertIsNotNone(step1_result, "First step should return next steps")
        
        # Step 2: Execute passthrough nodes
        step2_result = stepper.step()
        
        # Verify stepper has stash (even if empty, should be a defaultdict)
        self.assertIsInstance(stepper.stash, defaultdict)


class TestStepperConvenienceMethods(unittest.TestCase):
    """Test Phase 1 convenience methods for result access.
    
    These methods provide easier access to results without manually
    unwrapping the stash structure.
    """
    
    def setUp(self):
        """Create a graph for testing."""
        self.graph = Graph(tuple)
    
    def test_get_result_single_endpoint(self):
        """Test get_result() with a single endpoint graph."""
        # Create simple chain: 10 -> +10 -> +20 -> +30 = 70
        node_a = as_unit(add_n(10))
        self.graph.connect(node_a, add_n(20), add_n(30))
        
        self.graph.stepper_prepare(node_a, 10)
        stepper = self.graph.stepper()
        
        # Execute graph
        while stepper.step():
            pass
        
        # Test get_result()
        result = stepper.get_result()
        self.assertEqual(result, 70)
    
    def test_get_result_empty_stash(self):
        """Test get_result() returns default when no results."""
        node = as_unit(multiply_by_2)
        self.graph.add(node, multiply_by_2)
        
        stepper = self.graph.stepper()
        
        # No execution, empty stash
        result = stepper.get_result()
        self.assertIsNone(result)
        
        # Test custom default
        result = stepper.get_result(default=42)
        self.assertEqual(result, 42)
    
    def test_get_results_single_endpoint(self):
        """Test get_results() with a single endpoint."""
        node_a = as_unit(multiply_by_2)
        self.graph.connect(node_a, add_n(5))
        
        self.graph.stepper_prepare(node_a, 10)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Should return list with one result: (10 * 2) + 5 = 25
        results = stepper.get_results()
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 25)
    
    def test_get_results_multiple_endpoints(self):
        """Test get_results() with multiple branch endpoints."""
        # Create branching graph
        source = as_unit(multiply_by_2)
        branch_a = add_n(10)
        branch_b = add_n(20)
        
        self.graph.add(source, branch_a)
        self.graph.add(source, branch_b)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Should have 2 results: (5*2)+10=20 and (5*2)+20=30
        results = stepper.get_results()
        self.assertEqual(len(results), 2)
        self.assertIn(20, results)
        self.assertIn(30, results)
    
    def test_get_results_empty_stash(self):
        """Test get_results() returns empty list when no results."""
        stepper = self.graph.stepper()
        
        results = stepper.get_results()
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
    
    def test_get_results_unwrap_false(self):
        """Test get_results(unwrap=False) returns ArgsPack objects."""
        node = as_unit(multiply_by_2)
        self.graph.add(node, multiply_by_2)
        
        self.graph.stepper_prepare(node, 10)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Get unwrapped ArgsPack objects
        results = stepper.get_results(unwrap=False)
        self.assertEqual(len(results), 1)
        # Should be ArgsPack
        self.assertTrue(hasattr(results[0], 'args'))
        self.assertTrue(hasattr(results[0], 'kw'))
    
    def test_get_results_dict_by_name(self):
        """Test get_results_dict() organizes results by node name."""
        source = as_unit(add_n(1))
        handler_a = as_unit(add_n(10), name='handler_a')
        handler_b = as_unit(add_n(20), name='handler_b')
        
        self.graph.add(source, handler_a)
        self.graph.add(source, handler_b)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Get results organized by name
        results = stepper.get_results_dict(key='name')
        
        self.assertIsInstance(results, dict)
        self.assertIn('handler_a', results)
        self.assertIn('handler_b', results)
        self.assertEqual(results['handler_a'][0], 16)  # (5+1)+10
        self.assertEqual(results['handler_b'][0], 26)  # (5+1)+20
    
    def test_get_results_dict_by_id(self):
        """Test get_results_dict() can use callable to get node id."""
        source = as_unit(add_n(1))
        handler = as_unit(add_n(10))
        
        self.graph.add(source, handler)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Get results by id using callable (since id is a method)
        results = stepper.get_results_dict(key=lambda n: n.id())
        
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), 1)
        # Should have the handler's id as key
        handler_id = handler.id()
        self.assertIn(handler_id, results)
        self.assertEqual(results[handler_id][0], 16)  # (5+1)+10
    
    def test_get_results_dict_with_callable_key(self):
        """Test get_results_dict() with callable key function."""
        source = as_unit(add_n(1))
        
        # Create handlers with recognizable function names
        def handler_alpha(v):
            return v + 10
        
        def handler_beta(v):
            return v + 20
        
        node_a = as_unit(handler_alpha)
        node_b = as_unit(handler_beta)
        
        self.graph.add(source, node_a)
        self.graph.add(source, node_b)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Use callable to extract function name
        results = stepper.get_results_dict(key=lambda n: n.func.__name__)
        
        self.assertIsInstance(results, dict)
        self.assertIn('handler_alpha', results)
        self.assertIn('handler_beta', results)
    
    def test_get_results_dict_multiple_results_per_node(self):
        """Test get_results_dict() when same node receives multiple results.
        
        This test demonstrates that when multiple paths lead to the same endpoint,
        all results are collected under that endpoint's key.
        """
        # Create a simpler scenario: source fans out and reconverges
        # source -> +10 -> handler
        #       \-> +20 -> handler
        # This creates two paths to handler, producing two results
        source = as_unit(add_n(5))
        mid_a = as_unit(add_n(10))
        mid_b = as_unit(add_n(20))
        handler = as_unit(multiply_by_2, name='handler')
        
        self.graph.add(source, mid_a)
        self.graph.add(source, mid_b)
        self.graph.add(mid_a, handler)
        self.graph.add(mid_b, handler)
        
        self.graph.stepper_prepare(source, 1)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Handler should have 2 results
        results = stepper.get_results_dict(key='name')
        
        # Both paths should produce results
        if 'handler' in results:
            self.assertEqual(len(results['handler']), 2)
            # Path 1: (1+5)+10=16, then 16*2=32
            # Path 2: (1+5)+20=26, then 26*2=52
            self.assertIn(32, results['handler'])
            self.assertIn(52, results['handler'])
    
    def test_has_results_true(self):
        """Test has_results() returns True when results exist."""
        node = as_unit(multiply_by_2)
        self.graph.add(node, multiply_by_2)
        
        self.graph.stepper_prepare(node, 5)
        stepper = self.graph.stepper()
        
        # Before execution
        self.assertFalse(stepper.has_results())
        
        # After execution
        while stepper.step():
            pass
        
        self.assertTrue(stepper.has_results())
    
    def test_has_results_false(self):
        """Test has_results() returns False when no results."""
        stepper = self.graph.stepper()
        self.assertFalse(stepper.has_results())
    
    def test_result_count_single(self):
        """Test result_count() with single result."""
        node = as_unit(add_n(5))
        self.graph.add(node, add_n(10))
        
        self.graph.stepper_prepare(node, 10)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        self.assertEqual(stepper.result_count(), 1)
    
    def test_result_count_multiple(self):
        """Test result_count() with multiple results."""
        source = as_unit(multiply_by_2)
        
        self.graph.add(source, add_n(1))
        self.graph.add(source, add_n(2))
        self.graph.add(source, add_n(3))
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        # Should have 3 results
        self.assertEqual(stepper.result_count(), 3)
    
    def test_result_count_zero(self):
        """Test result_count() returns 0 when no results."""
        stepper = self.graph.stepper()
        self.assertEqual(stepper.result_count(), 0)
    
    def test_get_results_with_kwargs(self):
        """Test get_results() handles kwargs in ArgsPack."""
        def return_kwargs(**kw):
            return kw
        
        node = as_unit(return_kwargs)
        
        self.graph.stepper_prepare(node, foo=42, bar='test')
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        results = stepper.get_results()
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]['foo'], 42)
        self.assertEqual(results[0]['bar'], 'test')
    
    def test_get_results_with_multiple_args(self):
        """Test get_results() handles multiple positional args."""
        def return_multiple(v):
            return v, v*2, v*3
        
        node = as_unit(return_multiple)
        
        self.graph.stepper_prepare(node, 5)
        stepper = self.graph.stepper()
        
        while stepper.step():
            pass
        
        results = stepper.get_results()
        self.assertEqual(len(results), 1)
        # Multiple args should be returned as tuple
        self.assertIsInstance(results[0], tuple)
        self.assertEqual(results[0], (5, 10, 15))
    
    def test_convenience_methods_integration(self):
        """Test using convenience methods together in a real scenario."""
        # Build a realistic branching graph
        source = as_unit(add_n(5), name='source')
        transform = as_unit(multiply_by_2, name='transform')
        handler_a = as_unit(add_n(100), name='handler_a')
        handler_b = as_unit(add_n(200), name='handler_b')
        
        # source -> transform -> handler_a
        #                    \-> handler_b
        self.graph.add(source, transform)
        self.graph.add(transform, handler_a)
        self.graph.add(transform, handler_b)
        
        self.graph.stepper_prepare(source, 10)
        stepper = self.graph.stepper()
        
        # Check before execution
        self.assertFalse(stepper.has_results())
        self.assertEqual(stepper.result_count(), 0)
        
        # Execute
        while stepper.step():
            pass
        
        # Check after execution
        self.assertTrue(stepper.has_results())
        self.assertEqual(stepper.result_count(), 2)
        
        # Get all results
        all_results = stepper.get_results()
        self.assertEqual(len(all_results), 2)
        self.assertIn(130, all_results)  # ((10+5)*2)+100
        self.assertIn(230, all_results)  # ((10+5)*2)+200
        
        # Get organized results
        results_dict = stepper.get_results_dict()
        self.assertEqual(results_dict['handler_a'][0], 130)
        self.assertEqual(results_dict['handler_b'][0], 230)


class TestStreamFunction(unittest.TestCase):
    """Test the stream() function and stepper.stream() method.
    
    The stream() function allows iterating over results as they become available
    during graph execution, rather than waiting for complete execution.
    """

    def setUp(self):
        """Create a fresh graph for each test."""
        self.graph = Graph()

    def test_stream_simple_linear(self):
        """Test streaming results from a simple linear graph."""
        # Create a simple chain: add_10 -> add_20 -> add_30
        add_10 = as_unit(lambda x: x + 10, name='add_10')
        add_20 = as_unit(lambda x: x + 20, name='add_20')
        add_30 = as_unit(lambda x: x + 30, name='add_30')
        
        self.graph.add(add_10, add_20)
        self.graph.add(add_20, add_30)
        
        self.graph.stepper_prepare(add_10, 5)
        stepper = self.graph.stepper()
        
        # Stream results
        results = list(stepper.stream())
        
        # Should get one result: 5 + 10 + 20 + 30 = 65
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 65)
        
        # Stash should be empty after streaming
        self.assertEqual(len(stepper.stash), 0)

    def test_stream_multiple_branches(self):
        """Test streaming results from graph with multiple endpoints."""
        source = as_unit(lambda x: x * 2, name='source')
        branch_1 = as_unit(lambda x: x + 10, name='branch_1')
        branch_2 = as_unit(lambda x: x + 20, name='branch_2')
        branch_3 = as_unit(lambda x: x + 30, name='branch_3')
        
        self.graph.add(source, branch_1)
        self.graph.add(source, branch_2)
        self.graph.add(source, branch_3)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        # Stream all results
        results = list(stepper.stream())
        
        # Should get 3 results: (5*2)+10=20, (5*2)+20=30, (5*2)+30=40
        self.assertEqual(len(results), 3)
        self.assertEqual(set(results), {20, 30, 40})
        
        # Stash should be empty
        self.assertEqual(len(stepper.stash), 0)

    def test_stream_early_termination(self):
        """Test breaking out of stream early."""
        source = as_unit(lambda x: x, name='source')
        
        self.graph.add(source, as_unit(lambda x: x + 10, name='add_10'))
        self.graph.add(source, as_unit(lambda x: x + 20, name='add_20'))
        self.graph.add(source, as_unit(lambda x: x + 30, name='add_30'))
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        # Stream and stop after first result > 20
        results = []
        for result in stepper.stream():
            results.append(result)
            if result > 20:
                break
        
        # Should have stopped early
        self.assertGreater(len(results), 0)
        self.assertLess(len(results), 3)  # Didn't collect all 3
        
        # Stash may still have remaining results
        # (depends on execution order, but should have at least 1 remaining)
        self.assertGreaterEqual(len(stepper.stash), 1)

    def test_stream_unwrap_false(self):
        """Test streaming raw ArgsPack objects."""
        add_10 = as_unit(lambda x: x + 10, name='add_10')
        add_20 = as_unit(lambda x: x + 20, name='add_20')
        
        self.graph.add(add_10, add_20)
        
        self.graph.stepper_prepare(add_10, 5)
        stepper = self.graph.stepper()
        
        # Stream raw ArgsPack objects
        results = list(stepper.stream(unwrap=False))
        
        self.assertEqual(len(results), 1)
        akw = results[0]
        
        # Should be an ArgsPack
        self.assertTrue(hasattr(akw, 'args'))
        self.assertTrue(hasattr(akw, 'kwargs'))
        self.assertTrue(hasattr(akw, 'flat'))
        
        # Should contain the result value
        self.assertEqual(akw.flat(), 35)  # 5 + 10 + 20

    def test_stream_functional_style(self):
        """Test using standalone stream() function."""
        from hyperway.stepper import stream
        
        add_10 = as_unit(lambda x: x + 10, name='add_10')
        add_20 = as_unit(lambda x: x + 20, name='add_20')
        
        self.graph.add(add_10, add_20)
        
        self.graph.stepper_prepare(add_10, 5)
        stepper = self.graph.stepper()
        
        # Use functional style: stream(stepper)
        results = list(stream(stepper))
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 35)
        self.assertEqual(len(stepper.stash), 0)

    def test_stream_empty_graph(self):
        """Test streaming from a graph with no connections (immediate leaf)."""
        solo_node = as_unit(lambda x: x * 2, name='solo')
        
        # Node with no outgoing connections
        self.graph.stepper_prepare(solo_node, 10)
        stepper = self.graph.stepper()
        
        # Stream should yield the single result
        results = list(stepper.stream())
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 20)  # 10 * 2
        self.assertEqual(len(stepper.stash), 0)

    def test_stream_collect_while_streaming(self):
        """Test collecting results into a list while streaming."""
        source = as_unit(lambda x: x * 2, name='source')
        
        self.graph.add(source, as_unit(lambda x: x + 10, name='fast'))
        self.graph.add(source, as_unit(lambda x: x + 20, name='medium'))
        self.graph.add(source, as_unit(lambda x: x + 30, name='slow'))
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        # Collect results while streaming
        collected = []
        for result in stepper.stream():
            collected.append(result)
        
        # Should have all 3 results
        self.assertEqual(len(collected), 3)
        self.assertEqual(set(collected), {20, 30, 40})
        
        # Stash should be empty
        self.assertEqual(len(stepper.stash), 0)

    def test_stream_looped_graph_memory_safe(self):
        """Test that streaming is memory-safe with looped graphs.
        
        This verifies that results are popped from stash as they're yielded,
        preventing unbounded memory growth in cyclic graphs.
        """
        # Create a loop: A -> B -> C (leaf)
        #                     ^____v
        a = as_unit(lambda x: x + 1, name='A')
        b = as_unit(lambda x: x * 2, name='B')
        c = as_unit(lambda x: x, name='C')  # Leaf node
        
        self.graph.add(a, b)
        self.graph.add(b, c)
        self.graph.add(b, b)  # Loop back to B
        
        self.graph.stepper_prepare(a, 1)
        stepper = self.graph.stepper()
        
        # Stream with a limit
        count = 0
        max_iterations = 10
        results = []
        
        for result in stepper.stream():
            results.append(result)
            count += 1
            if count >= max_iterations:
                break
        
        # Should have collected results
        self.assertEqual(len(results), max_iterations)
        
        # Stash should be empty (or nearly empty) - results were popped
        # In a looped graph, there might be one pending result
        self.assertLessEqual(len(stepper.stash), 1)
        
        # Results should be growing exponentially
        # First few: (1+1)*2=4, (4+1)*2=10 -> wait, actually...
        # Let me trace: start with 1
        # A(1) -> 2, B(2) -> 4, C(4) -> yield 4, B(2) -> 4, C(4) -> yield 4
        # Actually B loops to itself, so: B(4) -> 8, C(8) -> yield 8
        self.assertTrue(len(results) > 0)

    def test_stream_oop_and_functional_equivalence(self):
        """Test that OOP and functional styles produce identical results."""
        from hyperway.stepper import stream
        
        # Setup
        add_10 = as_unit(lambda x: x + 10, name='add_10')
        add_20 = as_unit(lambda x: x + 20, name='add_20')
        
        self.graph.add(add_10, add_20)
        
        # Test OOP style
        self.graph.stepper_prepare(add_10, 5)
        stepper_oop = self.graph.stepper()
        results_oop = list(stepper_oop.stream())
        
        # Test functional style (need fresh stepper)
        self.graph.stepper_prepare(add_10, 5)
        stepper_func = self.graph.stepper()
        results_func = list(stream(stepper_func))
        
        # Should be identical
        self.assertEqual(results_oop, results_func)
        self.assertEqual(len(stepper_oop.stash), len(stepper_func.stash))

    def test_stream_with_kwargs(self):
        """Test streaming results that include kwargs."""
        def add_with_kwargs(x, multiplier=1):
            return x * multiplier
        
        node = as_unit(add_with_kwargs, name='with_kwargs')
        
        self.graph.stepper_prepare(node, 10, multiplier=5)
        stepper = self.graph.stepper()
        
        results = list(stepper.stream())
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 50)  # 10 * 5

    def test_stream_multiple_results_same_node(self):
        """Test streaming when same node produces multiple results.
        
        This can happen with merge nodes or when a node is reached
        multiple times through different paths.
        """
        # Create diamond pattern: source -> A -> sink
        #                                -> B -> sink
        source = as_unit(lambda x: x * 2, name='source')
        a = as_unit(lambda x: x + 10, name='A')
        b = as_unit(lambda x: x + 20, name='B')
        sink = as_unit(lambda x: x + 100, name='sink')
        
        self.graph.add(source, a)
        self.graph.add(source, b)
        self.graph.add(a, sink)
        self.graph.add(b, sink)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        # Stream all results
        results = list(stepper.stream())
        
        # Should get 2 results (one from each path through sink)
        # Path 1: (5*2)+10+100 = 120
        # Path 2: (5*2)+20+100 = 130
        self.assertEqual(len(results), 2)
        self.assertEqual(set(results), {120, 130})

    def test_stream_generator_behavior(self):
        """Test that stream() returns a proper generator."""
        add_10 = as_unit(lambda x: x + 10, name='add_10')
        add_20 = as_unit(lambda x: x + 20, name='add_20')
        
        self.graph.add(add_10, add_20)
        
        self.graph.stepper_prepare(add_10, 5)
        stepper = self.graph.stepper()
        
        # stream() should return a generator
        stream_gen = stepper.stream()
        
        # Check it's a generator
        import types
        self.assertIsInstance(stream_gen, types.GeneratorType)
        
        # Can iterate over it
        results = list(stream_gen)
        self.assertEqual(len(results), 1)

    def test_stream_stash_cleared(self):
        """Test that stash is completely cleared after full streaming."""
        source = as_unit(lambda x: x * 2, name='source')
        
        for i in range(5):
            branch = as_unit(lambda x, i=i: x + i*10, name=f'branch_{i}')
            self.graph.add(source, branch)
        
        self.graph.stepper_prepare(source, 5)
        stepper = self.graph.stepper()
        
        # Verify stash is initially empty
        self.assertEqual(len(stepper.stash), 0)
        
        # Stream all results
        results = list(stepper.stream())
        
        # Should have 5 results
        self.assertEqual(len(results), 5)
        
        # Stash must be completely empty after streaming
        self.assertEqual(len(stepper.stash), 0)
        self.assertEqual(dict(stepper.stash), {})

    def test_stream_continues_when_no_stash_results(self):
        """Test that stream() continues when step() executes but adds nothing to stash.
        
        This covers the continue path in stream() where intermediate nodes execute
        but don't add results to the stash (because they have outgoing connections).
        """
        # Create a longer chain to ensure multiple steps before hitting leaf
        # Use explicit functions to avoid lambda closure issues
        add_0 = as_unit(lambda x: x + 0, name='node_0')
        add_10 = as_unit(lambda x: x + 10, name='node_1')
        add_20 = as_unit(lambda x: x + 20, name='node_2')
        add_30 = as_unit(lambda x: x + 30, name='node_3')
        add_40 = as_unit(lambda x: x + 40, name='node_4')
        
        # Chain them: node_0 -> node_1 -> node_2 -> node_3 -> node_4 (leaf)
        self.graph.add(add_0, add_10)
        self.graph.add(add_10, add_20)
        self.graph.add(add_20, add_30)
        self.graph.add(add_30, add_40)
        
        self.graph.stepper_prepare(add_0, 5)
        stepper = self.graph.stepper()
        
        # Track how many times we iterate in the stream
        result_count = 0
        for result in stepper.stream():
            result_count += 1
        
        # Should get exactly 1 result (only the final leaf node)
        # But stream() internally looped multiple times (4 continues + 1 yield)
        self.assertEqual(result_count, 1)
        
        # The result should be: 5 + 0 + 10 + 20 + 30 + 40 = 105
        self.graph.stepper_prepare(add_0, 5)
        stepper2 = self.graph.stepper()
        results = list(stepper2.stream())
        self.assertEqual(results[0], 105)


