"""
Generate a loop (ring) of 6 nodes using the factory.

This example creates a circular graph where nodes connect back to the start,
forming an infinite loop. We limit execution to 14 steps to demonstrate
controlled iteration through the cycle.

The ring topology: A → B → C → D → E → F → A (repeats forever)

Usage:
    python loop_6_nodes.py [--render]
    
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
    """Create and execute a loop of 6 nodes for 14 steps."""
    
    # Create a new graph
    g = Graph(tuple)
    
    # Define 6 operations that form the loop
    operations = [
        f.add_1,      # Node 0: add 1
        f.mul_2,      # Node 1: multiply by 2
        f.sub_3,      # Node 2: subtract 3
        f.add_5,      # Node 3: add 5
        f.truediv_2,  # Node 4: divide by 2
        f.mul_3,      # Node 5: multiply by 3
    ]
    
    # Wrap operations as units
    units = [as_unit(op) for op in operations]
    
    print(f"Creating loop with {len(units)} nodes:")
    for i, unit in enumerate(units):
        print(f"  Node {i}: {unit}")
    
    # Create a ring: connect each node to the next, and last back to first
    # This creates: 0→1→2→3→4→5→0 (infinite loop)
    for i in range(len(units)):
        next_i = (i + 1) % len(units)  # Wrap around to 0 after last node
        g.add(units[i], units[next_i])
        print(f"  Connected: Node {i} → Node {next_i}")
    
    print(f"\nLoop topology: ", end="")
    for i in range(len(units)):
        print(f"{i}", end=" → " if i < len(units) - 1 else " → 0 (loop)\n")
    
    # Prepare stepper with initial value
    initial_value = 10
    print(f"\nStarting computation with initial value: {initial_value}")
    
    # Start from the first node
    start_unit = units[0]
    g.stepper_prepare(start_unit, initial_value)
    
    # Create stepper and execute for exactly 14 steps
    stepper = g.stepper()
    max_steps = 14
    
    print(f"\nExecuting loop for {max_steps} steps...")
    print("-" * 60)
    
    values = []  # Track values at each step
    
    for step_num in range(max_steps):
        rows = stepper.step()
        
        if not rows:
            print(f"Step {step_num + 1}: Loop completed naturally (no more rows)")
            break
        
        # Extract and display the value being processed
        for caller, akw in rows:
            if hasattr(akw, 'args') and akw.args:
                current_value = akw.args[0]
                values.append(current_value)
                node_info = f"{caller}" if caller else "unknown"
                print(f"Step {step_num + 1:2d}: Value = {current_value:10.2f} | Next: {node_info}")
    
    print("-" * 60)
    print(f"\nCompleted {len(values)} steps")
    
    # Display value progression
    if values:
        print(f"\nValue progression:")
        print(f"  Start: {initial_value}")
        for i, val in enumerate(values[:5], 1):  # Show first 5
            print(f"  Step {i}: {val:.2f}")
        if len(values) > 10:
            print(f"  ...")
            for i, val in enumerate(values[-5:], len(values) - 4):  # Show last 5
                print(f"  Step {i}: {val:.2f}")
        elif len(values) > 5:
            for i, val in enumerate(values[5:], 6):
                print(f"  Step {i}: {val:.2f}")
    
    # Calculate cycle analysis
    print(f"\nCycle analysis:")
    print(f"  Nodes in loop: {len(units)}")
    print(f"  Steps executed: {len(values)}")
    print(f"  Full cycles: {len(values) // len(units)}")
    print(f"  Partial cycle: {len(values) % len(units)} nodes")
    
    # Display stepper stash (should be empty since loop doesn't end)
    if stepper.stash:
        print(f"\nResults in stash ({len(stepper.stash)} items):")
        for func, akw_tuple in stepper.stash.items():
            print(f"  Function: {func}")
            for i, akw in enumerate(akw_tuple):
                print(f"    ArgsPack {i}: {akw}")
                if hasattr(akw, 'args') and akw.args:
                    final_value = akw.args[0]
                    print(f"      Final value: {final_value}")
    else:
        print("\nNo results in stash (loop has no natural end)")
    
    # Optional: Render graph visualization
    if '--render' in sys.argv:
        print("\nRendering graph visualization...")
        try:
            g.write("loop_6_nodes", directory="renders", direction="LR")
            print("  Graph saved to: renders/loop_6_nodes.gv.png")
        except Exception as e:
            print(f"  Could not render graph: {e}")
    
    return stepper, g, values


if __name__ == '__main__':
    print("=" * 60)
    print("Loop of 6 Nodes Example (14 steps)")
    print("=" * 60)
    stepper, graph, values = main()
    print("=" * 60)
    print("Done!")
    print("\nTip: Run with --render to generate a graph visualization")
