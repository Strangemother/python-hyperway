# Quick Reference: New Hyperway Examples

## Files Created

### Example Scripts
1. **`chain_50_nodes.py`** - Linear chain of 50 operations
2. **`loop_6_nodes.py`** - Circular loop of 6 operations (14 steps)

### Documentation
1. **`chain_50_nodes_README.md`** - Chain example documentation
2. **`loop_6_nodes_README.md`** - Loop example documentation
3. **`EXAMPLES_COMPARISON.md`** - Side-by-side comparison

### Generated Visualizations
1. **`renders/chain_50_nodes.gv.png`** - Chain graph image
2. **`renders/loop_6_nodes.gv.png`** - Loop graph image

## Quick Commands

```bash
# Run chain example (50 nodes)
python workspace/chain_50_nodes.py
python workspace/chain_50_nodes.py --render

# Run loop example (6 nodes, 14 steps)
python workspace/loop_6_nodes.py
python workspace/loop_6_nodes.py --render
```

## Key Results

### Chain of 50 Nodes
- **Input**: 10
- **Output**: 2535.6
- **Steps**: 50
- **Topology**: Linear (A→B→C→...→Z)

### Loop of 6 Nodes
- **Input**: 10
- **Output**: 230.0 (after 14 steps)
- **Steps**: 14 (2 full cycles + 2 nodes)
- **Topology**: Circular (A→B→C→D→E→F→A)

## Both Examples Demonstrate

✓ Factory-based node creation  
✓ Graph construction  
✓ Stepper execution  
✓ Value tracking  
✓ Graphviz rendering  
✓ Clean output formatting  

## Differences

| Feature | Chain | Loop |
|---------|-------|------|
| Termination | Automatic | Manual limit |
| Stash results | Yes | No |
| Use case | Pipelines | Iterations |
