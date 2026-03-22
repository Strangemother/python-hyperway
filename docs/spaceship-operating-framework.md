# Hyperway as a Spaceship Operating Framework

_A discussion on using graph-based functional execution for hardware simulation, power distribution, and data routing in a Python game engine._

---

## The Premise

Consider a spaceship. Not the sci-fi kind with magical warp drives that just work because the plot demands it, but the engineering kind — where a reactor connects to a power bus, the power bus feeds shields and weapons through actual cables, and if someone cuts the wrong wire, the life support goes down.

Now consider building that in Python. You need an execution model where:

- Hardware components are independent units of logic
- Cables carry power and data between them
- The whole system ticks forward in lockstep
- Components can be connected, disconnected, and rerouted at runtime
- Multiple signals merge at junction points (a power bus, a sensor array)

This is, fundamentally, a graph problem. Components are nodes, cables are edges, and each game tick walks the graph to propagate signals. Hyperway was built for exactly this pattern.


## Why Graphs?

A spaceship's internal wiring is already a graph. Engineers draw circuit diagrams, plumbing schematics, and data bus architectures as boxes connected by lines. The mental model is there before any code is written.

Traditional approaches to modelling this in a game engine tend to fall into one of two camps:

**The event bus** — Components publish and subscribe to events. This works until you need to reason about signal ordering, fan-out behaviour, or cable-specific transformations. An event bus is structureless; there's no concept of "which wire" a signal travelled down.

**The entity-component system** — Popular in game engines, but ECS is optimised for querying components by type, not for expressing directional data flow between specific hardware units. You end up bolting on a routing layer anyway.

A graph-based execution model sidesteps both problems. The wiring _is_ the program. Each connection knows its source, destination, and optionally a transformation function (signal degradation, voltage conversion, encryption). The execution engine walks the graph one tick at a time, processing every signal path in parallel.


## Mapping Ship Systems to Hyperway

The translation from spaceship hardware to Hyperway primitives is nearly one-to-one:

| Ship Concept | Hyperway Primitive | Role |
|---|---|---|
| Hardware component | `Unit` (node) | A callable that processes inputs and produces outputs |
| Cable / wire | `Connection` (edge) | Binds two components together |
| Signal conditioning | Wire function (`through`) | Transforms data in transit — loss, conversion, filtering |
| Power bus / junction | Merge node | Combines multiple incoming signals into one call |
| Ship computer | `Stepper` | Walks the graph each tick, propagating all signals |
| Ship wiring diagram | `Graph` | A dictionary of all connections |

### Components as Nodes

A ship component is a Python class with methods that accept input and return output. Instance methods work directly as nodes, so each component retains its own state:

```python
from hyperway.graph import Graph
from hyperway.nodes import as_unit

class Reactor:
    def __init__(self, max_output=100):
        self.max_output = max_output
        self.efficiency = 1.0
        self.fuel = 1000

    def generate(self, throttle=1.0):
        """Generate power based on throttle setting."""
        if self.fuel <= 0:
            return 0
        self.fuel -= throttle * 0.1
        return self.max_output * throttle * self.efficiency


class Shield:
    def __init__(self):
        self.charge = 0
        self.max_charge = 100

    def receive_power(self, watts=0):
        """Absorb incoming power to charge shields."""
        self.charge = min(self.max_charge, self.charge + watts * 0.1)
        return self.charge
```

These are plain Python classes. No framework inheritance, no decorator magic, no registration step. The graph doesn't care what your components look like internally — it only cares that they're callable and return a value.

### Cables as Connections with Wire Functions

The real power (pun intended) is in wire functions. A wire function sits between two nodes on a connection and transforms the signal in transit. This is where cable physics live:

```python
from hyperway.packer import argspack

def power_cable(watts, *a, **kw):
    """A cable with 10% power loss."""
    return argspack(watts * 0.9, **kw)

def damaged_cable(watts, *a, **kw):
    """A damaged cable — loss and intermittent faults."""
    import random
    if random.random() < 0.15:  # 15% chance of dropout
        return argspack(0, **kw)
    return argspack(watts * 0.6, **kw)

def data_bus(payload, *a, **kw):
    """A data cable that adds transit metadata."""
    return argspack(payload, bus='main', **kw)
```

Wire functions must return an `ArgsPack` via `argspack()`. This is the contract. In exchange, you get a clean separation: the reactor doesn't know about cable losses, and the shield doesn't care how the power arrived. The cable is responsible for its own physics.

```python
reactor = Reactor()
shield = Shield()

g = Graph(tuple)
g.add(reactor.generate, shield.receive_power, through=power_cable)
```

That single line says: "connect the reactor's output to the shield's input, through a cable with 10% loss". Swap `power_cable` for `damaged_cable` and the shield starts receiving less power — no changes to either component.


### Power Buses and Merge Nodes

A power bus is a junction where multiple sources feed a single consumer, or one source feeds many consumers. Hyperway handles both:

**Fan-out** (one source, many consumers) is automatic — add multiple connections from the same node:

```python
g.add(reactor.generate, shield.receive_power, through=power_cable)
g.add(reactor.generate, weapons.receive_power, through=power_cable)
g.add(reactor.generate, life_support.receive_power, through=power_cable)
```

**Fan-in** (many sources, one consumer) uses merge nodes:

```python
from hyperway.nodes import as_unit

# The power bus combines inputs from two reactors
bus = as_unit(power_bus_combiner)
bus.merge_node = True  # Accept multiple inputs

g.add(reactor_a.generate, bus)
g.add(reactor_b.generate, bus)
g.add(bus, shield.receive_power)
```

With `concat_aware=True` on the stepper, the bus node receives all incoming values in a single call. This is the natural model for any junction, mixer, or aggregation point on the ship.


## The Game Loop

The stepper is the ship's computer. Each tick of the game loop calls `stepper.step()`, which propagates all signals through the graph simultaneously:

```python
g.stepper_prepare(reactor_unit, throttle=0.8)
stepper = g.stepper()

# In your game loop:
def tick():
    rows = stepper.step()
    if not rows:
        # All signals have reached their endpoints this tick
        pass
```

For a real game, you'd likely step multiple times per tick (once per "layer" of the graph) until the signals reach the leaf nodes. The stepper handles branching, merging, and stashing of terminal results automatically.

The streaming API is also worth considering for real-time monitoring:

```python
# React to results as they arrive
for result in stepper.stream():
    update_hud(result)
```


## Runtime Reconfiguration

Ships get damaged. Cables get cut. Systems get rerouted. Because the `Graph` is a dictionary of connections, reconfiguration is straightforward:

```python
# Damage: remove a connection
# (Rebuild the graph without the damaged cable)

# Reroute: add a new connection at runtime
g.add(backup_reactor.generate, shield.receive_power, through=emergency_cable)

# Hot-swap: replace a wire function
# (Reconnect with a different through function)
```

This maps to real gameplay scenarios:
- **Battle damage** removes connections or degrades wire functions
- **Repair** restores them
- **Power rerouting** adds temporary connections
- **Upgrades** swap wire functions for more efficient ones


## Scalability Considerations

Hyperway walks the full graph on each step. For a ship with 20-50 hardware components and maybe 100 connections, this is not a concern — the stepper processes hundreds of nodes in milliseconds.

If the design scales to hundreds of components with complex fan-out, there are a few strategies:

1. **Subsystem graphs** — Run separate graphs for power, data, and propulsion, ticking them independently
2. **Conditional edges** — Only activate connections when relevant (see the condition support in the framework)
3. **Tick budgeting** — Not every system needs to update every frame; sensors might tick at 10Hz while power distribution runs at 60Hz

The existing `bench_stepper_expand.py` benchmarks in the workspace suggest the core stepping loop is already performance-conscious.


## What Hyperway Gives You for Free

Beyond the basic graph execution, several built-in features map directly to ship simulation needs:

**Kwargs bubbling** — Metadata can flow through the graph without polluting function signatures. A signal can carry `signal_type='power'`, `priority='critical'`, or `source='reactor_a'` through the ArgsPack kwargs, and wire functions can read, modify, or forward this metadata.

**Sentinel handling** — Nodes that receive no input (e.g., a sensor with no signal) are handled gracefully through the sentinel system, rather than crashing with missing arguments.

**Graph visualisation** — With graphviz installed, `g.write('ship_systems')` renders the entire wiring diagram. This is genuinely useful for debugging a complex ship layout.

**Stateful instance methods** — As shown above, class instance methods work as nodes. Each component maintains its own state across ticks. No global state required.


## A Circuit Example

To make this concrete, the `workspace/circuit-demo.py` demonstrates a multi-gate logic circuit using Hyperway. It builds an `OR(AND(A,C), NOT(B))` circuit with merge nodes, multiple entry points, and runs a full truth table:

```
A ──→ [AND] ──┐
               ├──→ [OR] ──→ Output
B ──→ [NOT] ──┘
```

The pattern — define gate functions, connect them as a graph with merge nodes, prepare multiple entry points with `stepper_prepare_many`, and step — translates directly to ship hardware. Replace the gates with components, and you have a subsystem.


## Open Questions

A few areas that will need exploration as the project develops:

**Bidirectional signals** — Hyperway connections are directional (A to B). Some ship systems need feedback: "shields full, stop charging" or "engine overheating, reduce power". This can be modelled with explicit return edges, or potentially through the planned fiber connection system described in the project's research notes — lightweight side-channels that allow nodes to influence each other without being on the main execution path.

**Tick ordering** — When multiple signals converge at a merge node, they must all arrive before the node executes. The `concat_aware` stepper mode handles this, but complex graphs may need careful attention to layer depth to ensure signals arrive in the right order.

**Data vs. power typing** — Currently, all signals travel as generic `ArgsPack` values. For a ship, it may be useful to distinguish between power signals (watts), data signals (sensor readings), and control signals (commands). This could be handled through kwargs metadata, typed wrapper objects, or potentially a lightweight protocol on top of ArgsPack.


## Conclusion

Hyperway's graph-based execution model maps naturally to the problem of simulating a spaceship's internal systems. Components are nodes, cables are connections with wire functions, and the stepper ticks the whole system forward each frame. The framework handles fan-out, fan-in via merge nodes, runtime reconfiguration, and metadata propagation out of the box.

The core abstractions — `Unit`, `Connection`, `Graph`, `Stepper` — are thin enough to not fight your domain model, but structured enough to handle the inherent complexity of interconnected hardware simulation. It's a graph library that happens to solve the wiring problem, because wiring _is_ a graph problem.

For developers exploring similar domains — hardware simulation, circuit modelling, data pipeline orchestration, or any system where "things connected by wires" is the mental model — Hyperway offers a lightweight, dependency-free foundation to build on.
