# AI agent guide for python-hyperway

This repository implements a small functional-execution engine on top of a graph. The core loop walks a graph of Unit (node) objects via Connection (edge) objects using a Stepper. Read this first to be productive:

- Source layout
  - `src/hyperway/graph/graph.py` and `src/hyperway/graph/base.py`: Graph storage and helpers. Graph is a thin defaultdict of connections keyed by edge id and node-a id.
  - `src/hyperway/edges.py`: Connection and PartialConnection implementations plus `make_edge`. A Connection binds A → [through?] → B and supports `pluck()` for A→(through)→B in one call.
  - `src/hyperway/nodes.py`: Unit (node) wrapper and helpers (`as_unit`, `as_units`, `is_unit`). Unit.process applies sentinel rules; Nodes.process is a raw pass-through.
  - `src/hyperway/stepper.py`: StepperC, the execution engine. `StepperC.call_one_*` drives A, [wire]→B, merging, and branch-end stashing.
  - `src/hyperway/packer.py`: `argspack`/`ArgsPack` for moving (args, kwargs) between nodes and wires.
  - `src/hyperway/writer.py` and `docs/*`: graphviz rendering and docs.
  - `src/hyperway/tools.py`: small factory/util functions used in examples and tests.

- Big-picture data flow
  - Build edges: `g.add(a, b, through=optional_wire)` or `g.connect(a, b, c, ...)` (chains pairs). Callables are wrapped via `as_unit(...)` automatically.
  - Execute: create a stepper and step:
    - `g.stepper_prepare(start_unit, *args, **kw)` then `s = g.stepper(); s.step()` repeatedly, or
    - For a single edge, `connection.pluck(*a, **kw)` runs A then [through] then B.
  - Stepper rows contain next-caller and an `ArgsPack`. Ends are stashed in `stepper.stash` (unless `stash_ends=False`).
  - Merge nodes: set `unit.merge_node=True` and `stepper.concat_aware=True` to combine multiple incoming rows into one call (see `row_concat`).

- Project conventions and patterns
  - Left-associative execution: edges run strictly A → [through] → B; no algebraic precedence (see README “Order of Operation”).
  - All inter-node values move via `ArgsPack`; wire functions must return `argspack(...)`.
  - Node uniqueness: `Unit(func)` objects are unique per wrap; reuse a specific Unit by pre-wrapping with `as_unit` and reusing that instance.
  - Sentinel handling: `Unit.process` treats a single positional arg equal to `unit.sentinal` as “no value” and strips it; use `as_unit(func, sentinal=None)` to suppress passing None to no-arg functions (see tests/test_sentinal.py).
  - `Nodes` subclass bypasses sentinel logic and forwards args as-is.

- Typical developer workflows
  - Tests: run fast with pytest
    - Quick run: `./quick_test.sh` (uses venv at `.venv`)
    - Or from repo root: `pytest -q` or `pytest -v --cov`
  - Examples and playground: `workspace/` contains many runnable examples and graphviz renders.
  - Docs: see `README.md` (rich overview) and `docs/` (`stepper.md`, `topology.md`). Rendering graphs requires `graphviz` (see `docs/graphviz-install.md`).

- Key APIs and examples
  - Build a connection and pluck
    - `from hyperway.tools import factory as f; from hyperway.edges import make_edge`
    - `c = make_edge(f.add_1, f.add_2)`; `assert c.pluck(1) == 4`
    - With wire transform: `c = make_edge(f.add_1, f.add_2, through=lambda v,*a,**kw: argspack(v*2, **kw))`
  - Graph and stepper
    - `from hyperway.graph import Graph`; `g = Graph()`
    - `chain = g.connect(f.add_10, f.add_20, f.add_30)`; `first = chain[0].a`
    - `g.stepper_prepare(first, 10)`; `s = g.stepper()`; `rows = s.step()`; continue stepping until rows empty; results appear in `s.stash`.
  - Merge-node example
    - `u = as_unit(print); u.merge_node = True`; `s = g.stepper(); s.concat_aware = True`

- Gotchas to keep in mind
  - Wire functions must return an `ArgsPack` via `argspack`; returning raw values will break downstream.
  - `Connection.__call__` runs only A; use `pluck()` to run A → [through] → B.
  - When there are no outgoing connections from a Unit, `StepperC.end_branch` stashes the result; `leaf()` on `Unit` handles this case.
  - Some modules print debug traces (e.g., resolve/connection calls). Keep outputs minimal in tests.

- Where to look when extending
  - New node behaviors: subclass `Unit` (see `Nodes`) and override `process`/`leaf` as needed.
  - Alternate graph strategies: extend `GraphBase` or composition around `Graph`.
  - Stepper policies: adjust `row_concat`, `concat_aware`, or replace `expand` via `set_global_expand`.

- Runbook
  - Install dev deps: ensure `pytest` available (declared in `pyproject.toml` as optional `dev`).
  - Run tests: `./quick_test.sh` or `pytest -q`.
  - Render graph images: ensure `graphviz` installed, then call `g.write("name", directory="renders", direction="LR")`.

Use the concrete patterns in `tests/` for style and integration expectations (e.g., `tests/test_wire_func.py`, `tests/test_stepper.py`, `tests/test_sentinal.py`, `tests/test_nodes.py`). Prefer adding small, focused tests that assert behavior via `pluck()` and `stepper` flows.

Run tests using the `./quick_test.sh` script to ensure all functionality remains intact.