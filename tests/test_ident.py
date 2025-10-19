"""Tests for the ident module."""

import unittest
from hyperway.ident import IDFunc


class TestIDFunc(unittest.TestCase):
    """Test IDFunc class."""
    
    def test_set_id(self):
        """set_id() stores a custom ID."""
        obj = IDFunc()
        obj.set_id(12345)
        self.assertEqual(obj._id, 12345)
    
    def test_set_id_with_string(self):
        """set_id() can store any value type."""
        obj = IDFunc()
        obj.set_id("custom-id")
        self.assertEqual(obj._id, "custom-id")
    
    def test_id_returns_custom_id(self):
        """id() returns custom ID when set."""
        obj = IDFunc()
        obj.set_id(999)
        self.assertEqual(obj.id(), 999)
    
    def test_id_returns_builtin_id_when_not_set(self):
        """id() returns built-in id() when no custom ID is set."""
        obj = IDFunc()
        self.assertEqual(obj.id(), id(obj))


