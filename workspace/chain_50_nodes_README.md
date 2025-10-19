# Chain of 50 Nodes Example

## Overview
This example demonstrates the hyperway library's ability to handle long execution chains by creating a graph with 50 sequential mathematical operations.

## File Location
`/workspaces/python-hyperway/workspace/chain_50_nodes.py`

## What It Does
1. **Creates 50 operations** using the Factory pattern from `hyperway.tools`
   - Operations include: add, subtract, multiply, divide, modulo
   - Each operation is dynamically generated using factory notation (e.g., `f.add_1`, `f.mul_2`)

2. **Chains them together** using `Graph.connect()`
   - Creates 49 connections (edges) between 50 nodes
   - Forms a linear execution path from first to last node

3. **Executes the chain** using the Stepper engine
   - Starts with initial value: 10
   - Processes through all 50 operations sequentially
   - Final computed value: **2535.6**

4. **Optional visualization** with `--render` flag
   - Generates a graphviz diagram showing all nodes and connections
   - Saved to `renders/chain_50_nodes.gv.png`

## Usage

### Basic execution:
```bash
python workspace/chain_50_nodes.py
```

### With graph visualization:
```bash
python workspace/chain_50_nodes.py --render
```

## Key Concepts Demonstrated

### Factory Pattern
The `Factory` class from `hyperway.tools` allows dynamic creation of operation nodes:
```python
f = t.Factory(commute=True)
operations = [
    f.add_1,      # Adds 1
    f.mul_2,      # Multiplies by 2
    f.sub_3,      # Subtracts 3
    # ... etc
]
```

### Graph Connection
The `connect()` method chains multiple units sequentially:
```python
units = [as_unit(op) for op in operations]
chain = g.connect(*units)  # Returns 49 connections
```

### Stepper Execution
The stepper walks the graph and executes each node:
```python
g.stepper_prepare(first_unit, initial_value)
stepper = g.stepper()
while stepper.step():
    pass  # Continue until no more rows
```

### Result Stashing
Final values are stored in `stepper.stash`:
```python
# Stash is a dict: {function: (ArgsPack, ...)}
for func, akw_tuple in stepper.stash.items():
    for akw in akw_tuple:
        value = akw.args[0]  # Extract computed value
```

## Output Example
```
============================================================
Chain of 50 Nodes Example
============================================================
Created chain with 49 connections
Starting with: Unit(func=P_add_1.0)
Ending with: Unit(func=P_truediv_5.0)

Starting computation with initial value: 10

Executing chain...
 C(0) "Unit(func=P_truediv_5.0)"

Completed in 50 steps

Final results in stash (1 items):
  Function: PartialConnection to Unit(func=P_truediv_5.0)
    ArgsPack 0: ArgsPack(*(2535.6,), **{})
      Final computed value: 2535.6
```

## Performance
- 50 nodes
- 49 connections
- 50 execution steps
- Linear O(n) complexity
- Demonstrates scalability of the hyperway engine

## Related Files
- Source: `workspace/chain_50_nodes.py`
- Visualization: `renders/chain_50_nodes.gv.png` (when rendered)
- Factory implementation: `src/hyperway/tools.py`
