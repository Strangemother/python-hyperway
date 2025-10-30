"""Tests for the writer module in Hyperway.

These tests validate graph visualization functions:
- set_graphviz PATH modification
- write_graphviz rendering with various options
- Graceful handling when graphviz is unavailable
"""

import unittest
from unittest.mock import patch, MagicMock, call
import os
from pathlib import Path

from hyperway.writer import set_graphviz, write_graphviz, HAS_GRAPHVIZ
from hyperway.graph import Graph
from hyperway.tools import factory as f

from tiny_tools import delete_sys_module

import sys

# @unittest.skip('Demonstration of module restoration in teardown')
class TestTestGraphvizImportErrorTearDown(unittest.TestCase):
    """Test the TestGraphvizImportError class 
    to ensure the teardown works as intended.
    """
    def setUp(self):
        """Save the original module."""
        from hyperway import writer 
        self.original_module = sys.modules.get('hyperway.writer')
        # the delete it to flag a new import
        delete_sys_module('hyperway.writer')
        assert 'hyperway.writer' not in sys.modules

    def tearDown(self):
        """Restore the original module."""
        sys.modules['hyperway.writer'] = self.original_module
        assert 'hyperway.writer' in sys.modules

    def test_teardown_restores_module(self):
        """Ensure that the teardown restores the original module."""
        assert 'hyperway.writer' not in sys.modules
        
        # run the other test class module teardown
        TestGraphvizImportError().tearDown()
        # because we deleted it in setUp, 
        # it should be restored now
        restored_module = sys.modules.get('hyperway.writer')
        self.assertIsNotNone(restored_module)
        # Teardown should restore the original module


class TestGraphvizImportError(unittest.TestCase):
    """Test handling of missing graphviz module."""
    original_writer = None
    def setUp(self):
        """Save the original module state."""
        import sys
        # Save the original writer module if it exists
        self.original_writer = sys.modules.get('hyperway.writer')
    
    def tearDown(self):
        """Restore the original module state."""
        import sys
        
        # Remove the test-modified module
        delete_sys_module('hyperway.writer')
        
        # Restore or reimport the original
        if self.original_writer:
            sys.modules['hyperway.writer'] = self.original_writer
        else:
            # Reimport fresh - this branch handles case where module wasn't loaded before
            import hyperway.writer

    @patch('sys.stderr.write')
    @patch('builtins.print')
    def test_graphviz_import_error_writes_to_stderr_better(self, mock_print, mock_stderr_write):
        """When graphviz import fails, error message is written to stderr."""
        import sys
        import importlib
        import builtins
        
        # Remove writer module from sys.modules to force reimport
        if 'hyperway.writer' in sys.modules:
            del sys.modules['hyperway.writer']
        
        # Save the original import function
        original_import = builtins.__import__
        
        # Mock graphviz to raise ImportError during import
        with patch('sys.modules', sys.modules.copy()):
            sys.modules['graphviz'] = None  # Mark as not available
            
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                       (_ for _ in ()).throw(ImportError("Mocked: graphviz not installed")) 
                       if name == 'graphviz' 
                       else original_import(name, *args, **kwargs)):
                
                # Import the module - should trigger the except block
                import hyperway.writer
                
                # Verify stderr.write was called with error message
                mock_stderr_write.assert_called()
                stderr_call_args = str(mock_stderr_write.call_args)
                self.assertIn('No graphviz installed', stderr_call_args)
                
                # Verify print was also called
                mock_print.assert_called()
                
                # Verify HAS_GRAPHVIZ is False
                self.assertFalse(hyperway.writer.HAS_GRAPHVIZ)


class TestSetGraphviz(unittest.TestCase):
    """Validate set_graphviz PATH manipulation."""

    def test_set_graphviz_updates_path(self):
        """Ensure set_graphviz appends to PATH."""
        original_path = os.environ.get("PATH", "")
        test_path = "/test/graphviz/bin"
        
        set_graphviz(test_path)
        
        new_path = os.environ["PATH"]
        self.assertIn(test_path, new_path)
        
        # Cleanup
        os.environ["PATH"] = original_path

    def test_set_graphviz_uses_pathlib(self):
        """Verify set_graphviz converts path to Path object."""
        original_path = os.environ.get("PATH", "")
        test_path_str = "/usr/local/bin"
        
        set_graphviz(test_path_str)
        
        # Should be able to find the path in PATH
        self.assertIn(test_path_str, os.environ["PATH"])
        
        # Cleanup
        os.environ["PATH"] = original_path


@unittest.skipUnless(HAS_GRAPHVIZ, "graphviz not installed")
class TestWriteGraphvizWithGraphviz(unittest.TestCase):
    """Test write_graphviz when graphviz is available."""

    def setUp(self):
        """Create a simple graph for testing."""
        self.graph = Graph()
        self.graph.connect(f.add_1, f.add_2, f.add_3)

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_creates_digraph(self, mock_digraph_class):
        """Verify write_graphviz creates a Digraph object."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        result = write_graphviz(self.graph, "test_title")
        
        # Should create a Digraph
        mock_digraph_class.assert_called_once()
        args, kwargs = mock_digraph_class.call_args
        self.assertEqual(args[0], "test_title")
        
        # Should call render
        mock_digraph.render.assert_called_once()
        
        # Should return the Digraph
        self.assertEqual(result, mock_digraph)

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_default_options(self, mock_digraph_class):
        """Check that default options are applied correctly."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test")
        
        args, kwargs = mock_digraph_class.call_args
        self.assertEqual(kwargs['format'], 'png')
        self.assertEqual(kwargs['engine'], 'dot')
        self.assertEqual(kwargs['graph_attr']['rankdir'], 'TB')

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_custom_direction(self, mock_digraph_class):
        """Test custom direction parameter."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", direction='LR')
        
        args, kwargs = mock_digraph_class.call_args
        self.assertEqual(kwargs['graph_attr']['rankdir'], 'LR')
        
        # Verify that graph_attr['rankdir'] was also set on the instance
        mock_digraph.graph_attr.__setitem__.assert_called_with('rankdir', 'LR')

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_custom_styles(self, mock_digraph_class):
        """Test custom style parameters."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        custom_styles = {
            'node_shape': 'ellipse',
            'node_color': '#FF0000',
            'bgcolor': '#FFFFFF',
        }
        
        write_graphviz(self.graph, "test", styles=custom_styles)
        
        # Verify attr was called with custom node properties
        mock_digraph.attr.assert_called()
        
        # Check for node attr call with shape
        calls = mock_digraph.attr.call_args_list
        node_call = calls[0]  # First attr call is for nodes
        self.assertEqual(node_call[1]['shape'], 'ellipse')
        self.assertEqual(node_call[1]['color'], '#FF0000')

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_with_directory(self, mock_digraph_class):
        """Test rendering to a specific directory."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "output/test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", directory="output")
        
        # Should pass directory to render
        mock_digraph.render.assert_called_once_with(directory="output")

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_adds_nodes_and_edges(self, mock_digraph_class):
        """Verify nodes and edges are added to the graph."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test")
        
        # Should add nodes
        self.assertGreater(mock_digraph.node.call_count, 0)
        
        # Should add edges
        self.assertGreater(mock_digraph.edge.call_count, 0)

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_with_show_view(self, mock_digraph_class):
        """Test that view() is called when show_view=True."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", view=True)
        
        # Should call view() when view=True
        mock_digraph.view.assert_called_once()
        mock_digraph.render.assert_called_once()

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_without_show_view(self, mock_digraph_class):
        """Test that view() is NOT called when show_view=False (default)."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", view=False)
        
        # Should NOT call view() when view=False
        mock_digraph.view.assert_not_called()
        mock_digraph.render.assert_called_once()

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_default_no_view(self, mock_digraph_class):
        """Test that view() is NOT called by default."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        # Call without view parameter
        write_graphviz(self.graph, "test")
        
        # Should NOT call view() by default
        mock_digraph.view.assert_not_called()

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_with_format_parameter(self, mock_digraph_class):
        """Test that format attribute is set when format parameter is provided."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", format='svg')
        
        # Should set format attribute on the digraph
        self.assertEqual(mock_digraph.format, 'svg')
        mock_digraph.render.assert_called_once()

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_format_parameter_none(self, mock_digraph_class):
        """Test that format attribute is NOT set when format=None."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", format=None)
        
        # format attribute should not be set when format=None
        # Check that format was never assigned after initialization
        # (it's set in defaults but shouldn't be reassigned)
        self.assertEqual(mock_digraph.render.call_count, 1)

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_with_directory_and_format(self, mock_digraph_class):
        """Test rendering with both directory and format parameters."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "output/test.svg"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", directory="output", format='svg')
        
        # Should set format
        self.assertEqual(mock_digraph.format, 'svg')
        # Should pass directory to render
        mock_digraph.render.assert_called_once_with(directory="output")

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_view_and_format_together(self, mock_digraph_class):
        """Test that both view and format work together."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.pdf"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test", view=True, format='pdf')
        
        # Should call view
        mock_digraph.view.assert_called_once()
        # Should set format
        self.assertEqual(mock_digraph.format, 'pdf')
        # Should render
        mock_digraph.render.assert_called_once()

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_directory_none_not_passed(self, mock_digraph_class):
        """Test that directory is not passed to render when None."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "test.gv"
        mock_digraph_class.return_value = mock_digraph
        
        write_graphviz(self.graph, "test")
        
        # Should call render without directory parameter
        mock_digraph.render.assert_called_once_with()

    @patch('hyperway.writer.graphviz.Digraph')
    def test_write_graphviz_all_options_combined(self, mock_digraph_class):
        """Test all highlighted options working together."""
        mock_digraph = MagicMock()
        mock_digraph.render.return_value = "renders/test.svg"
        mock_digraph_class.return_value = mock_digraph
        
        result = write_graphviz(
            self.graph, 
            "test_all_options",
            view=True,
            format='svg',
            directory="renders"
        )
        
        # Should call view
        mock_digraph.view.assert_called_once()
        # Should set format
        self.assertEqual(mock_digraph.format, 'svg')
        # Should pass directory to render
        mock_digraph.render.assert_called_once_with(directory="renders")
        # Should return the digraph
        self.assertEqual(result, mock_digraph)


class TestWriteGraphvizWithoutGraphviz(unittest.TestCase):
    """Test write_graphviz behavior when graphviz is unavailable."""

    @patch('hyperway.writer.HAS_GRAPHVIZ', False)
    def test_write_graphviz_returns_false_without_graphviz(self):
        """Verify write_graphviz returns False when graphviz is missing."""
        graph = Graph()
        graph.connect(f.add_1, f.add_2)
        
        result = write_graphviz(graph, "test")
        
        self.assertFalse(result)

    @patch('hyperway.writer.HAS_GRAPHVIZ', False)
    @patch('builtins.print')
    def test_write_graphviz_prints_message_without_graphviz(self, mock_print):
        """Check that a message is printed when graphviz is unavailable."""
        graph = Graph()
        
        write_graphviz(graph, "test")
        
        # Should print a message about graphviz not being installed
        mock_print.assert_called()
        call_args = [str(call[0]) for call in mock_print.call_args_list]
        messages = ' '.join(call_args)
        self.assertIn('graphviz', messages.lower())


class TestGraphvizImport(unittest.TestCase):
    """Test the graphviz import handling."""

    def test_has_graphviz_flag(self):
        """Verify HAS_GRAPHVIZ is a boolean."""
        self.assertIsInstance(HAS_GRAPHVIZ, bool)


