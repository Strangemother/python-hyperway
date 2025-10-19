# Hyperway Graph Examples Comparison

## Overview
This document compares two example implementations demonstrating different graph topologies in the hyperway library.

## Examples

### 1. Chain of 50 Nodes (`chain_50_nodes.py`)
**Topology**: Linear chain (sequential pipeline)
```
A → B → C → D → ... → Z (end)
```

### 2. Loop of 6 Nodes (`loop_6_nodes.py`)
**Topology**: Circular ring (infinite cycle)
```
A → B → C → D → E → F → A (repeats)
```

## Detailed Comparison

| Aspect | Chain (50 nodes) | Loop (6 nodes) |
|--------|------------------|----------------|
| **Topology** | Linear | Circular |
| **Structure** | A→B→C→...→Z | A→B→C→D→E→F→A |
| **Nodes** | 50 | 6 |
| **Connections** | 49 | 6 (including back-edge) |
| **Has endpoint** | ✓ Yes | ✗ No |
| **Execution** | Runs to completion | Infinite (requires limit) |
| **Step control** | Automatic (stops at end) | Manual (max_steps=14) |
| **Stash results** | ✓ Yes (1 result) | ✗ No (empty) |
| **Value tracking** | Via stash | Via step iteration |
| **Initial value** | 10 | 10 |
| **Final value** | 2535.6 (after 50 steps) | 230.0 (after 14 steps) |

## Code Structure Comparison

### Graph Creation

**Chain (50 nodes):**
```python
# Sequential connection
units = [as_unit(op) for op in operations]
chain = g.connect(*units)  # Auto-chains all units
```

**Loop (6 nodes):**
```python
# Circular connection with modulo
for i in range(len(units)):
    next_i = (i + 1) % len(units)  # Wraps to 0
    g.add(units[i], units[next_i])
```

### Execution Control

**Chain (50 nodes):**
```python
# Runs until completion
while True:
    rows = stepper.step()
    if not rows:
        break  # Natural endpoint reached
```

**Loop (6 nodes):**
```python
# Fixed iteration count
max_steps = 14
for step_num in range(max_steps):
    rows = stepper.step()
    # Track values during execution
```

### Result Collection

**Chain (50 nodes):**
```python
# Results collected in stash
for func, akw_tuple in stepper.stash.items():
    for akw in akw_tuple:
        final_value = akw.args[0]  # 2535.6
```

**Loop (6 nodes):**
```python
# Track values during iteration
values = []
for step_num in range(max_steps):
    rows = stepper.step()
    for caller, akw in rows:
        values.append(akw.args[0])
# values[-1] = 230.0
```

## Use Cases

### Linear Chain Pattern
Best for:
- Data transformation pipelines
- Sequential processing workflows
- ETL (Extract, Transform, Load) operations
- Multi-stage computations
- Functional composition chains

### Circular Loop Pattern
Best for:
- Iterative algorithms
- State machines
- Event loops
- Feedback systems
- Cyclic data processing
- Game loops
- Simulation steps

## Performance Characteristics

### Chain of 50 Nodes
- **Time complexity**: O(n) where n = number of nodes
- **Space complexity**: O(1) for execution, O(n) for graph storage
- **Predictable**: Always terminates after n steps
- **Scalable**: Can handle very long chains efficiently

### Loop of 6 Nodes
- **Time complexity**: O(k) where k = iteration count
- **Space complexity**: O(1) for execution, O(n) for graph storage
- **Unbounded**: Continues forever without limit
- **Efficient**: Small memory footprint for cyclic patterns

## Value Flow Examples

### Chain: 10 → ... → 2535.6 (50 operations)
```
10 →[+1]→ 11 →[×2]→ 22 →[−3]→ 19 →[+5]→ 24 →[÷2]→ 12 →[×3]→ 36 →[+10]→ 46 → ... → 2535.6
```

### Loop: 10 → 36 → 114 → 230 → ... (cycles forever)
```
Cycle 1: 10 →[+1]→ 11 →[×2]→ 22 →[−3]→ 19 →[+5]→ 24 →[÷2]→ 12 →[×3]→ 36
Cycle 2: 36 →[+1]→ 37 →[×2]→ 74 →[−3]→ 71 →[+5]→ 76 →[÷2]→ 38 →[×3]→ 114
Cycle 3: 114 →[+1]→ 115 →[×2]→ 230 →[−3]→ 227 →[+5]→ 232 →[÷2]→ 116 → ...
```

## Running the Examples

### Chain Example
```bash
# Basic run
python workspace/chain_50_nodes.py

# With visualization
python workspace/chain_50_nodes.py --render
```

### Loop Example
```bash
# Basic run
python workspace/loop_6_nodes.py

# With visualization
python workspace/loop_6_nodes.py --render
```

## Graph Visualizations

Both examples support graphviz rendering with the `--render` flag:

- **Chain**: Shows a long left-to-right flow
- **Loop**: Shows a circular structure with back-edge

Files saved to `renders/` directory:
- `chain_50_nodes.gv.png` (39KB)
- `loop_6_nodes.gv.png` (18KB)

## Key Takeaways

1. **Topology flexibility**: Hyperway handles both linear and cyclic graphs naturally
2. **No special loop handling**: The stepper executes cycles without modification
3. **Control mechanisms differ**: Chains self-terminate, loops need limits
4. **Stash behavior**: Only nodes with no outgoing connections populate stash
5. **Factory power**: Both examples use the same Factory pattern for node creation

## Related Documentation
- Main README: `README.md`
- Chain example: `workspace/chain_50_nodes_README.md`
- Loop example: `workspace/loop_6_nodes_README.md`
- Stepper docs: `docs/stepper.md`
- Topology docs: `docs/topology.md`
