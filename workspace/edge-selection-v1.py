"""
Edge Selection Example - Custom get_connections()

This example demonstrates how a Unit can implement custom connection selection
by overriding get_connections(). 

Node "Lana" connects to four nodes through named connections:
- Connection to Bob (name='bob')
- Connection to Alice (name='alice')
- Connection to Dave1 (name='Dave')
- Connection to Dave2 (name='Dave')

The SelectiveUnit reads the 'to' field from the data dict during process(),
then uses that value in get_connections() to filter which connections to follow.

When data {"foo": "Bar", "to": "Dave"} flows through:
1. Lana's process() extracts to="Dave" 
2. Lana's get_connections() returns only connections named "Dave"
3. Both Dave1 and Dave2 are called with the same dict
4. Bob and Alice are skipped entirely

Result: Dynamic routing based on data flowing through the graph!
"""

from hyperway.graph import Graph
from hyperway.nodes import Unit, as_unit
from hyperway.packer import argspack
from hyperway.stepper import StepperC


def print_node(name):
    """Factory function to create a print function with a fixed name."""
    def printer(*args, **kwargs):
        if args and isinstance(args[0], dict):
            print(f"  {name} received dict: {args[0]}")
        else:
            print(f"  {name} called with: args={args}, kwargs={kwargs}")
    printer.__name__ = name
    return printer


class SelectiveUnit(Unit):
    """A Unit that selects connections based on runtime data.
    
    Stores routing dict and overrides get_connections() to filter by name.
    The dict must be set before stepper execution via set_routing_data().
    """
    
    def __init__(self, func, **node_kwargs):
        super().__init__(func, **node_kwargs)
        self._routing_data = {}
    
    def set_routing_data(self, data):
        """Set the routing data dict before execution."""
        self._routing_data = data
        print(f"\n{self.get_name()} configured with routing data: {data}")
    
    def process(self, *a, **kw):
        """Process and pass through the data."""
        print(f"  {self.get_name()} processing data: {self._routing_data}")
        
        # Call the underlying function with the routing data
        super().process(self._routing_data)
        
        # Return the data to pass it along
        return self._routing_data
    
    def get_connections(self, graph):
        """Filter connections by name based on routing data.
        
        This method is called by get_connections() in edges.py.
        It uses the _routing_data dict to determine which connections to follow.
        """
        # Get all connections from graph
        connections = graph.get(self.id(), None)
        
        if not connections:
            return None
        
        target_name = self._routing_data.get('to', None)
        
        print(f"\n{self.get_name()} selecting from {len(connections)} connections:")
        print(f"  Looking for connections named: '{target_name}'")
        
        if target_name is None:
            print("  No 'to' field in routing data, returning all connections")
            return connections
        
        # Filter connections by name
        filtered = tuple(c for c in connections if c.name == target_name)
        
        print(f"  Found {len(filtered)} matching connection(s):")
        for conn in filtered:
            print(f"    - Connection to {conn.b.get_name()} (name='{conn.name}')")
        
        return filtered if filtered else None


def main():
    """Build and execute the example graph."""
    
    # Create the graph
    g = Graph()
    
    # Create nodes - Lana uses SelectiveUnit for custom connection selection
    lana = SelectiveUnit(print_node("Lana"))
    bob_node = as_unit(print_node("Bob"))
    alice_node = as_unit(print_node("Alice"))
    dave1_node = as_unit(print_node("Dave1"))
    dave2_node = as_unit(print_node("Dave2"))
    
    # Configure routing data BEFORE adding connections
    start_data = {"foo": "Bar", "to": "Dave"}
    lana.set_routing_data(start_data)
    
    # Connect Lana to multiple nodes with named connections
    g.add(lana, bob_node, name="bob")
    g.add(lana, alice_node, name="alice")
    g.add(lana, dave1_node, name="Dave")
    g.add(lana, dave2_node, name="Dave")
    
    print("=" * 70)
    print("Graph Structure:")
    print("=" * 70)
    print(f"Lana connects to:")
    print(f"  - Bob (name='bob')")
    print(f"  - Alice (name='alice')")
    print(f"  - Dave1 (name='Dave')")
    print(f"  - Dave2 (name='Dave')")
    print()
    
    # Prepare and run the stepper
    print("=" * 70)
    print("Starting Stepper")
    print("=" * 70)
    
    # Prepare stepper (data already set on lana node)
    g.stepper_prepare(lana)
    stepper = g.stepper()
    
    print(f"\nStarting at Lana")
    print()
    
    # Execute the graph
    step_count = 0
    while True:
        step_count += 1
        print(f"\n--- Step {step_count} ---")
        rows = stepper.step()
        
        if not rows:
            print("No more rows to process")
            break
            
        print(f"Active rows: {len(rows)}")
        for caller, akw in rows:
            caller_name = caller.get_name() if hasattr(caller, 'get_name') else str(caller)
            print(f"  Next: {caller_name} with {akw}")
    
    print("\n" + "=" * 70)
    print("Execution Complete")
    print("=" * 70)
    print(f"\nTotal steps: {step_count - 1}")
    print(f"Stashed results: {len(stepper.stash)}")
    
    if stepper.stash:
        print("\nFinal results in stash:")
        for i, item in enumerate(stepper.stash, 1):
            if hasattr(item, 'get_name'):
                node_name = item.get_name()
            else:
                node_name = str(item)
            print(f"  {i}. {node_name}")


if __name__ == "__main__":
    main()
