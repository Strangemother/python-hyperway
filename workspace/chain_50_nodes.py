"""
Generate a chain of 50 nodes using the factory.

This example creates a long linear chain of mathematical operations
using the hyperway factory to dynamically generate operations.
The chain demonstrates the scalability of the graph execution engine.

Usage:
    python chain_50_nodes.py [--render]
    
    --render: Generate a graphviz visualization (requires graphviz installed)
"""

import sys
from hyperway.graph import Graph
from hyperway.nodes import as_unit
from hyperway.stepper import StepperC
import hyperway.tools as t

# Use the commutative factory for logical operation order
f = t.Factory(commute=True)


def main():
    """Create and execute a chain of 50 nodes."""
    
    # Create a new graph
    g = Graph(tuple)
    
    # Define 50 operations using the factory
    # Mix different operations: add, sub, mul, truediv, mod
    operations = [
        f.add_1,      # 0
        f.mul_2,      # 1
        f.sub_3,      # 2
        f.add_5,      # 3
        f.truediv_2,  # 4
        f.mul_3,      # 5
        f.add_10,     # 6
        f.sub_5,      # 7
        f.mul_2,      # 8
        f.add_7,      # 9
        f.truediv_3,  # 10
        f.add_2,      # 11
        f.mul_5,      # 12
        f.sub_10,     # 13
        f.add_8,      # 14
        f.truediv_2,  # 15
        f.mul_4,      # 16
        f.add_3,      # 17
        f.sub_7,      # 18
        f.mul_2,      # 19
        f.add_15,     # 20
        f.sub_8,      # 21
        f.truediv_2,  # 22
        f.add_6,      # 23
        f.mul_3,      # 24
        f.sub_12,     # 25
        f.add_9,      # 26
        f.truediv_3,  # 27
        f.mul_2,      # 28
        f.add_4,      # 29
        f.sub_6,      # 30
        f.mul_5,      # 31
        f.add_11,     # 32
        f.truediv_2,  # 33
        f.sub_9,      # 34
        f.mul_3,      # 35
        f.add_7,      # 36
        f.sub_4,      # 37
        f.truediv_2,  # 38
        f.add_13,     # 39
        f.mul_2,      # 40
        f.sub_11,     # 41
        f.add_5,      # 42
        f.truediv_3,  # 43
        f.mul_4,      # 44
        f.add_2,      # 45
        f.sub_8,      # 46
        f.mul_2,      # 47
        f.add_10,     # 48
        f.truediv_5,  # 49
    ]
    
    # Wrap operations as units
    units = [as_unit(op) for op in operations]
    
    # Connect all units in a chain
    chain = g.connect(*units)
    
    print(f"Created chain with {len(chain)} connections")
    print(f"Starting with: {chain[0].a}")
    print(f"Ending with: {chain[-1].b}")
    
    # Prepare stepper with initial value
    initial_value = 10
    print(f"\nStarting computation with initial value: {initial_value}")
    
    first_unit = chain[0].a
    g.stepper_prepare(first_unit, initial_value)
    
    # Create stepper and execute
    stepper = g.stepper()
    step_count = 0
    
    print("\nExecuting chain...")
    while True:
        rows = stepper.step()
        step_count += 1
        if not rows:
            break
    
    print(f"\nCompleted in {step_count} steps")
    
    # Display results
    if stepper.stash:
        print(f"\nFinal results in stash ({len(stepper.stash)} items):")
        for func, akw_tuple in stepper.stash.items():
            print(f"  Function: {func}")
            for i, akw in enumerate(akw_tuple):
                print(f"    ArgsPack {i}: {akw}")
                # Extract the actual value from ArgsPack
                if hasattr(akw, 'args') and akw.args:
                    final_value = akw.args[0]
                    print(f"      Final computed value: {final_value}")
    else:
        print("\nNo results in stash")
    
    # Optional: Render graph visualization
    if '--render' in sys.argv:
        print("\nRendering graph visualization...")
        try:
            g.write("chain_50_nodes", directory="renders", direction="LR")
            print("  Graph saved to: renders/chain_50_nodes.gv.png")
        except Exception as e:
            print(f"  Could not render graph: {e}")
    
    return stepper, g


if __name__ == '__main__':
    print("=" * 60)
    print("Chain of 50 Nodes Example")
    print("=" * 60)
    stepper, graph = main()
    print("=" * 60)
    print("Done!")
    print("\nTip: Run with --render to generate a graph visualization")

