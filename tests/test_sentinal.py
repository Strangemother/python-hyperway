"""Test sentinal values in Hyperway.

Sentinal values allow functions to explicitly return "no value" instead of None,
preventing unintended argument passing when chaining functions together.

See docs/sentinal.md for more information.
"""
import unittest

from hyperway.edges import make_edge
from hyperway.nodes import as_unit


# Define a custom sentinal value (a singleton object)
UNDEFINED = object()


def func_no_args():
    """A function that expects no arguments and returns a value."""
    return "egg"


def func_returns_none():
    """A function that returns None (Python's default 'no value')."""
    return None


def func_returns_sentinal():
    """A function that returns a sentinal value to explicitly indicate 'no value'."""
    return UNDEFINED


class TestSentinal(unittest.TestCase):
    """Validate that sentinal values prevent unintended argument passing.
    
    Without a sentinal, Python's None is passed as an argument to downstream nodes,
    causing TypeError when the downstream function expects no arguments.
    
    With a sentinal, Hyperway recognizes the explicit 'no value' and doesn't pass
    it to downstream nodes.
    """

    def test_without_sentinal_none_causes_type_error(self):
        """Without sentinal: func_returns_none() returns None, which is passed to 
        func_no_args(), causing TypeError since func_no_args() takes 0 arguments."""
        
        connection = make_edge(func_returns_none, as_unit(func_no_args))
        
        with self.assertRaises(TypeError) as context:
            connection.pluck()
        
        self.assertIn("takes 0 positional arguments but 1 was given", str(context.exception))

    def test_with_sentinal_none_works_correctly(self):
        """With sentinal=None: When func_returns_none() returns None, 
        Hyperway treats it as 'no value' and calls func_no_args() without arguments."""
        
        connection = make_edge(
            func_returns_none, 
            as_unit(func_no_args, sentinal=None)
        )
        
        result = connection.pluck()
        self.assertEqual(result, "egg")

    def test_with_custom_sentinal_works_correctly(self):
        """With custom sentinal: When func_returns_sentinal() returns UNDEFINED,
        Hyperway treats it as 'no value' and calls func_no_args() without arguments."""
        
        connection = make_edge(
            func_returns_sentinal,
            as_unit(func_no_args, sentinal=UNDEFINED)
        )
        
        result = connection.pluck()
        self.assertEqual(result, "egg")

    def test_sentinal_prevents_argument_passing(self):
        """Demonstrate that sentinal values prevent the sentinal itself from being 
        passed as an argument to downstream nodes."""
        
        def returns_undefined():
            return UNDEFINED
        
        def expects_no_args():
            return "success"
        
        # With sentinal configured, UNDEFINED is not passed downstream
        connection = make_edge(
            returns_undefined,
            as_unit(expects_no_args, sentinal=UNDEFINED)
        )
        
        result = connection.pluck()
        self.assertEqual(result, "success")

