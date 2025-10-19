# Loop of 6 Nodes Example

## Overview
This example demonstrates the hyperway library's ability to handle **circular/cyclic graphs** by creating a ring of 6 nodes that form an infinite loop. Execution is deliberately limited to 14 steps to prevent infinite execution.

## File Location
`/workspaces/python-hyperway/workspace/loop_6_nodes.py`

## What It Does

### Loop Structure
Creates a circular topology where the last node connects back to the first:
```
0 → 1 → 2 → 3 → 4 → 5 → 0 (repeats forever)
```

### Operations in the Loop
1. **Node 0**: `add_1` - Adds 1
2. **Node 1**: `mul_2` - Multiplies by 2
3. **Node 2**: `sub_3` - Subtracts 3
4. **Node 3**: `add_5` - Adds 5
5. **Node 4**: `truediv_2` - Divides by 2
6. **Node 5**: `mul_3` - Multiplies by 3
7. Back to **Node 0** (loop continues)

### Execution Details
- **Initial value**: 10
- **Steps executed**: 14
- **Full cycles**: 2 complete loops through all 6 nodes
- **Partial cycle**: 2 additional nodes
- **Final value after 14 steps**: 230.0

## Usage

### Basic execution:
```bash
python workspace/loop_6_nodes.py
```

### With graph visualization:
```bash
python workspace/loop_6_nodes.py --render
```

## Key Concepts Demonstrated

### Circular Graph Creation
Using modulo arithmetic to create the loop:
```python
for i in range(len(units)):
    next_i = (i + 1) % len(units)  # Wraps back to 0
    g.add(units[i], units[next_i])
```

### Controlled Loop Execution
Limiting infinite loops with a step counter:
```python
max_steps = 14
for step_num in range(max_steps):
    rows = stepper.step()
    if not rows:
        break
```

### Value Tracking
Monitoring values as they flow through the loop:
```python
for caller, akw in rows:
    if hasattr(akw, 'args') and akw.args:
        current_value = akw.args[0]
        values.append(current_value)
```

### Empty Stash Behavior
Unlike linear chains, loops don't have natural endpoints, so `stepper.stash` remains empty.

## Output Example

```
============================================================
Loop of 6 Nodes Example (14 steps)
============================================================
Creating loop with 6 nodes:
  Node 0: Unit(func=P_add_1.0)
  Node 1: Unit(func=P_mul_2.0)
  Node 2: Unit(func=P_sub_3.0)
  Node 3: Unit(func=P_add_5.0)
  Node 4: Unit(func=P_truediv_2.0)
  Node 5: Unit(func=P_mul_3.0)

Loop topology: 0 → 1 → 2 → 3 → 4 → 5 → 0 (loop)

Starting computation with initial value: 10

Executing loop for 14 steps...
------------------------------------------------------------
Step  1: Value =      11.00 | Next: P_mul_2.0
Step  2: Value =      22.00 | Next: P_sub_3.0
Step  3: Value =      19.00 | Next: P_add_5.0
Step  4: Value =      24.00 | Next: P_truediv_2.0
Step  5: Value =      12.00 | Next: P_mul_3.0
Step  6: Value =      36.00 | Next: P_add_1.0
Step  7: Value =      37.00 | Next: P_mul_2.0
Step  8: Value =      74.00 | Next: P_sub_3.0
Step  9: Value =      71.00 | Next: P_add_5.0
Step 10: Value =      76.00 | Next: P_truediv_2.0
Step 11: Value =      38.00 | Next: P_mul_3.0
Step 12: Value =     114.00 | Next: P_add_1.0
Step 13: Value =     115.00 | Next: P_mul_2.0
Step 14: Value =     230.00 | Next: P_sub_3.0
------------------------------------------------------------

Cycle analysis:
  Nodes in loop: 6
  Steps executed: 14
  Full cycles: 2
  Partial cycle: 2 nodes

No results in stash (loop has no natural end)
```

## Value Progression Analysis

| Step | Operation | Calculation | Result |
|------|-----------|-------------|--------|
| 0 | (start) | - | 10 |
| 1 | add_1 | 10 + 1 | 11 |
| 2 | mul_2 | 11 × 2 | 22 |
| 3 | sub_3 | 22 - 3 | 19 |
| 4 | add_5 | 19 + 5 | 24 |
| 5 | truediv_2 | 24 ÷ 2 | 12 |
| 6 | mul_3 | 12 × 3 | 36 |
| 7 | add_1 | 36 + 1 | 37 |
| 8 | mul_2 | 37 × 2 | 74 |
| 9 | sub_3 | 74 - 3 | 71 |
| 10 | add_5 | 71 + 5 | 76 |
| 11 | truediv_2 | 76 ÷ 2 | 38 |
| 12 | mul_3 | 38 × 3 | 114 |
| 13 | add_1 | 114 + 1 | 115 |
| 14 | mul_2 | 115 × 2 | 230 |

## Performance & Characteristics

- **6 nodes** in the ring
- **6 connections** (including the back-edge)
- **14 execution steps** (configurable)
- **2.33 complete cycles** (14 ÷ 6)
- **Infinite potential**: Loop would continue forever without step limit
- **No stash results**: Loops don't have natural endpoints

## Comparison with Chain Example

| Feature | Chain (50 nodes) | Loop (6 nodes) |
|---------|------------------|----------------|
| Topology | Linear | Circular |
| Nodes | 50 | 6 |
| Connections | 49 | 6 |
| Natural end | Yes | No |
| Stash results | Yes | No |
| Execution control | Automatic | Manual limit |
| Use case | Sequential pipeline | Cyclic processing |

## Related Files
- Source: `workspace/loop_6_nodes.py`
- Visualization: `renders/loop_6_nodes.gv.png` (when rendered)
- Chain example: `workspace/chain_50_nodes.py`
- Factory implementation: `src/hyperway/tools.py`

## Notes
- The loop demonstrates **controlled infinite execution**
- The stepper naturally handles cycles without special logic
- Step limiting prevents runaway execution
- Useful for modeling: iterative algorithms, state machines, event loops, feedback systems
