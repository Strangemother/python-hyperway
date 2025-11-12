# Streaming Results Proposal

## Overview

This document proposes a streaming API for accessing stepper results in real-time as graph execution progresses. Currently, users must wait until execution completes to access results. A streaming API would enable reactive patterns, progress monitoring, and early result processing.

> The streaming is lazy and event-driven - it only emits values when actual results are collected; or "pop on leaf".

## The Problem

Current workflow requires complete execution before accessing results:

```python
g.stepper_prepare(start, 10)
s = g.stepper()

# Must complete ALL execution first
while s.step():
    pass

# Only NOW can we see results
results = s.get_results()
```

**Limitations:**
- Can't observe intermediate results
- No progress feedback for long-running graphs
- Can't react to results as they arrive
- Memory accumulates in stash until completion

## Proposed Solution: `stream()` Method

Add a streaming iterator that yields results as they're produced:

```python
g.stepper_prepare(start, 10)
s = g.stepper()

# Stream results as they arrive
for result in s.stream():
    print(f"Got result: {result}")
    # React immediately to each result
```

## Core Usage Patterns

### 1. Simple Streaming - Process as Available

```python
from hyperway import Graph, as_unit
from hyperway.tools import factory as f

g = Graph()
g.connect(f.add_10, f.add_20, f.add_30)

start = g.connect()[0].a  # Get first node
g.stepper_prepare(start, 5)
s = g.stepper()

# Stream results as they complete
for result in s.stream():
    print(f"Result: {result}")
    # Output: Result: 65
```

### 2. Streaming Multiple Endpoints

For graphs with multiple endpoints, stream results as each branch completes (reaches a leaf):

```python
# Graph with 3 branches - each branch has a LEAF node at the end
source = as_unit(lambda x: x * 2)
g.add(source, as_unit(lambda x: x + 10, name='fast'))      # Leaf: yields when complete
g.add(source, as_unit(lambda x: time.sleep(1) or x + 20, name='medium'))  # Leaf: yields after 1s
g.add(source, as_unit(lambda x: time.sleep(2) or x + 30, name='slow'))    # Leaf: yields after 2s

g.stepper_prepare(source, 5)
s = g.stepper()

# Results arrive ONLY when each leaf node completes
for result in s.stream():
    print(f"{time.time()}: {result}")
    # Output (with timestamps):
    # 1699999999.1: 20  (fast branch LEAF reached)
    # 1700000000.1: 30  (medium branch LEAF reached, +1s)
    # 1700000001.1: 40  (slow branch LEAF reached, +2s)
    
# Note: stream() did NOT yield during the intermediate 'source' node execution,
# only when each branch reached its endpoint and result was added to stash
```

### 3. Progress Monitoring

Track execution progress for long-running graphs:

```python
g = Graph()
# Large graph with 100 nodes...
g.stepper_prepare(start, input_data)
s = g.stepper()

total = s.result_count() if s.has_results() else None
processed = 0

for result in s.stream():
    processed += 1
    if total:
        print(f"Progress: {processed}/{total} ({processed/total*100:.1f}%)")
    else:
        print(f"Processed: {processed}")
```

### 4. Early Termination

Stop execution when a condition is met:

```python
g.stepper_prepare(start, 10)
s = g.stepper()

# Stop after first valid result
for result in s.stream():
    if result > 50:
        print(f"Found valid result: {result}")
        break
        # Stepper stops, remaining branches may not execute
```

### 5. Reactive Processing

React to results as they arrive:

```python
g.stepper_prepare(start, 10)
s = g.stepper()

# Process results immediately
for result in s.stream():
    # Send to message queue
    queue.publish(result)
    
    # Update metrics
    metrics.record(result)
    
    # Trigger downstream processing
    if result > threshold:
        trigger_alert(result)
```

### 6. Looped Graphs (Memory-Safe)

Stream handles cyclic graphs without memory explosion:

```python
# Graph with loop: A → B → C → D (leaf)
#                       ↑_____↓
# B loops back to itself, could execute many times

g = Graph()
a = as_unit(lambda x: x + 1, name='A')
b = as_unit(lambda x: x * 2, name='B')  
c = as_unit(lambda x: x + 5, name='C')
d = as_unit(lambda x: x, name='D')  # Leaf

g.add(a, b)
g.add(b, c)
g.add(c, d)
g.add(b, b)  # Loop: B can call itself

g.stepper_prepare(a, 1)
s = g.stepper()

# Stream safely handles the loop
# Results are POPPED, so stash never grows unbounded
count = 0
for result in s.stream():
    print(f"Result {count}: {result}")
    count += 1
    if count > 100:  # Safety limit
        break

# Stash is empty (all results were popped as yielded)
assert len(s.stash) == 0
```

## Implementation Design

### When to Yield - Key Concept

**Stream only yields when NEW results are added to the stash.**

The stash is populated when:
1. **Leaf nodes** complete (nodes with no outgoing connections)
2. **Branch ends** are reached (via `end_branch()` when `stash_ends=True`)
3. Execution hits a node with no further connections

**Stream does NOT yield:**
- During intermediate node execution (nodes with outgoing edges)
- When stepping through the graph without hitting endpoints
- When no new results have been added to stash

This means streaming is **event-driven** - yields happen only when results are actually produced.

### Visual Example

```
Graph: A → B → C → D (leaf)
                ↘ E (leaf)

Execution flow with stream():

step 1: Execute A → produces value, continues to B (NO YIELD - not a leaf)
step 2: Execute B → produces value, continues to C (NO YIELD - not a leaf)  
step 3: Execute C → produces value, branches to D and E (NO YIELD - not a leaf)
step 4: Execute D → LEAF reached, adds to stash → YIELD result from D
step 5: Execute E → LEAF reached, adds to stash → YIELD result from E
```

**Key Point:** `stream()` only yielded twice (at D and E), even though 5 nodes executed. It yielded when results were **collected** (added to stash), not when nodes were **executed**.

### Basic `stream()` Implementation

```python
def stream(self, unwrap=True):
    """Stream results as they become available during execution.
    
    Yields results immediately as branches complete, without waiting
    for full graph execution. Results are POPPED from stash as they're
    yielded, preventing memory buildup in looped graphs.
    
    IMPORTANT: Only yields when new results are added to stash (i.e., when
    execution reaches a leaf node or branch end). Does NOT yield during
    intermediate node execution.
    
    Args:
        unwrap: If True (default), extract values using ArgsPack.flat().
    
    Yields:
        Result values as they become available. Order depends on
        execution path and may not be deterministic.
    
    Note:
        Results are removed from stash after yielding. This prevents
        memory growth in looped/cyclic graphs. After streaming completes,
        stash will be empty unless execution is interrupted.
    
    Example:
        >>> for result in s.stream():
        ...     print(f"Got: {result}")
    """
    ok = 1 
    while ok:
        # Execute one step
        rows = self.step()
        
        # Check if any new results appeared in stash
        if len(self.stash) == 0:
            continue

        # Pop all current results from stash (use .pop()for efficiency)
        # Create snapshot of nodes to avoid dict sizechange during iteration
        for node in tuple(self.stash.keys()):
            # Pop the entire tuple of results for this node
            akw_tuple = self.stash.pop(node)
            
            # Yield each result for this node
            for akw in akw_tuple:
                value = akw.flat() if unwrap else akw
                yield value
        
        # Stop when no more rows to process
        ok = len(rows)
        if not ok:
            break
```

## Advanced Use Cases

### 1. Pipeline Composition

```python
# Chain processing pipelines
def process_stream(stream):
    for result in stream:
        transformed = transform(result)
        if validate(transformed):
            yield transformed

results = process_stream(s.stream())
for r in results:
    save_to_db(r)
```

### 3. Async/Await Integration

```python
async def async_stream():
    """Async wrapper for streaming"""
    for result in s.stream():
        await asyncio.sleep(0)  # Yield to event loop
        yield result

async def process_async():
    async for result in async_stream():
        await save_async(result)
```

## API Summary

### Core Method

**`stream(unwrap=True)`** - Stream results as they become available

- **Args:**
  - `unwrap` (bool): If True (default), extract values using `ArgsPack.flat()`. If False, return raw `ArgsPack` objects.

- **Returns:** Generator yielding results as leaf nodes complete

- **Usage:**
  ```python
  for result in s.stream():
      process(result)
  ```

### Future Extensions

The `stream()` method can be extended in the future with additional parameters for different behaviors:

```python
# Potential future options (not in initial implementation)
s.stream(unwrap=True, clear_stash=False, timeout=None)
```

## Compatibility Considerations

### Backward Compatibility

- **All existing code continues to work unchanged**
- `stream()` is purely additive
- Existing `get_results()` etc. remain unchanged
- No performance impact on non-streaming usage

### Memory Considerations

**Streaming automatically prevents memory buildup:**

```python
# Old way: accumulates all results in stash
while s.step():
    pass
results = s.get_results()  # All results stored in memory

# New way: results are popped as they're yielded
for result in s.stream():
    process(result)
    # Result removed from stash immediately after yielding
    # Stash only contains uncollected results

# After streaming completes:
assert len(s.stash) == 0  # Stash is empty (all results were popped)
```

**This is especially important for:**
- **Looped/cyclic graphs** - prevents unbounded memory growth
- **Long-running processes** - steady-state memory usage
- **Large result sets** - process and discard incrementally

**Note:** If you need to access results after streaming, collect them yourself:

```python
results = []
for result in s.stream():
    results.append(result)
    process(result)
# results list now contains everything
```

## Implementation Plan

### Initial Implementation
- Implement `stream(unwrap=True)` method
- **POP behavior**: Delete results from stash after yielding
- No offset tracking needed (simpler implementation!)
- Comprehensive tests for:
  - Single endpoint graphs
  - Multiple endpoint graphs  
  - Early termination (breaking from loop)
  - Unwrap True/False behavior
  - Empty graphs
  - **Looped/cyclic graphs** (verify stash doesn't grow)
  - Verify stash is empty after completion

### Key Implementation Notes
1. **No additional framework changes needed** - pure stepper method
2. **No state tracking required** - just pop from stash as we yield
3. **Memory-safe by default** - works correctly with infinite loops
4. **Simpler than offset approach** - less code, clearer intent

### Future Extensions (Optional)
Future versions could add optional parameters to `stream()`:
- `timeout=None` - Timeout for long operations
- `max_results=None` - Limit number of results
- Filter/transform callbacks if needed

## Design Decisions

### 1. Stash Behavior
**Decision:** POP results from stash as they're yielded
- Prevents memory buildup in looped/cyclic graphs
- Stash only contains uncollected results
- If user needs results afterward, they can collect them during streaming
- Critical for long-running or infinite graph execution

### 2. Error Handling
**Decision:** Let errors propagate naturally
- If a node raises an exception, `stream()` raises it
- User can wrap in try/except if needed
- Consistent with `step()` behavior

### 3. Ordering
**Decision:** Document as non-deterministic
- Order depends on execution path
- No performance penalty for ordering guarantees
- Users can sort results afterward if needed

### 4. Iterator Protocol
**Decision:** Use generator (`for result in s.stream()`)
- Pythonic and composable
- Works with `itertools`, comprehensions, etc.
- Clear distinction from `step()` (which uses `while`)

## Example Code

A working example will be added to `workspace/streaming-basic.py`:

```python
"""Basic streaming example"""
from hyperway import Graph, as_unit
from hyperway.tools import factory as f

# Simple linear graph
g = Graph()
chain = g.connect(f.add_10, f.add_20, f.add_30)
start = chain[0].a

g.stepper_prepare(start, 5)
s = g.stepper()

# Stream and process results
for result in s.stream():
    print(f"Result: {result}")

# Can still access all results afterward
all_results = s.get_results()
print(f"Total results: {all_results}")
```

## Summary

The streaming API provides:
- ✅ Real-time result access
- ✅ Progress monitoring capabilities  
- ✅ Memory efficiency for large graphs
- ✅ Early termination support
- ✅ Reactive programming patterns
- ✅ Full backward compatibility

**Next Steps:**
1. Review this proposal and provide feedback
2. Implement Phase 1 basic streaming
3. Add comprehensive tests
4. Create working examples
5. Update documentation

---

*This proposal was collaboratively designed and documented with the assistance of Claude Sonnet 4.5, whose insights helped refine the streaming architecture and identify the elegant "pop on yield" solution for memory-safe graph execution.*
