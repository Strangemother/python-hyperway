# Result Access Improvement Proposal

**Date:** November 8, 2025  
**Status:** Proposed  
**Author:** Analysis of current Hyperway implementation

## Executive Summary

This document proposes improvements to how users access execution results in Hyperway. The current `stash` system, while functional, creates friction for users through non-intuitive access patterns and manual unwrapping of result values. We propose a three-phase enhancement plan that provides immediate improvements while maintaining full backwards compatibility.

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Problems with Current Approach](#problems-with-current-approach)
3. [Proposed Solution](#proposed-solution)
4. [Implementation Phases](#implementation-phases)
5. [Examples and Use Cases](#examples-and-use-cases)
6. [Migration Path](#migration-path)

---

## Current State Analysis

### How the Stash System Works

The current result retrieval mechanism in Hyperway works as follows:

1. The stepper walks the graph executing nodes sequentially
2. When a node has no outgoing connections (leaf/end node), results are stored in `stepper.stash`
3. `stash` is implemented as a `defaultdict(tuple)` keyed by the final node (Unit object)
4. Values are tuples of `ArgsPack` objects
5. Users must manually access and unwrap `stepper.stash` after execution completes

### Current API

```python
from hyperway.graph import Graph
from hyperway.tools import factory as f

g = Graph()
g.connect(f.add_10, f.add_20, f.add_30)

# Execute graph
g.stepper_prepare(first_node, 10)
s = g.stepper()
while s.step():
    pass

# Access results - current approach
results = s.stash  
# defaultdict(tuple, {<Unit(func=add_30)>: (<ArgsPack(*(60,), **{})>,)})

# Or use helper methods
for caller, akw in s.flush():  # Yields and clears stash
    print(caller, akw)
    
for akw in s.peek():  # Yields values without clearing
    print(akw)
```

### Stash Implementation

From `src/hyperway/stepper.py`:

```python
class StepperC(object):
    stash_ends = True
    
    def __init__(self, graph, rows=None):
        self.graph = graph
        self.reset_stash()
    
    def reset_stash(self):
        self.stash = defaultdict(tuple)
    
    def end_branch(self, func, akw):
        """Store results when execution path ends."""
        if self.stash_ends:
            self.stash[func] += (akw,)
            return ()
        return ((None, akw,),)
    
    def flush(self):
        """Yield all stash contents and clear."""
        for caller, akw in self.stash.items():
            yield caller, akw
        self.reset_stash()
    
    def peek(self):
        """Yield stash values without clearing."""
        for akw in self.stash.values():
            yield akw
```

---

## Problems with Current Approach

### 1. Non-intuitive Access Pattern

**Issue:** Users need to understand the internal structure of `defaultdict(tuple)` and manually extract values.

```python
# Current: Requires understanding internal structure
for node, akw_tuple in s.stash.items():
    for akw in akw_tuple:
        if akw.args:
            result = akw.args[0]  # Extract first positional arg
            print(result)

# What users expect:
result = s.get_result()  # Simple!
```

**Impact:** 
- Steep learning curve for new users
- Verbose boilerplate code
- Easy to make mistakes extracting values

### 2. Opaque Result Keys

**Issue:** Results are keyed by Unit objects which are opaque to users.

```python
# Current: Unit objects as keys
stash = {<Unit(func=add_30) at 0x...>: (<ArgsPack...>,)}

# Users can't easily identify which result is which
for unit, results in stash.items():
    print(unit)  # <Unit(func=add_30)> - not very helpful
```

**Impact:**
- Difficult to identify which node produced which result
- No clear relationship between graph structure and results
- Hard to debug or trace execution

### 3. Multiple End Points Create Confusion

**Issue:** Graphs with multiple leaf nodes scatter results across dictionary keys.

```python
# Graph with 3 endpoints
g.connect(split, branch_a)
g.connect(split, branch_b)
g.connect(split, branch_c)

# Results scattered across 3 keys
stash = {
    <Unit(branch_a)>: (<ArgsPack(10)>,),
    <Unit(branch_b)>: (<ArgsPack(20)>,),
    <Unit(branch_c)>: (<ArgsPack(30)>,),
}

# No clear ordering or relationship
```

**Impact:**
- Unpredictable result ordering
- Must know graph topology to interpret results
- Cannot easily collect "all results" as a simple list

### 4. Loss of Execution Context

**Issue:** Results don't carry information about how they were produced.

```python
# Multiple paths to same node
g.add(route_a, handler)
g.add(route_b, handler)

# Both results end up in same stash entry
stash = {<Unit(handler)>: (<ArgsPack(1)>, <ArgsPack(2)>)}

# Can't tell which path produced which result
```

**Impact:**
- Ambiguous results from convergent paths
- No execution path tracing
- Difficult to debug or audit execution
- Cannot implement path-aware result handling

### 5. Synchronous Only

**Issue:** Must wait for complete execution before accessing results.

```python
# Current: Must complete entire graph
while s.step():
    pass

# Only then can access results
results = s.stash

# Cannot process results incrementally
# Cannot stop early when target result found
# Cannot stream results for long-running graphs
```

**Impact:**
- No incremental processing
- Cannot short-circuit execution
- Memory accumulation for large result sets
- No progress feedback during execution

### 6. Manual Unwrapping Required

**Issue:** ArgsPack wrapper adds friction for accessing actual values.

```python
# Current: Manual unwrapping
akw = stash[node][0]
if akw.args:
    value = akw.args[0]  # Single value
    # or
    values = akw.args    # Multiple values
elif akw.kw:
    value = akw.kw       # Keyword arguments

# Desired: Direct access
value = results[0]
```

**Impact:**
- Verbose code
- Easy to forget unwrapping
- Inconsistent patterns (args vs kw)
- Harder to compose with standard Python tools

### 7. No Type Safety or Validation

**Issue:** Results are untyped and cannot be validated.

```python
# Current: No type information
results = s.stash  # What types are in here?

# Cannot:
# - Validate result schemas
# - Transform results automatically
# - Provide type hints for IDEs
# - Enforce contracts between nodes
```

**Impact:**
- Runtime errors from unexpected types
- No IDE autocomplete
- Difficult to document expected results
- No automatic serialization/deserialization

---

## Proposed Solution

### Design Principles

1. **Simple by default, powerful when needed** - Common cases should be one-liners
2. **Results should be immediately usable** - No manual unwrapping required
3. **Support both synchronous and streaming patterns** - Choose based on use case
4. **Preserve execution context when requested** - Optional rich result objects
5. **Fully backwards compatible** - Existing code continues to work
6. **Progressive enhancement** - Each phase adds value independently

---

## Implementation Phases

### Phase 1: Backwards-Compatible Enhancement (Quick Win)

**Goal:** Add convenience methods to existing `StepperC` class without breaking changes.

**Timeline:** Immediate implementation  
**Complexity:** Low  
**Impact:** High user satisfaction improvement

#### New Methods

```python
class StepperC:
    def get_results(self, unwrap=True):
        """Get all results as a flat list.
        
        Args:
            unwrap: If True, extract values from ArgsPack (default)
                   If False, return ArgsPack objects
        
        Returns:
            List of result values
            
        Example:
            >>> s.get_results()
            [60, 42, 100]
        """
        results = []
        for akw_tuple in self.stash.values():
            for akw in akw_tuple:
                if unwrap:
                    # Extract value from ArgsPack
                    if akw.args:
                        # Single arg: unwrap, multiple: return tuple
                        results.append(akw.args[0] if len(akw.args) == 1 else akw.args)
                    elif akw.kw:
                        results.append(akw.kw)
                    else:
                        results.append(None)
                else:
                    results.append(akw)
        return results
    
    def get_result(self, unwrap=True, default=None):
        """Get the first result (for single-endpoint graphs).
        
        Args:
            unwrap: If True, extract value from ArgsPack
            default: Value to return if no results exist
        
        Returns:
            The first result value, or default if no results
            
        Example:
            >>> s.get_result()
            60
        """
        results = self.get_results(unwrap=unwrap)
        return results[0] if results else default
    
    def get_results_dict(self, key='name', unwrap=True):
        """Get results organized by node attribute.
        
        Args:
            key: Node attribute to use as dict key ('name', 'id', or callable)
            unwrap: If True, extract values from ArgsPack
        
        Returns:
            Dict mapping node key to list of results
            
        Example:
            >>> s.get_results_dict()
            {'add_30': [60], 'mul_2': [120]}
        """
        results_dict = {}
        for node, akw_tuple in self.stash.items():
            # Get node key
            if callable(key):
                node_key = key(node)
            else:
                node_key = getattr(node, key, str(node))
            
            # Extract results for this node
            node_results = []
            for akw in akw_tuple:
                if unwrap:
                    if akw.args:
                        node_results.append(akw.args[0] if len(akw.args) == 1 else akw.args)
                    elif akw.kw:
                        node_results.append(akw.kw)
                    else:
                        node_results.append(None)
                else:
                    node_results.append(akw)
            
            results_dict[node_key] = node_results
        return results_dict
    
    def has_results(self):
        """Check if any results exist.
        
        Returns:
            True if stash contains results, False otherwise
            
        Example:
            >>> s.has_results()
            True
        """
        return len(self.stash) > 0
    
    def result_count(self):
        """Count total number of results.
        
        Returns:
            Total number of result values across all nodes
            
        Example:
            >>> s.result_count()
            3
        """
        count = 0
        for akw_tuple in self.stash.values():
            count += len(akw_tuple)
        return count
```

#### Benefits

- ✅ Zero breaking changes - all existing code works
- ✅ Immediate UX improvement
- ✅ Minimal code to implement (~50 lines)
- ✅ Easy to test and document
- ✅ Natural Python idioms

#### Example Usage

```python
# Simple single result
s.get_result()  # 60

# Multiple results
s.get_results()  # [60, 42, 100]

# Organized by node
s.get_results_dict()  # {'add_30': [60], 'handler_a': [42]}

# Check existence
if s.has_results():
    print(f"Got {s.result_count()} results")

# Keep ArgsPack wrapper if needed
akws = s.get_results(unwrap=False)
```

---

### Phase 2: Result Collector System

**Goal:** Add pluggable result collection strategies for advanced use cases.

**Timeline:** After Phase 1 stabilizes  
**Complexity:** Medium  
**Impact:** Enables advanced patterns (streaming, callbacks, custom handling)

#### ResultCollector Base Class

```python
# New file: src/hyperway/results.py

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
from .packer import ArgsPack
from .nodes import Unit


class ResultCollector(ABC):
    """Base class for result collection strategies.
    
    ResultCollectors handle how results are accumulated during
    graph execution. Different implementations provide different
    collection and access patterns.
    """
    
    @abstractmethod
    def add(self, node: Unit, akw: ArgsPack):
        """Called when a result is produced.
        
        Args:
            node: The node that produced the result
            akw: The result data wrapped in ArgsPack
        """
        pass
    
    def finalize(self):
        """Called when execution completes.
        
        Override to perform any cleanup or final processing.
        """
        pass
    
    def reset(self):
        """Reset collector to initial state.
        
        Override to clear any accumulated results.
        """
        pass
```

#### ListCollector Implementation

```python
class ListCollector(ResultCollector):
    """Collect results in a simple list.
    
    The most common use case - accumulate all results
    in order of production.
    
    Example:
        collector = ListCollector()
        stepper = g.stepper(node, 10, collector=collector)
        while stepper.step():
            pass
        results = collector.all()  # [60, 42, 100]
    """
    
    def __init__(self, unwrap: bool = True):
        """Initialize list collector.
        
        Args:
            unwrap: If True, extract values from ArgsPack
        """
        self.unwrap = unwrap
        self.results = []
    
    def add(self, node: Unit, akw: ArgsPack):
        """Add result to list."""
        if self.unwrap:
            if akw.args:
                value = akw.args[0] if len(akw.args) == 1 else akw.args
            elif akw.kw:
                value = akw.kw
            else:
                value = None
        else:
            value = akw
        
        self.results.append(value)
    
    def first(self, default=None):
        """Get first result."""
        return self.results[0] if self.results else default
    
    def last(self, default=None):
        """Get last result."""
        return self.results[-1] if self.results else default
    
    def all(self):
        """Get all results."""
        return self.results
    
    def count(self):
        """Count results."""
        return len(self.results)
    
    def reset(self):
        """Clear results."""
        self.results.clear()
```

#### DictCollector Implementation

```python
class DictCollector(ResultCollector):
    """Collect results organized by node attribute.
    
    Useful for graphs with multiple endpoints where you
    want to distinguish results by node.
    
    Example:
        collector = DictCollector(key='name')
        stepper = g.stepper(node, 10, collector=collector)
        while stepper.step():
            pass
        results = collector.results
        # {'handler_a': [42], 'handler_b': [100]}
    """
    
    def __init__(self, key: str = 'name', unwrap: bool = True):
        """Initialize dict collector.
        
        Args:
            key: Node attribute to use as dict key ('name', 'id', etc)
            unwrap: If True, extract values from ArgsPack
        """
        self.key = key
        self.unwrap = unwrap
        self.results = {}
    
    def add(self, node: Unit, akw: ArgsPack):
        """Add result to dict under node key."""
        # Get node key
        node_key = getattr(node, self.key, str(node))
        
        # Extract value
        if self.unwrap:
            if akw.args:
                value = akw.args[0] if len(akw.args) == 1 else akw.args
            elif akw.kw:
                value = akw.kw
            else:
                value = None
        else:
            value = akw
        
        # Add to results
        if node_key not in self.results:
            self.results[node_key] = []
        self.results[node_key].append(value)
    
    def get(self, key: str, default=None):
        """Get results for specific key."""
        return self.results.get(key, default)
    
    def keys(self):
        """Get all node keys."""
        return self.results.keys()
    
    def values(self):
        """Get all result lists."""
        return self.results.values()
    
    def items(self):
        """Get all key-value pairs."""
        return self.results.items()
    
    def reset(self):
        """Clear results."""
        self.results.clear()
```

#### CallbackCollector Implementation

```python
class CallbackCollector(ResultCollector):
    """Call a function for each result as it's produced.
    
    Useful for:
    - Processing results incrementally
    - Logging/monitoring execution
    - Side effects (sending to queue, database, etc)
    - Early termination based on results
    
    Example:
        def handle(value, node):
            print(f"Got {value} from {node.name}")
        
        collector = CallbackCollector(on_result=handle)
        stepper = g.stepper(node, 10, collector=collector)
        while stepper.step():
            pass  # Callback fires during execution
    """
    
    def __init__(self, 
                 on_result: Callable[[Any, Unit], None],
                 unwrap: bool = True):
        """Initialize callback collector.
        
        Args:
            on_result: Function called with (value, node) for each result
            unwrap: If True, extract values from ArgsPack before callback
        """
        self.on_result = on_result
        self.unwrap = unwrap
        self.count = 0
    
    def add(self, node: Unit, akw: ArgsPack):
        """Call callback with result."""
        # Extract value
        if self.unwrap:
            if akw.args:
                value = akw.args[0] if len(akw.args) == 1 else akw.args
            elif akw.kw:
                value = akw.kw
            else:
                value = None
        else:
            value = akw
        
        # Invoke callback
        self.on_result(value, node)
        self.count += 1
    
    def reset(self):
        """Reset counter."""
        self.count = 0
```

#### RichResultCollector Implementation

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Any, Optional


@dataclass
class Result:
    """Rich result object with execution context.
    
    Attributes:
        value: The actual result value
        node: The node that produced it
        timestamp: When result was produced
        metadata: Custom metadata dict
    """
    value: Any
    node: Unit
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: dict = field(default_factory=dict)
    
    def unwrap(self):
        """Get raw value."""
        return self.value
    
    def __repr__(self):
        node_name = getattr(self.node, 'name', str(self.node))
        return f"Result({self.value}, from={node_name})"


class RichResultCollector(ResultCollector):
    """Collect results with full execution context.
    
    Each result includes:
    - The value
    - Source node
    - Timestamp
    - Optional metadata
    
    Example:
        collector = RichResultCollector()
        stepper = g.stepper(node, 10, collector=collector)
        while stepper.step():
            pass
        
        for result in collector.results:
            print(f"{result.value} from {result.node.name}")
            print(f"at {result.timestamp}")
    """
    
    def __init__(self):
        self.results: List[Result] = []
    
    def add(self, node: Unit, akw: ArgsPack):
        """Add rich result."""
        # Extract value
        if akw.args:
            value = akw.args[0] if len(akw.args) == 1 else akw.args
        elif akw.kw:
            value = akw.kw
        else:
            value = None
        
        # Create rich result
        result = Result(value=value, node=node)
        self.results.append(result)
    
    def values(self):
        """Get just the values."""
        return [r.value for r in self.results]
    
    def nodes(self):
        """Get just the nodes."""
        return [r.node for r in self.results]
    
    def first(self, default=None):
        """Get first result."""
        return self.results[0] if self.results else default
    
    def last(self, default=None):
        """Get last result."""
        return self.results[-1] if self.results else default
    
    def filter(self, predicate: Callable[[Result], bool]):
        """Filter results by predicate."""
        return [r for r in self.results if predicate(r)]
    
    def reset(self):
        """Clear results."""
        self.results.clear()
```

#### StepperC Integration

```python
# Modifications to src/hyperway/stepper.py

class StepperC:
    def __init__(self, graph, rows=None, collector=None):
        self.graph = graph
        self.run = 1
        self.reset_stash()
        self.start_nodes = None
        self.start_akw = None
        self.rows = rows
        self.collector = collector  # NEW: Optional result collector
    
    def end_branch(self, func, akw):
        """Store results when execution path ends."""
        if self.stash_ends:
            self.stash[func] += (akw,)
        
        # NEW: Also notify collector if present
        if self.collector is not None:
            self.collector.add(func, akw)
        
        return ()
```

#### Graph Integration

```python
# Modifications to src/hyperway/graph/graph.py

class Graph:
    def stepper(self, n=None, *a, collector=None, **kw):
        """Create a stepper for graph execution.
        
        Args:
            n: Starting node
            *a: Positional arguments for starting node
            collector: Optional ResultCollector for custom result handling
            **kw: Keyword arguments for starting node
        
        Returns:
            StepperC instance
        """
        _stepper_class = self.get_stepper_class()
        
        if self._stepper_rows is not None:
            stepper = _stepper_class(self, self._stepper_rows, collector=collector)
            return stepper

        stepper = _stepper_class(self, collector=collector)
        n = n or self._stepper_callers
        akw = self._stepper_args
        initiate_mode = self._stepper_initiate

        if len(a) + len(kw) > 0:
            akw = argspack(*a, **kw)
        if n is not None:
            stepper.prepare(n, akw=akw, initiate=initiate_mode)
        return stepper
```

#### Benefits

- ✅ Pluggable architecture for custom handling
- ✅ Streaming/callback patterns enabled
- ✅ Rich context preservation when needed
- ✅ Still backwards compatible (collector is optional)
- ✅ Easy to extend with new collectors

#### Example Usage

```python
from hyperway.results import (
    ListCollector, DictCollector, CallbackCollector, RichResultCollector
)

# Simple list collection
collector = ListCollector()
stepper = g.stepper(node, 10, collector=collector)
while stepper.step():
    pass
results = collector.all()  # [60, 42, 100]

# Organized by node
collector = DictCollector(key='name')
stepper = g.stepper(node, 10, collector=collector)
while stepper.step():
    pass
results = collector.results  # {'add_30': [60], 'handler': [42]}

# Callback for each result
def log_result(value, node):
    print(f"Result: {value} from {node.name}")

collector = CallbackCollector(on_result=log_result)
stepper = g.stepper(node, 10, collector=collector)
while stepper.step():
    pass  # Logs results as they arrive

# Rich results with context
collector = RichResultCollector()
stepper = g.stepper(node, 10, collector=collector)
while stepper.step():
    pass

for result in collector.results:
    print(f"{result.value} from {result.node.name} at {result.timestamp}")
```

---

### Phase 3: High-Level Execution APIs

**Goal:** Add Pythonic high-level APIs for common execution patterns.

**Timeline:** After Phase 2 stabilizes  
**Complexity:** Medium-High  
**Impact:** Maximum ease-of-use for common cases

#### ExecutionContext Class

```python
# Add to src/hyperway/results.py

class ExecutionContext:
    """Context for graph execution with automatic result collection.
    
    Can be used as a context manager or called directly.
    
    Example:
        # Context manager
        with g.execute(node, 10) as results:
            pass
        print(results.first())
        
        # Direct execution
        results = g.execute(node, 10).run()
        print(results.first())
    """
    
    def __init__(self, graph, start_node, args, kwargs, collector=None):
        self.graph = graph
        self.start_node = start_node
        self.args = args
        self.kwargs = kwargs
        self.collector = collector or ListCollector()
        self.stepper = None
    
    def run(self):
        """Execute graph and return collector."""
        self.stepper = self.graph.stepper(
            self.start_node, 
            *self.args,
            collector=self.collector,
            **self.kwargs
        )
        
        while self.stepper.step():
            pass
        
        self.collector.finalize()
        return self.collector
    
    def __enter__(self):
        """Context manager entry."""
        self.run()
        return self.collector
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False
```

#### Graph High-Level Methods

```python
# Add to src/hyperway/graph/graph.py

class Graph:
    def execute(self, start_node, *args, collector=None, **kwargs):
        """Execute graph and collect results.
        
        Can be used as context manager or called with .run()
        
        Args:
            start_node: Node to start execution from
            *args: Positional arguments for start node
            collector: Optional custom ResultCollector
            **kwargs: Keyword arguments for start node
        
        Returns:
            ExecutionContext that can be used as context manager or called
        
        Example:
            # Context manager
            with g.execute(node, 10) as results:
                pass
            print(results.first())
            
            # Direct call
            results = g.execute(node, 10).run()
            print(results.first())
        """
        from ..results import ExecutionContext
        return ExecutionContext(self, start_node, args, kwargs, collector)
    
    def run(self, start_node, *args, **kwargs):
        """Execute graph and return results immediately.
        
        Convenience method for simple execution cases.
        
        Args:
            start_node: Node to start execution from
            *args: Positional arguments for start node
            **kwargs: Keyword arguments for start node
        
        Returns:
            List of result values
        
        Example:
            results = g.run(node, 10)
            print(results)  # [60]
        """
        collector = ListCollector()
        stepper = self.stepper(start_node, *args, collector=collector, **kwargs)
        
        while stepper.step():
            pass
        
        return collector.all()
    
    def stream(self, start_node, *args, **kwargs):
        """Stream results as they are produced.
        
        Yields results during execution, allowing incremental
        processing without waiting for completion.
        
        Args:
            start_node: Node to start execution from
            *args: Positional arguments for start node
            **kwargs: Keyword arguments for start node
        
        Yields:
            Result values as execution progresses
        
        Example:
            for result in g.stream(node, 10):
                print(f"Got: {result}")
                if result > 100:
                    break  # Can stop early
        """
        from ..results import StreamCollector
        
        collector = StreamCollector()
        stepper = self.stepper(start_node, *args, collector=collector, **kwargs)
        
        while True:
            rows = stepper.step()
            if not rows:
                break
            
            # Yield any new results
            while collector.has_pending():
                yield collector.next()
```

#### StreamCollector Implementation

```python
# Add to src/hyperway/results.py

from collections import deque


class StreamCollector(ResultCollector):
    """Collector that supports streaming results.
    
    Results are queued and can be consumed incrementally
    during execution.
    
    Example:
        collector = StreamCollector()
        stepper = g.stepper(node, 10, collector=collector)
        
        while stepper.step():
            while collector.has_pending():
                result = collector.next()
                print(result)
    """
    
    def __init__(self, unwrap: bool = True):
        self.unwrap = unwrap
        self.queue = deque()
    
    def add(self, node: Unit, akw: ArgsPack):
        """Add result to queue."""
        if self.unwrap:
            if akw.args:
                value = akw.args[0] if len(akw.args) == 1 else akw.args
            elif akw.kw:
                value = akw.kw
            else:
                value = None
        else:
            value = akw
        
        self.queue.append(value)
    
    def has_pending(self):
        """Check if results are available."""
        return len(self.queue) > 0
    
    def next(self, default=None):
        """Get next result from queue."""
        try:
            return self.queue.popleft()
        except IndexError:
            return default
    
    def reset(self):
        """Clear queue."""
        self.queue.clear()
```

#### Benefits

- ✅ Pythonic context manager pattern
- ✅ One-liner execution for simple cases
- ✅ Streaming support for incremental processing
- ✅ Can short-circuit execution
- ✅ Minimal boilerplate

#### Example Usage

```python
# Context manager - cleanest for simple cases
with g.execute(node, 10) as results:
    pass

print(results.first())  # 60
print(results.all())    # [60]

# Direct execution - even simpler
results = g.run(node, 10)
print(results)  # [60]

# Streaming - for incremental processing
for result in g.stream(node, 10):
    print(f"Got: {result}")
    if result > threshold:
        break  # Can stop early

# Advanced: Custom collector with context manager
collector = RichResultCollector()
with g.execute(node, 10, collector=collector) as results:
    pass

for result in results.results:
    print(f"{result.value} from {result.node.name}")
```

---

## Examples and Use Cases

### Use Case 1: Simple Single Result

**Scenario:** Linear graph with one endpoint, just want the final value.

```python
# Before (Current)
g.stepper_prepare(start_node, 10)
s = g.stepper()
while s.step():
    pass

for node, akw_tuple in s.stash.items():
    for akw in akw_tuple:
        result = akw.args[0]
        print(result)  # 60

# After Phase 1: Simple method
g.stepper_prepare(start_node, 10)
s = g.stepper()
while s.step():
    pass

result = s.get_result()
print(result)  # 60

# After Phase 3: One-liner
result = g.run(start_node, 10)[0]
print(result)  # 60
```

### Use Case 2: Multiple Results from Branching Graph

**Scenario:** Graph branches to multiple endpoints, want all results.

```python
# Graph structure:
#     -> handler_a (produces 42)
# split
#     -> handler_b (produces 100)

# Before (Current)
g.stepper_prepare(split, 10)
s = g.stepper()
while s.step():
    pass

results = []
for node, akw_tuple in s.stash.items():
    for akw in akw_tuple:
        results.append(akw.args[0])
print(results)  # [42, 100] (order not guaranteed)

# After Phase 1: Simple list
g.stepper_prepare(split, 10)
s = g.stepper()
while s.step():
    pass

results = s.get_results()
print(results)  # [42, 100]

# After Phase 3: One-liner
results = g.run(split, 10)
print(results)  # [42, 100]
```

### Use Case 3: Results Organized by Handler

**Scenario:** Need to distinguish which handler produced which result.

```python
# Before (Current) - complex manual grouping
g.stepper_prepare(split, 10)
s = g.stepper()
while s.step():
    pass

results_by_node = {}
for node, akw_tuple in s.stash.items():
    node_name = getattr(node, 'name', str(node))
    results_by_node[node_name] = []
    for akw in akw_tuple:
        results_by_node[node_name].append(akw.args[0])

print(results_by_node)  # {'handler_a': [42], 'handler_b': [100]}

# After Phase 1: Built-in method
g.stepper_prepare(split, 10)
s = g.stepper()
while s.step():
    pass

results = s.get_results_dict()
print(results)  # {'handler_a': [42], 'handler_b': [100]}

# After Phase 2: Collector
collector = DictCollector(key='name')
stepper = g.stepper(split, 10, collector=collector)
while stepper.step():
    pass

results = collector.results
print(results)  # {'handler_a': [42], 'handler_b': [100]}
```

### Use Case 4: Logging Results as They Arrive

**Scenario:** Want to monitor execution progress, log each result.

```python
# Before (Current) - must wait for completion
g.stepper_prepare(start, 10)
s = g.stepper()
while s.step():
    pass

for node, akw_tuple in s.stash.items():
    for akw in akw_tuple:
        print(f"Result: {akw.args[0]}")  # Only prints at end

# After Phase 2: Callback collector
def log_result(value, node):
    print(f"Result: {value} from {node.name}")

collector = CallbackCollector(on_result=log_result)
stepper = g.stepper(start, 10, collector=collector)
while stepper.step():
    pass  # Logs appear during execution

# After Phase 3: Streaming
for result in g.stream(start, 10):
    print(f"Result: {result}")  # Prints as results arrive
```

### Use Case 5: Early Termination

**Scenario:** Stop execution when target result found.

```python
# Before (Current) - cannot stop early
g.stepper_prepare(start, 10)
s = g.stepper()
while s.step():
    pass  # Must complete entire graph

# After Phase 3: Streaming with break
target = 42
for result in g.stream(start, 10):
    if result == target:
        print(f"Found target: {result}")
        break  # Stop execution early
```

### Use Case 6: Rich Context for Debugging

**Scenario:** Need execution context for debugging/auditing.

```python
# Before (Current) - no context available
g.stepper_prepare(start, 10)
s = g.stepper()
while s.step():
    pass

# Only have results, no context
for node, akw_tuple in s.stash.items():
    print(node)  # Opaque Unit object

# After Phase 2: Rich collector
collector = RichResultCollector()
stepper = g.stepper(start, 10, collector=collector)
while stepper.step():
    pass

for result in collector.results:
    print(f"Value: {result.value}")
    print(f"From: {result.node.name}")
    print(f"At: {result.timestamp}")
    print(f"Metadata: {result.metadata}")
```

### Use Case 7: Custom Result Processing

**Scenario:** Need custom processing (e.g., save to database).

```python
# After Phase 2: Custom collector
class DatabaseCollector(ResultCollector):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def add(self, node, akw):
        value = akw.args[0] if akw.args else None
        self.db.execute(
            "INSERT INTO results (node, value) VALUES (?, ?)",
            (node.name, value)
        )

collector = DatabaseCollector(db_conn)
stepper = g.stepper(start, 10, collector=collector)
while stepper.step():
    pass  # Results saved to database during execution
```

---

## Migration Path

### For Existing Code

All existing code continues to work without changes:

```python
# This still works exactly as before
g.stepper_prepare(node, 10)
s = g.stepper()
while s.step():
    pass

results = s.stash  # Still available
for node, akw_tuple in s.stash.items():
    for akw in akw_tuple:
        print(akw.args[0])
```

### Gradual Adoption

Users can adopt new APIs incrementally:

```python
# Step 1: Start using convenience methods
result = s.get_result()  # Instead of manual stash access

# Step 2: Try collectors for specific use cases
collector = ListCollector()
stepper = g.stepper(node, 10, collector=collector)

# Step 3: Adopt high-level APIs for new code
results = g.run(node, 10)
```

### Documentation Strategy

1. **Quick Start** - Show simplest APIs first (Phase 3)
2. **Common Patterns** - Document typical use cases with Phase 1 methods
3. **Advanced Usage** - Explain collectors and custom strategies (Phase 2)
4. **Migration Guide** - Help users transition from `stash`
5. **Deprecation Timeline** - Eventually mark `stash` as advanced/internal

---

## Implementation Checklist

### Phase 1 (Immediate)
- [ ] Add `get_result()` method to `StepperC`
- [ ] Add `get_results()` method to `StepperC`
- [ ] Add `get_results_dict()` method to `StepperC`
- [ ] Add `has_results()` method to `StepperC`
- [ ] Add `result_count()` method to `StepperC`
- [ ] Write unit tests for new methods
- [ ] Update documentation with examples
- [ ] Add to README Quick Example section

### Phase 2 (Next)
- [ ] Create `src/hyperway/results.py` module
- [ ] Implement `ResultCollector` base class
- [ ] Implement `ListCollector`
- [ ] Implement `DictCollector`
- [ ] Implement `CallbackCollector`
- [ ] Implement `RichResultCollector` with `Result` dataclass
- [ ] Implement `StreamCollector`
- [ ] Modify `StepperC.__init__` to accept `collector` parameter
- [ ] Modify `StepperC.end_branch` to notify collector
- [ ] Modify `Graph.stepper` to accept `collector` parameter
- [ ] Write unit tests for all collectors
- [ ] Write integration tests
- [ ] Document collector system
- [ ] Add examples to documentation

### Phase 3 (Future)
- [ ] Implement `ExecutionContext` class
- [ ] Add `Graph.execute()` method
- [ ] Add `Graph.run()` method
- [ ] Add `Graph.stream()` method
- [ ] Write unit tests for high-level APIs
- [ ] Write integration tests
- [ ] Update all documentation examples
- [ ] Create migration guide
- [ ] Update README with simplest patterns first

---

## Performance Considerations

### Phase 1 Impact
- Minimal: Just unwrapping existing stash data
- No execution overhead
- O(n) traversal of results (already in memory)

### Phase 2 Impact
- Minimal when no collector used (backwards compatible)
- Small overhead when collector used: one method call per result
- No memory overhead (collectors just organize data differently)
- Callback collectors may reduce memory (no accumulation)

### Phase 3 Impact
- Same as Phase 2 (uses collectors internally)
- Context manager adds ~microseconds overhead (negligible)
- Streaming may reduce memory for large result sets

### Optimization Opportunities
- Collectors could use generators internally
- Streaming can process results without full accumulation
- Custom collectors can implement memory-efficient strategies

---

## Open Questions

1. **Naming**: Are method names intuitive? (`get_result` vs `result`, `get_results` vs `results`)
2. **Default Unwrapping**: Should `unwrap=True` be default? (Proposed: yes, for ease of use)
3. **Collector API**: Is `add(node, akw)` the right signature? Should we pass more context?
4. **Result Class**: Should include execution path? (Memory vs information tradeoff)
5. **Streaming Semantics**: Should `g.stream()` consume results (remove from stash)?
6. **Type Hints**: Should we add comprehensive type hints in Phase 1 or wait?
7. **Async Support**: Future consideration for async graph execution?

---

## Conclusion

This proposal provides a clear path to significantly improve result access in Hyperway while maintaining complete backwards compatibility. The three-phase approach allows for incremental implementation and user adoption:

- **Phase 1** provides immediate UX wins with minimal code
- **Phase 2** enables advanced patterns for power users
- **Phase 3** delivers maximum simplicity for common cases

Each phase builds on the previous while standing alone as a valuable improvement. Users can adopt new patterns gradually without breaking existing code.

The result will be a more intuitive, Pythonic API that reduces friction for new users while preserving the power and flexibility that advanced users need.
