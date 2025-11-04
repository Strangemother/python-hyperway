# Knuckles

**Knuckles** are dynamic edge selection mechanisms that filter outgoing connections at execution time. They implement conditional graph traversal by allowing nodes to choose which edges to follow based on runtime state, data, or predicates.

In graph theory terms, a knuckle transforms a static directed graph into a dynamic one where edge traversal is determined by a function `f(v, data) → E' ⊆ E`, where `v` is a vertex and `E'` is a subset of its outgoing edges.

## Core Mechanism

When a node has multiple outgoing connections, the stepper's default behavior is to traverse all of them (parallel expansion). A knuckle intercepts this point and returns a filtered subset, enabling selective traversal.

```python
# The knuckle signature
def get_connections(self, graph, akw=None):
    # graph: the Graph instance
    # akw: ArgsPack with current values (or None)
    # returns: tuple of Connection objects to follow
    pass
```

Override `get_connections()` on your Unit subclass to implement custom traversal logic.

## Basic Implementation

A node that performs conditional routing based on data attributes:

```python
from hyperway.graph import Graph
from hyperway.nodes import Unit, as_unit
from hyperway.packer import argspack


class Router(Unit):
    """Route based on a key in the data."""
    
    def get_connections(self, graph, akw=None):
        # Retrieve all outgoing edges from this vertex
        connections = tuple(graph.get(self.id(), ()))
        
        # Default: return all edges (no filtering)
        if akw is None:
            return connections
        
        # Filter edges by name attribute matching 'route' key
        route = akw.get('route')
        if route is None:
            return connections
        
        filtered = tuple(c for c in connections if c.name == route)
        return filtered if filtered else ()


# Build the graph
g = Graph()

router = Router(lambda x: x)
handler_a = as_unit(lambda x: print(f"Handler A: {x}"))
handler_b = as_unit(lambda x: print(f"Handler B: {x}"))

g.add(router, handler_a, name='route_a')
g.add(router, handler_b, name='route_b')

# Execute: only handler_a is reached
g.stepper_prepare(router, argspack(10, route='route_a'))
s = g.stepper()
while s.step():
    pass
# Output: Handler A: 10
```

The connection named `'route_a'` is selected; all other edges are pruned from the traversal.

## Etymology

The term derives from the anatomical joint metaphor: a knuckle is a branch point in skeletal structure. In graph topology, a knuckle represents a vertex where execution diverges, and the knuckle function determines which branches (edges) to traverse.

The term is preferred over "conditional edge filter" or "dynamic edge selector" for brevity and memorability.

## Execution Model

The stepper invokes `get_connections()` during graph traversal to resolve the next edges:

1. Vertex executes and produces result data (`akw`)
2. Stepper queries the vertex for outgoing edges via `get_connections(graph, akw)`
3. Vertex evaluates `akw`, graph topology, internal state
4. Returns filtered tuple of Connection objects
5. Stepper traverses returned edges (or treats vertex as sink if empty)

The default `Unit.get_connections()` returns all outgoing edges (full expansion). Override this method to implement custom traversal policies.

This mechanism is similar to transition functions in automata theory, where `δ(q, σ) → Q'` maps a state `q` and input `σ` to a set of successor states `Q'`.

## Pattern: Edge Labeling and Selection

The most common pattern uses edge labels (connection names) for routing:

```python
class NamedRouter(Unit):
    def get_connections(self, graph, akw=None):
        connections = tuple(graph.get(self.id(), ()))
        if not akw:
            return connections
        
        target = akw.get('target')
        if not target:
            return connections
        
        return tuple(c for c in connections if c.name == target)
```

Nodes can embed routing metadata in their output:

```python
def process_data(data):
    if data > 100:
        return argspack(data, target='high_value')
    else:
        return argspack(data, target='normal')
```

The `target` attribute determines edge selection.

## Pattern: Predicate-Based Branching

Filter edges using value predicates:

```python
class Splitter(Unit):
    def get_connections(self, graph, akw=None):
        connections = tuple(graph.get(self.id(), ()))
        if not akw or not akw.args:
            return connections
        
        value = akw.args[0]
        
        # Route even values to 'even' edges, odd values to 'odd' edges
        target = 'even' if value % 2 == 0 else 'odd'
        return tuple(c for c in connections if c.name == target)
```

## Pattern: Stateful Knuckles

Knuckles can maintain internal state for deterministic scheduling, rate limiting, or circuit breaking. This allows implementation of stateful graph traversal policies:

```python
class RoundRobin(Unit):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.counter = 0
    
    def get_connections(self, graph, akw=None):
        connections = tuple(graph.get(self.id(), ()))
        if not connections:
            return ()
        
        # Select next edge using modulo rotation
        selected = connections[self.counter % len(connections)]
        self.counter += 1
        return (selected,)
```

Each invocation selects the next edge in cyclic order, implementing a round-robin load distribution policy.

## Pattern: Type-Based Routing

Apply arbitrary predicates including type checks, thresholds, or complex conditions:

```python
class TypeRouter(Unit):
    def get_connections(self, graph, akw=None):
        connections = tuple(graph.get(self.id(), ()))
        if not akw or not akw.args:
            return connections
        
        value = akw.args[0]
        value_type = type(value).__name__
        
        # Route based on runtime type
        return tuple(c for c in connections 
                     if c.name == value_type or c.name == 'default')
```

This enables polymorphic dispatch where edge selection depends on runtime type information.

## Pattern: Stochastic Edge Selection

For non-deterministic traversal, A/B testing, or Monte Carlo exploration:

```python
import random

class RandomSplit(Unit):
    def get_connections(self, graph, akw=None):
        connections = tuple(graph.get(self.id(), ()))
        if len(connections) <= 1:
            return connections
        
        # Weighted probabilistic split (80/20)
        if random.random() < 0.8:
            return (connections[0],)
        else:
            return (connections[1],)
```

## Empty Edge Sets

If `get_connections()` returns an empty tuple (or `None`), the stepper treats the vertex as a sink node and stashes the result:

```python
class ConditionalEnd(Unit):
    def get_connections(self, graph, akw=None):
        if akw and akw.get('stop'):
            return ()  # Terminate traversal
        
        # Continue with normal expansion
        return tuple(graph.get(self.id(), ()))
```

This enables dynamic determination of sink nodes based on runtime conditions.

## Advanced: Finite Automata Implementation

Knuckles enable implementation of finite automata and state machines. A vertex can:

- Maintain internal state (`self.state = ...`)
- Compute state transitions based on input (`akw`)
- Select outgoing edges corresponding to transitions
- Trigger side effects or event emissions

```python
class StateMachine(Unit):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.state = 'idle'
    
    def get_connections(self, graph, akw=None):
        connections = tuple(graph.get(self.id(), ()))
        
        if not akw:
            return connections
        
        event = akw.get('event')
        
        # Transition function: δ(state, event) → (state', edges)
        if self.state == 'idle' and event == 'start':
            self.state = 'running'
            return tuple(c for c in connections if c.name == 'on_start')
        
        elif self.state == 'running' and event == 'stop':
            self.state = 'idle'
            return tuple(c for c in connections if c.name == 'on_stop')
        
        # No valid transition (stay in current state)
        return ()
```

This implements a transition function similar to finite automata: `δ: Q × Σ → Q × E`, where `Q` is the state set, `Σ` is the input alphabet, and `E` is the edge set. Supports epsilon transitions (state changes without edge traversal), non-deterministic transitions, and event-driven control flow.

## Knuckles vs Wires

**Wires** are edge functions that transform values during traversal. **Knuckles** are vertex functions that select edges for traversal.

- Use wires for data transformation on edges (map operations)
- Use knuckles for edge selection at vertices (filter/routing operations)

These mechanisms compose:

```python
class Router(Unit):
    def get_connections(self, graph, akw=None):
        # Knuckle: select edges
        route = akw.get('route') if akw else None
        connections = tuple(graph.get(self.id(), ()))
        return tuple(c for c in connections if c.name == route)

# Wire: transform data during edge traversal
def scale_wire(value, *a, **kw):
    return argspack(value * 10, **kw)

router = Router(some_func)
g.add(router, handler, name='route_a', through=scale_wire)
```

The knuckle performs edge selection, the wire performs data transformation.

## Implementation Guidelines

**Simplicity.** Most knuckles filter by edge labels. Avoid unnecessary complexity.

**Return type.** Always return a tuple (or empty tuple). While `None` is supported, `()` is more explicit.

**Default behavior.** When filtering conditions are absent, return all edges. This maintains backward compatibility.

**Edge cases.** Handle missing connections, null `akw`, and empty data structures gracefully.

**Idempotence.** `get_connections()` may be invoked multiple times for the same vertex. Minimize or eliminate side effects.

**Performance.** For large graphs, avoid expensive operations in `get_connections()`. This method is on the hot path.

## Reference Implementations

See `workspace/` for working examples:

- **`edge-selection.py`** - Label-based routing implementation
- **`edge-selection-v1.py`** - Alternative implementation (retained for comparison)

Test coverage:

- **`tests/test_knuckles.py`** - Comprehensive pattern examples and edge cases

## Use Cases

Apply knuckles when:

- Multiple outgoing edges exist and runtime selection is required
- Routing depends on data attributes or runtime state
- Implementing finite automata, decision trees, or control flow graphs
- Conditional branching is needed without creating intermediate vertices
- Load balancing, A/B testing, circuit breaking, or adaptive routing is required

Avoid knuckles when:

- Data transformation is the goal (use wires for edge functions)
- All outgoing edges should always be traversed (default behavior)
- Logic complexity suggests a separate vertex would be clearer

## The Name

The term "knuckles" is deliberately informal while remaining technically grounded. It captures the branching topology more memorably than alternatives like "dynamic edge selector" or "conditional connection filter."

In practice:

*"Add a knuckle here to route by user type."*

vs.

*"Implement dynamic connection selection via Unit subclass method override."*

The former is preferred for conciseness and clarity.

---

Knuckles provide conditional graph traversal through vertex-level edge selection. Override `get_connections()` to implement custom routing logic, return the filtered edge set, and the stepper handles traversal.
