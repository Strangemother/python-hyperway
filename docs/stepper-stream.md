# Stepper Streaming

The streaming API provides real-time access to graph execution results as they become available, enabling reactive patterns, progress monitoring, and memory-efficient processing of long-running or infinite graphs.

## Overview

Instead of waiting for complete graph execution to access results, the `stream()` function yields results immediately as branches complete (reach leaf nodes). This is particularly useful for:

- **Real-time processing** - React to results as they arrive
- **Progress monitoring** - Track execution of long-running graphs
- **Memory efficiency** - Results are popped from stash as they're yielded
- **Infinite loops** - Memory-safe execution of cyclic graphs
- **Early termination** - Stop execution when a condition is met

## Basic Usage

### OOP Style

```python
from hyperway import Graph
from hyperway.tools import factory as f

g = Graph()
g.connect(f.add_10, f.add_20, f.add_30)

start = g.connect()[0].a
g.stepper_prepare(start, 5)
s = g.stepper()

# Stream results as they become available
for result in s.stream():
    print(f"Result: {result}")
# Output: Result: 65
```

### Functional Style

```python
from hyperway.stepper import stream

g.stepper_prepare(start, 5)
s = g.stepper()

# Functional style - pass stepper to stream()
for result in stream(s):
    print(f"Result: {result}")
```

Both styles are functionally equivalent - choose whichever fits your coding style.

## How Streaming Works

### Event-Driven Yields

Streaming is **event-driven** - it only yields when results are **collected** (added to stash), not when nodes are **executed**.

Results are added to stash when execution reaches:
1. **Leaf nodes** - Nodes with no outgoing connections
2. **Branch ends** - When `stash_ends=True` (default)

**Key Point:** Intermediate node execution does NOT trigger yields.

#### Example Flow

```
Graph: A → B → C → D (leaf)
                ↘ E (leaf)

Execution with stream():
1. Execute A → continues to B (NO YIELD - not a leaf)
2. Execute B → continues to C (NO YIELD - not a leaf)
3. Execute C → branches to D and E (NO YIELD - not a leaf)
4. Execute D → LEAF reached → YIELD result from D
5. Execute E → LEAF reached → YIELD result from E
```

Stream yielded only twice (at D and E), even though 5 nodes executed.

### Memory-Safe POP Behavior

**Critical:** Results are **removed from stash** after yielding via `.pop()`.

This prevents memory buildup in looped/cyclic graphs:

```python
# Graph with loop: A → B → C (leaf)
#                       ↑___↓
# B loops back to itself

for result in s.stream():
    process(result)
    # Result removed from stash immediately
    # Stash stays small even with infinite loops

# After streaming:
assert len(s.stash) == 0  # Stash is empty
```

## Common Patterns

### 1. Multiple Endpoints

Stream results from graphs with multiple branches:

```python
source = as_unit(lambda x: x * 2, name='source')
g.add(source, as_unit(lambda x: x + 10, name='branch_1'))
g.add(source, as_unit(lambda x: x + 20, name='branch_2'))
g.add(source, as_unit(lambda x: x + 30, name='branch_3'))

g.stepper_prepare(source, 5)
s = g.stepper()

# Each branch yields when it completes
for result in s.stream():
    print(f"Branch completed: {result}")
# Output (order may vary):
# Branch completed: 20
# Branch completed: 30
# Branch completed: 40
```

### 2. Progress Monitoring

Track execution progress for long-running graphs:

```python
processed = 0
for result in s.stream():
    processed += 1
    print(f"Processed {processed} results...")
    # Update progress bar, send metrics, etc.
```

### 3. Early Termination

Stop execution when a condition is met:

```python
for result in s.stream():
    if result > 50:
        print(f"Found target: {result}")
        break
        # Execution stops, remaining branches may not complete
```

### 4. Collecting Results While Streaming

Build a result list while processing:

```python
results = []
for result in s.stream():
    results.append(result)
    process(result)  # Also process immediately

# Now you have both: immediate processing AND a complete list
print(f"All results: {results}")
```

### 5. Looped/Cyclic Graphs

Stream safely handles infinite loops:

```python
# Create loop: A → B → C (leaf)
#                  ↑___↓
a = as_unit(lambda x: x + 1, name='A')
b = as_unit(lambda x: x * 2, name='B')
c = as_unit(lambda x: x, name='C')  # Leaf

g.add(a, b)
g.add(b, c)
g.add(b, b)  # Loop back to B

g.stepper_prepare(a, 1)
s = g.stepper()

# Safe with memory limits
count = 0
for result in s.stream():
    print(f"Result {count}: {result}")
    count += 1
    if count > 100:
        break

# Stash stays at 0 - results were popped as yielded
assert len(s.stash) == 0
```

### 6. Pipeline Composition

Chain stream processing with generators:

```python
def validate_results(stream):
    """Filter and transform streamed results"""
    for result in stream:
        if result > 10:
            yield result * 2

def save_results(stream):
    """Save validated results"""
    for result in stream:
        database.save(result)
        yield result

# Compose pipeline
validated = validate_results(s.stream())
saved = save_results(validated)

# Execute pipeline
list(saved)  # Consumes the entire pipeline
```

## API Reference

### `stream(stepper, unwrap=True)`

Functional-style streaming function.

**Parameters:**
- `stepper` (StepperC): A stepper instance to stream from
- `unwrap` (bool): If True (default), extract values using `ArgsPack.flat()`

**Yields:**
- Result values as they become available

**Example:**
```python
from hyperway.stepper import stream

for result in stream(s):
    process(result)
```

### `StepperC.stream(unwrap=True)`

OOP-style streaming method. Delegates to the standalone `stream()` function.

**Parameters:**
- `unwrap` (bool): If True (default), extract values using `ArgsPack.flat()`

**Yields:**
- Result values as they become available

**Example:**
```python
for result in s.stream():
    process(result)
```

### Unwrapping Behavior

When `unwrap=True` (default), uses `ArgsPack.flat()` which returns:
- **Single positional arg** → the value itself
- **Multiple positional args** → tuple of args
- **Only kwargs** → dict of kwargs
- **Args + kwargs** → tuple of (args, kwargs)
- **Nothing** → None

When `unwrap=False`, yields raw `ArgsPack` objects:

```python
for akw in s.stream(unwrap=False):
    print(f"Args: {akw.args}, Kwargs: {akw.kwargs}")
    value = akw.flat()  # Manually unwrap if needed
```

## Performance Considerations

### Optimized Loop

The streaming loop uses an optimized pattern:

```python
ok = 1 
while ok:
    rows = stepper.step()
    
    if len(stepper.stash) == 0:
        continue
    
    # Process results...
    
    ok = len(rows)  # Natural loop exit - no explicit break needed
```

This avoids an unnecessary `if not ok: break` check on every iteration (~3.6% faster).

### Memory Efficiency

- **POP behavior** - Results removed via `.pop()` after yielding
- **Tuple snapshots** - `tuple(stepper.stash.keys())` prevents dict size change during iteration
- **Steady-state memory** - Stash size stays constant even in infinite loops

### When NOT to Use Streaming

Streaming adds overhead. Don't use it when:
- You need all results at once anyway
- Graph execution is trivial (< 5 nodes)
- You're not processing results until completion

In these cases, use the standard approach:

```python
while s.step():
    pass
results = s.get_results()
```

## Comparison: Standard vs Streaming

### Standard Approach

```python
# Execute completely first
while s.step():
    pass

# Then access all results
results = s.get_results()
for result in results:
    process(result)

# Stash accumulates all results in memory
```

**Pros:**
- Simpler for small graphs
- All results available together

**Cons:**
- Can't react during execution
- Memory accumulates
- No progress feedback
- Unsafe for infinite loops

### Streaming Approach

```python
# Process as execution happens
for result in s.stream():
    process(result)
    # React immediately

# Stash is empty after streaming
```

**Pros:**
- Real-time processing
- Memory-safe (results popped)
- Progress monitoring
- Early termination
- Safe for infinite loops

**Cons:**
- Results not stored (unless you collect them)
- Order may be non-deterministic
- Slightly more complex

## Advanced Topics

### Non-Deterministic Ordering

Result order depends on execution path and is not guaranteed:

```python
# Multiple branches may complete in any order
for result in s.stream():
    print(result)
# Output order varies: [20, 30, 40] or [30, 20, 40] or ...

# If you need ordering, collect and sort:
results = sorted(list(s.stream()))
```

### Async Integration

Wrap streaming in async context:

```python
async def async_stream(stepper):
    """Async wrapper for streaming"""
    for result in stepper.stream():
        await asyncio.sleep(0)  # Yield to event loop
        yield result

async def process():
    async for result in async_stream(s):
        await save_async(result)
```

### Error Handling

Errors propagate naturally from the graph:

```python
try:
    for result in s.stream():
        process(result)
except SomeNodeError as e:
    print(f"Graph execution failed: {e}")
    # Handle error appropriately
```

## Best Practices

1. **Use streaming for long-running graphs** - Get feedback during execution
2. **Always use unwrap=True** - Unless you need direct ArgsPack access
3. **Collect results if needed** - Stream doesn't store them for you
4. **Add safety limits for loops** - Use counters or timeouts
5. **Handle non-deterministic order** - Don't assume result sequence
6. **Consider memory tradeoffs** - Streaming vs collecting all results

## See Also

- [Stepper Documentation](stepper.md) - Complete stepper API reference
- [Topology Guide](topology.md) - Understanding graph structure
- [ArgsPack Flat Method](stepper.md#argspack-flat) - Result unwrapping details
- [Result Access Methods](stepper.md#result-access) - Alternative result retrieval

---

**Pro Tip:** The streaming API combines the power of Python generators with graph execution, giving you fine-grained control over how and when results are processed. Use it when you need reactive patterns or memory efficiency!
