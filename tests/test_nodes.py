"""Tests for the Node (Unit) class in Hyperway.

These tests validate core node behaviors:
- Wrapping callables with as_unit/as_units
- Name resolution and string representations
- Sentinal handling in Unit.process
- Nodes.process bypassing sentinal logic
- Leaf behavior integrating with a stepper's end_branch
"""

import unittest
from unittest.mock import patch

from hyperway.nodes import (
    as_unit,
    as_units,
    is_unit,
    Unit,
    Nodes,
    get_edge_func,
    CACHE,
)
from hyperway.packer import argspack

class CallableNoName:
    def __call__(self, *a, **kw):
        return "x"

assert CallableNoName()() == "x"

class TestGetEdgeFunc(unittest.TestCase):
    """Test get_edge_func() caching behavior."""
    
    def test_returns_cached_make_edge(self):
        """get_edge_func() returns cached make_edge when available."""
        mock_func = lambda: "cached"
        
        with patch.dict(CACHE, {'make_edge': mock_func}):
            result = get_edge_func()
            self.assertEqual(result, mock_func)
    
    def test_imports_and_caches_when_not_cached(self):
        """get_edge_func() imports make_edge and caches it when not present."""
        with patch.dict(CACHE, {}, clear=True):
            result = get_edge_func()
            
            # Should have imported and cached make_edge
            self.assertIn('make_edge', CACHE)
            self.assertEqual(CACHE['make_edge'], result)
            
            # Should be the actual make_edge function from edges module
            from hyperway.edges import make_edge
            self.assertEqual(result, make_edge)



def no_arg_func():
    """Simple function that takes no arguments and returns a value."""
    return "ok"


def echo(*a, **kw):
    """Echo all inputs for easy assertions."""
    return (a, kw)


class TestAsUnitHelpers(unittest.TestCase):
    """Validate as_unit/as_units and is_unit helpers."""

    def test_as_unit_wraps_callable(self):
        u = as_unit(no_arg_func)
        self.assertIsInstance(u, Unit)
        self.assertIs(u.func, no_arg_func)

    def test_as_unit_idempotent(self):
        u1 = as_unit(no_arg_func)
        u2 = as_unit(u1)
        self.assertIs(u2, u1)

    def test_as_unit_custom_node_class(self):
        n = as_unit(echo, node_class=Nodes)
        self.assertIsInstance(n, Nodes)
        self.assertIs(n.func, echo)

    def test_as_units_multiple(self):
        units = as_units(no_arg_func, echo)
        # Validate all returned are Units and their underlying funcs are present
        self.assertTrue(all(is_unit(u) for u in units))
        funcs = {getattr(u, "func", None) for u in units}
        self.assertIn(no_arg_func, funcs)
        self.assertIn(echo, funcs)

    def test_is_unit(self):
        u = as_unit(echo)
        self.assertTrue(is_unit(u))
        self.assertTrue(is_unit(u, node_class=Nodes))  # subclass also counts


class TestUnitNamingAndStr(unittest.TestCase):
    """Test naming and string/representation of Unit."""

    def test_default_name_from_func(self):
        u = as_unit(no_arg_func)
        self.assertEqual(u.get_name(), "no_arg_func")
        self.assertIn("Unit(func=no_arg_func)", str(u))
        self.assertIn("Unit(func=no_arg_func)", repr(u))

    def test_custom_name_override(self):
        u = as_unit(no_arg_func, name="Custom")
        self.assertEqual(u.get_name(), "Custom")
        self.assertIn("Unit(func=Custom)", str(u))

    def test_name_from_non_callable_repr(self):
        

        obj = CallableNoName()
        u = as_unit(obj)
        # Narrow type for static analysis and sanity-check
        self.assertIsInstance(u, Unit)
        # CallableNoName.__call__ exists but object itself has no __name__
        # get_name() is used internally by __str__, so ensure it picks a repr
        s = str(u)
        self.assertIn("Unit(func=", s)
        self.assertIn(str(obj), s)


class TestUnitSentinalBehavior(unittest.TestCase):
    """Verify Unit.process sentinal behavior matches expectations.

    - By default, Unit.sentinal is a unique object, so passing None does not
      trigger the 'no-arg' behavior.
    - When sentinal is set to None, a single None argument is treated as
      'no value' and not passed to the underlying function.
    - A custom sentinal object works similarly.
    """

    def test_default_sentinal_does_not_match_none(self):
        u = as_unit(no_arg_func)
        # Unit.process will attempt to pass None to no_arg_func which takes 0 args
        with self.assertRaises(TypeError):
            u.process(None)

    def test_none_sentinal_treats_none_as_no_args(self):
        u = as_unit(no_arg_func, sentinal=None)
        self.assertEqual(u.process(None), "ok")

    def test_custom_sentinal(self):
        CUSTOM = object()
        def zero():
            return 42
        u = as_unit(zero, sentinal=CUSTOM)
        # Passing CUSTOM should be treated as 'no-arg'
        self.assertEqual(u.process(CUSTOM), 42)
        # Passing a different object should be forwarded and error (zero takes no args)
        with self.assertRaises(TypeError):
            u.process(object())


class TestNodesProcessBehavior(unittest.TestCase):
    """Nodes.process should not apply sentinal filtering (passes args through)."""

    def test_nodes_process_keeps_arguments(self):
        n = as_unit(echo, node_class=Nodes)
        # Nodes.process forwards args regardless of sentinal usage in Unit
        a, kw = n.process(None, x=1)
        self.assertEqual(a, (None,))
        self.assertEqual(kw, {"x": 1})


class TestLeafBehavior(unittest.TestCase):
    """Validate Unit.leaf calls process and forwards result to stepper.end_branch."""

    def test_leaf_end_branch_integration(self):
        calls = {}

        class FakeStepper:
            def end_branch(self, node, res):
                # capture for assertions and return a marker
                calls["node"] = node
                calls["res"] = res
                return ("end", res)

        def doubler(v):
            return v * 2

        u = as_unit(doubler)
        akw = argspack(3)
        stepper = FakeStepper()

        result = u.leaf(stepper, akw)

        # Verify end_branch was called with the Unit and argspack of process result
        self.assertIs(calls["node"], u)
        self.assertEqual(calls["res"].args, (6,))
        self.assertEqual(calls["res"].kwargs, {})
        # And leaf returns whatever end_branch returns
        self.assertEqual(result[0], "end")


class TestUnitInput(unittest.TestCase):
    """Test Unit.input() method delegation."""
    
    def test_input_calls_process_with_args_and_kwargs(self):
        """input() calls process() with the provided args and kwargs."""
        func = lambda x, y=10: x + y
        u = Unit(func)
        
        with patch.object(u, 'process', return_value=42) as mock_process:
            result = u.input((5,), {'y': 20})
            
            # input() calls process(a, kw) - passing the tuple and dict as args
            mock_process.assert_called_once_with((5,), {'y': 20})
            self.assertEqual(result, 42)
    
    def test_input_returns_process_result(self):
        """input() returns the result from process()."""
        func = lambda a_tuple, kw_dict: a_tuple[0] * 2
        u = Unit(func)
        
        # input() receives (args_tuple, kwargs_dict) and passes them to process
        # Since process has *a signature, it will receive them as two positional args
        result = u.input((10,), {})
        
        self.assertEqual(result, 20)

