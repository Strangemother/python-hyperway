## Knuckles and Connection Decisions

> A knuckle is a connection selection mechanism that filters available edges at execution time. It transforms static graph topology into dynamic routing based on runtime state, values, or conditions.

### Core Concept

When a `Unit` has multiple outgoing connections, the stepper normally follows all of them. A knuckle intercepts this point and returns a filtered subset:

```python
# Pseudocode
def select_connections(connections, stepper, akw):
    # connections: tuple of available Connection objects
    # stepper: StepperC instance (for state access)
    # akw: ArgsPack with current values
    return filtered_subset_of_connections
```

### Implementation Approaches

**1. Method Override** - Subclass `Unit` and override `select_connections()`:

```python
class ConditionalUnit(Unit):
    def select_connections(self, connections, stepper, akw):
        if condition_met(akw):
            return connections  # follow all
        return connections[:1]  # follow only first
```

**2. Pluggable Knuckle** - Attach a callable to `unit.knuckle`:

```python
unit = as_unit(func)
unit.knuckle = lambda conns, s, akw: filter_logic(conns, akw)
```

The `Unit.select_connections()` method checks for an attached knuckle first, then falls back to default behavior (return all connections).

### Integration Point

The stepper invokes knuckle logic in `call_one_unit()` after resolving available connections but before iteration:

```python
# Pseudocode in StepperC.call_one_unit
connections = get_connections(graph, unit)
selected = unit.select_connections(connections, stepper, akw)
if not selected:
    return unit.leaf(...)  # treat as end-node
for conn in selected:
    # execute connection...
```

### Use Cases

- **Conditional branching**: Route based on value thresholds, types, or predicates
- **State machine transitions**: Implement NFA/epsilon transitions by selecting connections without consuming input
- **Round-robin distribution**: Stateful knuckles can track invocation count and alternate paths
- **Circuit breaking**: Dynamically disable connections based on errors or stepper state
- **A/B testing**: Probabilistic routing between connection sets

### Event Emission and State Machines

Knuckles enable independent state machine behavior:

- A knuckle can emit events to external observers when selecting connections
- Epsilon transitions occur when `akw` values don't change but connection selection does
- Non-deterministic routing happens when multiple valid connections exist and selection varies per invocation
- State machines can track history via `stepper.stash` or custom knuckle state

# Example

An example of a knuckle selecting connections given their name and a key in `akw`:

```python
def name_based_knuckle(connections, stepper, akw):
    key = akw.get('route_key')
    return [conn for conn in connections if conn.name == key]

unit = as_unit(some_function)
unit.knuckle = name_based_knuckle


# 4 connections, two called dave:
g = Graph()

for name in ['alice', 'bob', 'dave', 'dave']:
    g.connect(unit, another_unit, name=name)
stepper = StepperC(g)

akw1 = ArgsPack(route_key='dave')
selected_conns = unit.select_connections(g.get_connections(unit), stepper, akw1)
assert len(selected_conns) == 2  # both 'dave' connections selected
```

```python
akw2 = ArgsPack(route_key='alice')
selected_conns = unit.select_connections(g.get_connections(unit), stepper, akw2)
assert len(selected_conns) == 1  # only 'alice' connection selected
```

## Value Splitting Knuckles

A knuckle can perform value splitting. Each connection can receive a modified `ArgsPack`:

```python
def splitting_knuckle(connections, stepper, akw):
    result = []
    for conn in connections:
        modified_akw = akw.copy()
        modified_akw['selected'] = conn.name
        result.append((conn, modified_akw))
    return result

unit.knuckle = splitting_knuckle
```

In an example where the value is numerical, the knuckle can provide each edge with a divided value:

```python
def dividing_knuckle(connections, stepper, akw):
    value = akw.get('value', 1)
    num_conns = len(connections)
    for conn in connections:
        modified_akw = akw.copy()
        modified_akw['value'] = value / num_conns
        yield (conn, modified_akw)

unit.knuckle = dividing_knuckle
```