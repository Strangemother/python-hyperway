"""
Edge Selection Example - Version 2

This is a clean, simple demonstration of custom edge selection using a Unit
subclass with a `get_connections()` method.

See also: [Version 1](edge-selection-v1.py) - Works but is overly complicated.

This Version 2 was also written with AI assistance - but after being told off and told
to do it correctly :D

The key insight: Just override `get_connections()` in your Unit subclass to
filter which connections to follow. The existing infrastructure in edges.py
already checks for and uses this method - no framework changes needed!

In this example:
- Lana (ChoiceNode) connects to Bob, Alice, Dave1, and Dave2
- ChoiceNode.get_connections() filters to only "Dave" named connections
- Result: Only Dave1 and Dave2 are called, Bob and Alice are skipped
"""

from hyperway.graph import Graph
from hyperway.nodes import Unit, as_unit
from hyperway.packer import argspack


class ChoiceNode(Unit):
    """A custom node that implements get_connections() for edge selection."""
    
    def get_connections(self, graph, akw=None):
        """Filter and return connections based on custom logic."""
        # Get all connections from graph
        connections = graph.get(self.id(), None)
        
        if not connections:
            return None
        
        name = "bob"
        if akw is not None:
            print('Using akw for target_name:', akw)
            name = akw.args[0].get('target_name', 'alice')
            print('Extracted target_name from akw:', name)
        else:
            print('No akw provided, using default target_name:', name)

        print(f'--- ChoiceNode.get_connections(). Filtering for {name} ---')
        # Filter for connections named "Dave"
        filtered = tuple(c for c in connections if c.name == name)
        names = [c.name for c in filtered]  
        print(f'--- ChoiceNode.get_connections() filtered connections: {names} ---')
        return filtered if filtered else None


def print_node(name):
    """Factory function to create a print function with a fixed name."""
    def printer(*args, **kwargs):
        d = args[0]
        if d is None:
            print(f"  {name} called with no data")
        else: 
            d[name] = True
        print(f"  {name} called with: args={args}, kwargs={kwargs}")
        return d 
    
    printer.__name__ = name
    return printer


def main():
    """Build and execute the example graph."""
    
    # Create the graph
    g = Graph()
    
    # Create the nodes - Lana uses ChoiceNode for custom connection selection
    lana = ChoiceNode(print_node("Lana"))
    bob_node = as_unit(print_node("Bob"))
    alice_node = as_unit(print_node("Alice"))
    dave1_node = as_unit(print_node("Dave1"))
    dave2_node = as_unit(print_node("Dave2"))
    
    
    # Connect Lana to multiple nodes with named connections
    g.add(lana, bob_node, name="bob")
    g.add(lana, alice_node, name="alice")
    g.add(lana, dave1_node, name="Dave")
    g.add(lana, dave2_node, name="Dave")
    # g.add(dave1_node, as_unit(print_node("Out")), name="out")
    # g.add(dave2_node, as_unit(print_node("Out")), name="out")
    
    print("=" * 70)
    print("Graph Structure:")
    print("=" * 70)
    print(f"Lana connects to:")
    print(f"  - Bob (name='bob')")
    print(f"  - Alice (name='alice')")
    print(f"  - Dave1 (name='Dave')")
    print(f"  - Dave2 (name='Dave')")
    print()
    
    # Step the graph from lana until complete
    from hyperway import INITIATE_UNIFIED
    
    print("=" * 70)
    print("Executing Graph with initiate=INITIATE_UNIFIED:")
    print("=" * 70)
    
    g.stepper_prepare(lana, {'foo': 'bar', 'target_name': 'Dave'}, initiate=INITIATE_UNIFIED)
    stepper = g.stepper()
    # return stepper

    while True:
        rows = stepper.step()
        if not rows:
            break
    
    print("\nExecution complete!")
    print(f"Stashed results: {len(stepper.stash)}: {stepper.stash}")
    return stepper

if __name__ == "__main__":
    st= main()
