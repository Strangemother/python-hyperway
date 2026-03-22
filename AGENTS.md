# Agents Instructions

The main developer documentation lives in the `docs/` directory. The following points summarise how to set up the environment, build tests, run checks, build docs. Additional examples exist within the `workspace/` directory. The primary `README.md` contains human-readable documentation about the project.

## Setting up the Development Environment

This is a standard Python package, using `pip` and `venv` for environment management. To set up the development environment, utilise the `pyproject.toml` file for dependency management.

For local source development, install in editable mode:

    pip install -e .

## Building and Running Tests

Tests are located in the `tests/` directory. You can run tests using `pytest`. Ensure you have all development dependencies installed. For quick testing, you can run `./quick_test.sh` from the root directory.

## Code Quality and Formatting

We use `pep8` for style checking. See [`.github/instructions/python.instructions.md`](.github/instructions/python.instructions.md) for the full coding conventions.

---

## Known Pitfalls and Discoveries

The following issues were discovered whilst building the `workspace/ship-*.py` and `workspace/circuit-demo.py` example scripts. These are essential to understand before writing new code against hyperway.

### 1. Unit Uniqueness (Critical)

Every call to `g.add(func, ...)` wraps `func` with `as_unit()` internally, creating a **new** `Unit` instance each time. Two `g.add()` calls with the same callable produce two _different_ Unit objects with different IDs. The graph stores connections keyed by Unit ID, so:

```python
# BROKEN — creates three separate Units for reactor.generate
g.add(reactor.generate, shield.receive_power, through=power_cable)
g.add(reactor.generate, weapons.receive_power, through=heavy_cable)
g.stepper_prepare(reactor.generate, 1.0)  # Yet another Unit — no connections found
```

The stepper resolves connections by looking up `unit.id()` in the graph. If the Unit passed to `stepper_prepare` is not the _same instance_ stored by `g.add()`, fan-out will silently fail — the reactor fires but no downstream consumers receive power.

**Fix: pre-wrap with `as_unit()` and reuse the instance.**

```python
from hyperway.nodes import as_unit

reactor_unit = as_unit(reactor.generate)

g.add(reactor_unit, shield.receive_power, through=power_cable)
g.add(reactor_unit, weapons.receive_power, through=heavy_cable)
g.stepper_prepare(reactor_unit, 1.0)  # Same instance — connections resolve correctly
```

This applies to any callable used as the A-side of multiple edges: plain functions, bound methods, lambdas. If a node appears in more than one `g.add()` call, always pre-wrap it.

See: [`src/hyperway/nodes.py`](src/hyperway/nodes.py) — `as_unit()`, `Unit`, and ID generation.

### 2. Stepper: `stepper_prepare` vs `stepper_prepare_many`

There are two ways to initialise a stepper:

| Method | Use case | How it works |
|---|---|---|
| `g.stepper_prepare(node, *args)` | Single entry point | Stores start node + args; `step()` calls `expand()` on first invocation |
| `g.stepper_prepare_many((nodeA, val), (nodeB, val), ...)` | Multiple entry points | Pre-builds rows directly; `step()` skips expansion entirely |

`stepper_prepare_many` is required for merge-node patterns (e.g. two inputs feeding one gate) and multi-source graphs. The rows it creates are stored in `graph._stepper_rows` and passed directly to `StepperC.__init__`, bypassing the `start_nodes` check in `step()`.

See: [`src/hyperway/graph/graph.py`](src/hyperway/graph/graph.py) — `stepper_prepare`, `stepper_prepare_many`, `stepper`.
See: [`src/hyperway/stepper.py`](src/hyperway/stepper.py) — `step()` method, row initialisation logic.

### 3. Stash Keys Are PartialConnections, Not Functions

When a branch ends (no outgoing connections), `StepperC.end_branch` stores the result in `stepper.stash`. The key is the **`PartialConnection`** object that delivered the value — _not_ the original function or Unit.

```python
# BROKEN — function reference is not a stash key
result = s.stash.get(my_output_func)  # Returns None

# CORRECT — iterate the stash
for key, value_tuple in s.stash.items():
    if value_tuple:
        first_argpack = value_tuple[0]
        result = first_argpack.args[0]
```

Alternatively, use `s.get_results()` for a flat list of all stashed values.

See: [`src/hyperway/stepper.py`](src/hyperway/stepper.py) — `end_branch`, `get_results`, `flush`, `peek`.

### 4. Falsy Values in Results

When extracting boolean or numeric results from the stash, do not use truthiness checks:

```python
# BROKEN — treats False and 0 as missing
display = int(out) if out else '?'

# CORRECT — explicit None check
display = int(out) if out is not None else '?'
```

This matters for logic gate circuits where `False` / `0` is a valid output.

### 5. Wire Functions Must Return `argspack`

Every wire function (the `through=` parameter) **must** return an `argspack(...)`. Returning a raw value will break downstream processing:

```python
# BROKEN
def my_cable(watts, *a, **kw):
    return watts * 0.9

# CORRECT
def my_cable(watts, *a, **kw):
    return argspack(watts * 0.9, **kw)
```

Pass `**kw` through to preserve any kwargs bubbling through the graph.

See: [`docs/kwargs-bubbling.md`](docs/kwargs-bubbling.md).

### 6. Distributed vs Unified Initiation

The default stepper mode is `INITIATE_DISTRIBUTED`: when a start node has multiple outgoing connections, the node is called **once per connection**. This means a reactor feeding three subsystems generates power three times per tick.

For "call once, distribute result to all" semantics, use `INITIATE_UNIFIED`:

```python
g.stepper_prepare(reactor_unit, 1.0, initiate_mode=INITIATE_UNIFIED)
```

In many simulation scenarios, distributed mode is acceptable (each connection gets a fresh call). Be aware of side effects — e.g. fuel is consumed per call, not per tick.

See: [`src/hyperway/stepper.py`](src/hyperway/stepper.py) — `expand_distributed`, `expand_unified`, `INITIATE_DISTRIBUTED`, `INITIATE_UNIFIED`.

### 7. Merge Nodes Require Both Flags

For fan-in (multiple sources feeding one node), **both** flags must be set:

```python
bus_node = as_unit(power_bus)
bus_node.merge_node = True    # On the node

s = g.stepper()
s.concat_aware = True          # On the stepper
```

Missing either flag causes the merge node to be called separately for each incoming value instead of receiving them combined.

See: [`docs/stepper.md`](docs/stepper.md) — merge node documentation.
See: [`workspace/circuit-demo.py`](workspace/circuit-demo.py) — working merge-node example with logic gates.

### 8. Library Debug Output

The hyperway library prints debug traces during execution:
- `Calling through ...` — from [`src/hyperway/edges.py`](src/hyperway/edges.py) when a wire function fires
- `C(0) "..."` — from [`src/hyperway/edges.py`](src/hyperway/edges.py) when a node has no outgoing connections

These are informational and not errors. For clean output in simulations, suppress stdout during stepping:

```python
import io, contextlib

with contextlib.redirect_stdout(io.StringIO()):
    while True:
        rows = s.step()
        if not rows:
            break
```

### 9. Stepper Re-use Across Ticks

To run a graph repeatedly (e.g. a game loop), call `stepper_prepare` and create a fresh `stepper()` each tick. The stepper is stateful and should not be reused across ticks:

```python
for tick in range(total_ticks):
    g.stepper_prepare(reactor_unit)
    s = g.stepper()
    while True:
        rows = s.step()
        if not rows:
            break
```

See: [`workspace/ship-game-loop.py`](workspace/ship-game-loop.py) — tick-based simulation pattern.

### 10. `pluck()` vs Stepper for Simple Edges

For a single A → [wire] → B connection, `pluck()` is simpler than a full stepper:

```python
conn = make_edge(reactor.generate, shield.receive_power, through=power_cable)
result = conn.pluck(1.0)  # Runs A → wire → B in one call
```

Use the stepper when you need fan-out, merge nodes, or multi-step graph traversal.

See: [`src/hyperway/edges.py`](src/hyperway/edges.py) — `Connection.pluck`.

---

## Reference Examples

| Script | Demonstrates |
|---|---|
| [`workspace/circuit-demo.py`](workspace/circuit-demo.py) | Merge nodes, `stepper_prepare_many`, stash extraction, truth tables |
| [`workspace/ship-components.py`](workspace/ship-components.py) | Basic wiring, `pluck()`, fan-out with `as_unit`, cable swapping |
| [`workspace/ship-power-bus.py`](workspace/ship-power-bus.py) | Merge-node power bus, fan-out distribution, low-power scenarios |
| [`workspace/ship-damage.py`](workspace/ship-damage.py) | Runtime reconfiguration — rebuilding edges with different wire functions |
| [`workspace/ship-game-loop.py`](workspace/ship-game-loop.py) | Tick-based simulation, stepper re-use, suppressing debug output |

## Documentation Links

- [`README.md`](README.md) — Project overview, order of operation, graph concepts
- [`docs/stepper.md`](docs/stepper.md) — Stepper execution model
- [`docs/topology.md`](docs/topology.md) — Graph topology patterns
- [`docs/sentinal.md`](docs/sentinal.md) — Sentinel handling in Unit.process
- [`docs/kwargs-bubbling.md`](docs/kwargs-bubbling.md) — How kwargs flow through wire functions
- [`docs/spaceship-operating-framework.md`](docs/spaceship-operating-framework.md) — Spaceship OS research article
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — Full AI agent guide with API examples
