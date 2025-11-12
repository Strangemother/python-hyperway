
<div align="center">

<br>

![hyperway logo](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/logo-v2.png)

<br>

[![Upload Python Package](https://github.com/Strangemother/python-hyperway/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Strangemother/python-hyperway/actions/workflows/python-publish.yml)
[![PyPI](https://img.shields.io/pypi/v/hyperway?label=hyperway)](https://pypi.org/project/hyperway/)
![License](https://img.shields.io/pypi/l/hyperway)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/hyperway)](https://pypi.org/project/hyperway/)
[![Sonar Coverage](https://img.shields.io/sonar/coverage/Strangemother_python-hyperway?server=https%3A%2F%2Fsonarcloud.io)](https://sonarcloud.io/summary/new_code?id=Strangemother_python-hyperway)

# Hyperway

A Python graph based functional execution library, with a unique API.

</div>

+ [Graph](#graph)
+ [Stepper](#-stepper)
+ [Units (Nodes)](#units-nodes) | [Functions](#functions)
+ [Connections (Edges)](#connections-edges) | [Wire Functions](#wire-function)
+ [Reference Links](#areas-of-interest)

Hyperway is a graph based functional execution library, allowing you to connect functions arbitrarily through a unique API. Mimic a large range of programming paradigms such as procedural, parallel, or aspect-oriented-programming. Build B-trees or decision trees, circuitry or logic gates; all with a simple _wiring_ methodology.



## 📦 Install

Hyperway has no enforced dependencies. 

Install via pip:

```bash
pip install hyperway
```

If you want to render graphs, ensure [graphviz](https://graphviz.org/) is installed. This can be done through your own methods, or by installing the optional dependency:

```bash
pip install hyperway[graphviz]
```

## 🚀 Quick Example

For a quick example of the important parts, let's connect some functions and run the chain:

```python
import hyperway
from hyperway.tools import factory as f

# Store
g = hyperway.Graph()

# Connect
first_connection = g.add(f.add_10, f.add_20)
# More connections
many_connections = g.connect(f.add_30, f.add_1, f.add_2, f.add_3)
# Cross connect
compound_connection = g.add(many_connections[1].b, f.add_3)

# Prepare to run
stepper = g.stepper(first_connection.a, 10)

# Run a step
concurrent_row = stepper.step()
```

Render this graph (if [graphviz](https://graphviz.org/) is installed):

```python
g.write('intro-example', directory='renders', direction='LR')
```

![connection diagram](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/intro-example.gv.png)


That's it! You're a graph engineer.

> [!NOTE]
> The stepper yields rows of `(Unit, ArgsPack)` tuples representing the next functions to execute.
> Continue calling `step()` until no rows remain. Access results easily with `stepper.get_result()` or `stepper.get_results()`.




# Getting Started

Hyperway aims to simplify graph based execution chains, allowing a developer to use functional graphs without managing the connections.

> [!TIP]
> **TL;DR:** The `Unit` (or node) is a function connected to other nodes through `Connections`. The `Stepper` walks the `Graph` of all connections.

### Glossary

The Hyperway API aims to simplify standard graph-theory terminology, by providing more intuitive names for common graph components. Developers and mathematicians can extend the base library with preferred terms, without changing the core functionality:

```python
class Vertex(Unit): 
    """Alias for Unit (Node)"""
    pass
```

Hyperway components, and their conventional siblings:

| Hyperway | Graph Theory | Description |
| --- | --- | --- |
| `Graph` | Graph, or Tree | A flat dictionary to hold all connections |
| `Unit` | Node, Point, or Vertex | A function on a graph, bound through edges |
| `Connection` | Edge, link, or Line | A connection between Units |
| `Stepper` | Walker, or Agent | A graph walking tool |


## Graph

The `Graph` is a fancy `defaultdict` of tuples, used to store connections:

```python
import hyperway

g = hyperway.Graph()
```

There are a few convenience methods, such as `add()` and `connect()`, but fundamentally it's a dictionary of connections.

All Connections are stored within a single `Graph` instance. We can consider the graph as a dictionary register of all associated connections.

```python
from hyperway.graph import Graph, add
from hyperway.nodes import as_units
from hyperway.tools import factory as f

g = Graph()
unit_a, unit_b = as_units(f.add_2, f.mul_2)

connection = add(g, unit_a, unit_b)
```

Under the hood, The graph is just a `defaultdict` and doesn't do much.

## Connections (Edges)

A `Connection` binds two functions (or `Unit` objects) together. It represents an edge between two nodes.

+ [Create](#create)
+ [Run](#run-a-connection)
+ [Pluck](#plucking)
+ [Wire Function](#wire-function)
+ [Self Reference](#self-reference)


A connection needs a minimum of two nodes:

![connection diagram of two nodes with an optional wire function](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/connection.png)

```python
from hyperway.edges import make_edge

c = make_edge(f.add_1, f.add_2)
# <Connection>
```

### Create

We can create a connection in two ways:

#### Hyperway

The `Graph` has an `add()` method to create a connection between two functions:

```python
import hyperway
from hyperway.tools import factory as f

g = hyperway.Graph()

connection = g.add(f.add_1, f.add_2)
# <Connection>
```

#### Functional

Alternatively we can use the `make_edge` function directly (without a graph):

```python
from hyperway.edges import make_edge
from hyperway.tools import factory as f
c = make_edge(f.add_1, f.add_2)
# <Connection>
```

### Run a Connection

We can _run_ a connection, calling the chain of two nodes. Generally a `Connection` isn't used outside a graph unless we're playing with it.

> [!IMPORTANT]
> A `Connection` has two processing steps due to a potential _wire_ function. Consider using `pluck()` to run both steps.

A standard call to a connection will run node `a` (the left side):

```python
# connection = make_edge(f.add_1, f.add_2)
>>> value_part_a = connection(1) # call A-side `add_1`
2.0
```

Then process the second part `b` (providing the value from the first call):

```python
>>> connection.process(value_part_a) # call B-side `add_2`
4.0
```

Alternatively use the `pluck()` method.

### Plucking

We can "pluck" a connection (like plucking a string) to run the functions with any arguments:

```python
from hyperway.tools import factory as f
from hyperway.edges import make_edge

c = make_edge(f.add_1, f.add_2)
# Run side _a_ (`add_1`) and _b_ (`add_2`) with our input value.

c.pluck(1)    # 4.0 == 1 + 1 + 2
c.pluck(10)   # 13.0 == 10 + 1 + 2
```

The `pluck()` executes both nodes and the optional wire function, in the expected order. Fundamentally a connection is self-contained and doesn't require a parent graph.


### Wire Function

An optional wire function exists between two nodes

![connection diagram of two nodes with a wire function](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/connection-with-wire.png)


The [Connection](#connections-edges) can have a function existing between its connected [Units](#units-nodes), allowing the alteration of the data through transit (whilst running through a connection):


```python
from hyperway.tools import factory as f
from hyperway.edges import make_edge, wire

c = make_edge(f.add_1, f.add_2, through=wire(f.mul_2))
# <Connection(Unit(func=P_add_1.0), Unit(func=P_add_2.0), through="P_mul_2.0" name=None)>
```

When using the connection side A (the `f.add_1` function), the wire function `wire(f.mul_2)` can inspect the values as they move to `f.add_2`.

It's important to note Hyperway is _[left-associative](#order-of-operation)_. The order of operation computes linearly:

```python
assert c.pluck(1) == 6   # (1 + 1) * 2 + 2 == 6
assert c.pluck(10) == 24 # (10 + 1) * 2 + 2 == 24
```

---

#### Why use a wire function?

It's easy to argue a wire function is a _node_, and you can implement the wire function without this connection tap.

+ Wire functions are optional: node to node connections are inherently not optional.
+ Removing a wire function does not remove the edge: Edges are persistent to the graph
+ Wire functions may be inert (e.g. just logging); Nodes cannot be inert as they must be bound to edges.

Fundamentally a wire function exists for topological clarity and may be ignored.

---

`make_edge` can accept the wire function. It receives the concurrent values transmitting through the attached edge:

```python
from hyperway.edges import make_edge
from hyperway.packer import argspack

import hyperway.tools as t
f = t.factory

def doubler(v, *a, **kw):
    # The wire function `through` _doubles_ the given number.
    # response with an argpack.
    return argspack(v * 2, **kw)


c = make_edge(f.add_1, f.add_2, through=doubler)
# <Connection(Unit(func=P_add_1.0), Unit(func=P_add_2.0), name=None)>

c.pluck(1)  # 6.0
c.pluck(2)  # 8.0
c.pluck(3)  # 10.0
```

> [!IMPORTANT]
> Wire functions **must** return an `ArgsPack` via `argspack()`. Returning raw values will break the execution chain.
> See [Extras](#extras) for `argspack` details.


The wire function is the reason for a two-step process when executing connections:

```python
# Call Node A: (+ 1)
c(4)
5.0

# Call Wire + B: (double then + 2)
c.process(5.0)
12.0
```

Or a single `pluck()`:

```python
c.pluck(4)
12.0
```

#### Self Reference

A connection `A -> B` may be the same node, performing a _loop_ or self-referencing node connection.

![self referencing connection](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/self-reference.png)


We can use the `as_unit` function, and reference the same unit on the graph:

```python
# pre-define the graph node wrapper
u = as_unit(f.add_2)
# Build an loop edge
e = make_edge(u, u)

g = Graph()
g.add_edge(e)

# Setup the start from the unit (side A)
g.stepper(u, 1)

# Call the stepper forever.
g.step()
g.step()
...
# 3, 5, 7, 9, 11, ...
```


## Functions

A function is our working code. We can borrow operator functions from the tools:

```python
from hyperway.tools import factory as f
add_10 = f.add_10
# functools.partial(<built-in function add>, 10.0)
add_10(1)
# 11.0
add_10(14)
# 24.0
```


## Units (Nodes)


The `Unit` (or node) is a function connected to other nodes through a `Connection`. A `Unit` is a wrapper for any python function. Everything in the graph (and in a Connection) is a `Unit`.


When we create a new connection, it automatically wraps the given functions as `Unit` types:

```python
c = make_edge(f.mul_3, f.add_4)
c.a
# <Unit(func=P_mul_3.0)>
c.b
# <Unit(func=P_add_4.0)>
```

A Unit has additional methods used by the graph tools, such as the `process` method:

```python
# Call our add_4 function:
>>> c.b.process(1)
5.0
```

A new unit is very unique. Creating a Connection with the same function for both sides `a` and `b`, will insert two new nodes:

```python
c = make_edge(f.add_4, f.add_4)
c.pluck(4)
12.0
```

We can cast a function as a `Unit` before insertion, allowing the re-reference to _existing_ nodes.

### Very Unique `Unit`

> [!IMPORTANT]
> A `Unit` is unique, even when using the same function:
> `Unit(my_func)` != `Unit(my_func)`


If you create a Unit using the same function, this will produce two unique units:

```python
unit_a = as_unit(f.add_2)
unit_a_2 = as_unit(f.add_2)
assert unit_a != unit_a_2  # Not the same.
```

Attempting to recast a `Unit`, will return the same `Unit`:

```python
unit_a = as_unit(f.add_2)
unit_a_2 = as_unit(unit_a) # unit_a is already a Unit
assert unit_a == unit_a_2  # They are the same
```

---

With this we create a linear chain of function calls, or close a loop that will run forever.

### Linear (not closed)

Generally when inserting functions, a new reference is created. This allows us to use the same function at different points in a chain:

![3 nodes linear chain](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/3-nodes.png)

```python
a = f.add_1
b = f.add_2
c = f.add_2

# a -> b -> c | done.
connection_1 = make_edge(a, b)
_ = make_edge(b, c)
_ = make_edge(c, a)

```


### Loop (closed)

Closing a path produces a loop. To close a path we can reuse the same `Unit` at both ends of our path.

![3 nodes loop](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/3-node-loop.png)

To ensure a node is reused when applied, we pre-convert it to a `Unit`:

```python
a = as_unit(f.add_1) # sticky reference.
b = f.add_2
c = f.add_2

# a -> b -> c -> a ... forever
connection_1 = make_edge(a, b)
_ = make_edge(b, c)
_ = make_edge(c, a)
```



## 👣 Stepper

The `Stepper` run units and discovers connections through the attached Graph. It runs concurrent units and spools the next callables for the next _step_.

![self referencing connection](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper.png)

```python
from hyperway.graph import Graph
from hyperway.tools import factory as f

g = Graph()
a_connections = g.connect(f.add_10, f.add_20, f.add_30)
b_connections = g.connect(f.add_1, f.add_2, f.add_3)
c_connection = g.add(b_connections[1].b, f.add_3)

first_connection_first_node = a_connections[0].a
stepper = g.stepper(first_connection_first_node, 10)
# <stepper.StepperC object at 0x000000000258FEB0>

concurrent_row = stepper.step()
# rows. e.g: ((<Unit(func=my_func)>, <ArgsPack(*(1,), **{})>),)
```

For each `step()` call, we yield a step. When iterating from `first_connection_first_node` (`f.add_10`), the stepper will _pause_ half-way through our call. The _next_ step will resolve the value and prepare the next step:

```python
# From above:
# g.stepper(first_connection_first_node, 10)

stepper.step()
(
    # Partial edge (from add_10 to add_20), with the value "20.0" (10 add 10)
    (<edges.PartialConnection>, <ArgsPack(*(20.0,), **{})>),
)


stepper.step()
(
    # Previous step complete; input(10), add(10), then add(20)
    (<Unit(func=P_add_30.0)>, <ArgsPack(*(40.0,), **{})>),
)

```

We initiated a stepper at our preferred node `stepper = g.stepper(first_connection_first_node, 10)`. Any subsequent `stepper.step()` calls _push_ the stepper to the next execution step.

Each iteration returns the _next_ thing to perform and the values from the previous unit call.

```python
# Many (1) rows to call next.
(
    (<Unit(func=P_add_30.0)>, <ArgsPack(*(40.0,), **{})>),
)
```

We see one row, with `f.add_30` as the _next_ function to call.


### `run_stepper` Function

The stepper can run once (allowing us to loop it), or we can use the built-in `run_stepper` function, to walk the nodes until the chain is complete

```python
from hyperway.graph import Graph
from hyperway.tools import factory as f

from hyperway.packer import argspack
from hyperway.stepper import run_stepper


g = Graph()
connections = g.connect(f.add_10, f.add_20, f.add_30)

# run until exhausted
result = run_stepper(g, connections[0].a, argspack(10))
```

---

# Results

The value of the stepper is concurrent. When a path ends, the value is stored in the `stepper.stash`.
When executing node steps, the result from the call is given to the next connected unit.

## Accessing Results

The stepper provides convenient methods to access results without manually unwrapping the stash:

```python
g = Graph()
g.connect(f.add_10, f.add_20, f.add_30)

g.stepper_prepare(start_node, 10)
s = g.stepper()

while s.step():
    pass

# Simple access to results
result = s.get_result()  # 70 (single result)
results = s.get_results()  # [70] (all results as list)

# Check if results exist
if s.has_results():
    print(f"Got {s.result_count()} results")
```

For graphs with multiple endpoints, organize results by node:

```python
# Branching graph with multiple handlers
g.add(source, handler_a)  # handler_a named 'process_a'
g.add(source, handler_b)  # handler_b named 'process_b'

g.stepper_prepare(source, 10)
s = g.stepper()
while s.step():
    pass

# Organize by node name
results_dict = s.get_results_dict()
# {'process_a': [42], 'process_b': [100]}

# Access specific handler results
process_a_results = results_dict['process_a']
```

> [!TIP]
> Use `get_result()` for single-endpoint graphs, `get_results()` for all results as a list, or `get_results_dict()` to organize by node name.

### Advanced: Custom Keys and ArgsPack

You can organize results using custom keys:

```python
# By node ID
results_by_id = s.get_results_dict(key=lambda n: n.id())

# By function name
results_by_func = s.get_results_dict(key=lambda n: n.func.__name__)
```

For advanced use cases, access raw `ArgsPack` objects and use `.flat()` for custom unwrapping:

```python
# Get raw ArgsPack objects
raw_results = s.get_results(unwrap=False)

for akw in raw_results:
    value = akw.flat()  # Smart unwrapping to natural representation
    # Or access directly: akw.args, akw.kw
```

## Streaming Results

For real-time processing, the streaming API yields results as they become available during graph execution:

```python
g.stepper_prepare(start_node, 10)
s = g.stepper()

# Stream results as they arrive (no need to wait for completion)
for result in s.stream():
    print(f"Got result: {result}")
    # Process immediately, update progress, etc.

# After streaming, stash is empty (results were popped)
assert len(s.stash) == 0
```

**Key Features:**
- **Real-time processing** - React to results as branches complete
- **Memory-safe** - Results are popped from stash as they're yielded
- **Progress monitoring** - Track long-running graph execution
- **Early termination** - Break from loop to stop execution
- **Infinite loop safety** - Memory stays constant even in cyclic graphs

```python
# Multiple endpoints - results arrive as each branch completes
for result in s.stream():
    process(result)  # Handle each result immediately

# Early termination
for result in s.stream():
    if result > 50:
        break  # Stop execution when condition met
```

> [!TIP]
> Use `stream()` for long-running graphs, reactive patterns, or when you need progress feedback. For complete graphs where you need all results at once, use the standard `get_results()` approach.

📖 **[Full Streaming Documentation →](docs/stepper-stream.md)**

![stepper classic path movement](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper-classic-path.png)

If two nodes call to the same destination node, this causes _two_ calls of the next node:

```python
           +4
i  +2  +3       print
           +5
```

With this layout, the `print` function will be called twice by the `+4` and `+5` node. Two calls occur:

```python

          10
 1  3  6      print
          11

# Two results
print(10) # from path: 1 → +2 → +3 → +4 → 10
print(11) # from path: 1 → +2 → +3 → +5 → 11
```

This is because there are two connections _to_ the `print` node, causing two calls.


## Result Concatenation (Merge Nodes)

Use merge nodes to action _one_ call to a node, with two results.

1. Set `merge_node=True` on target node
2. Flag `concat_aware=True` on the stepper

![stepper merge node](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper-merge.png)

```python
g = Graph()
u = as_unit(print)
u.merge_node = True

s = g.stepper()
s.concat_aware = True

s.step()
...
```

When processing a print merge-node, one call is executed when events occur through multiple connections during one step:

```python
         10
1  3  6      print
         11

print(10, 11) # resultant
```


## Results Explode!

> [!IMPORTANT]
> Every _fork_ within the graph will yield a new path.

A _path_ defines the flow of a `stepper` through a single processing chain. A function connected to more than one function will _fork_ the stepper and produce a result per connection.

![stepper classic path movement](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper-value-2-fork-wires.png)

For example a graph with a a split path will yield two results:

```python
from hyperway import Graph, as_units
from hyperway.tools import factory as f

g = Graph()

split, join = as_units(f.add_2, f.add_2)

cs = g.connect(f.add_1, split)
g.connect(split, f.add_3, join)
g.connect(split, f.add_4, join)
g.connect(join, f.add_1)
```

If [graphviz](https://github.com/xflr6/graphviz) is installed, The graph can be rendered with `graph.write()`:

```python
# Continued from above
g.write('double-split', direction='LR')
```

![double split](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/double-split.gv.png)

---

Connecting nodes will grow the result count. For example creating in two exits nodes will double the result count

![stepper classic path movement](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper-value-4-fork-wires.png)

To model this, we can extend the _above_ code with an extra connection: `g.connect(join, f.sub_1)`:

```python
# same as above
from hyperway import Graph, as_units
from hyperway.tools import factory as f

g = Graph()

split, join = as_units(f.add_2, f.add_2)

cs = g.connect(f.add_1, split)
g.connect(split, f.add_3, join)
g.connect(split, f.add_4, join)
g.connect(join, f.add_1)

# connect another function
g.connect(join, f.sub_1)

g.write('double-double-split', direction='LR')
```

![double split with two exit nodes](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/double-double-split.png)

> [!NOTE]
> The count of results is a _product_ of the node count - and may result exponential paths if unmanaged.
> Hyperway can **and will** execute this forever.

_Wire functions have been removed for clarity_

![stepper classic path movement](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper-value-9-fork.png)

```python
from hyperway import Graph, as_unit

g = Graph()

split = as_unit(f.add_2, name='split')
join_a = as_unit(f.add_2)

# sum([1,2,3]) accepts an array - so we merge the args for the response.
join = as_unit(lambda *x: sum(x), name='sum')

cs = g.connect(f.add_1, split)
g.connect(split, f.add_3, join)
g.connect(split, f.add_4, join)
g.connect(split, f.add_5, join)

g.connect(join, f.add_1)
g.connect(join, f.sub_1)
g.connect(join, f.sub_2)
g.write('triple-split', direction='LR')
```

![triple split with three exit nodes](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/triple-split-3.gv.png)


## Dynamic Edge Selection (Knuckles)

**Knuckles** enable nodes to dynamically choose which outgoing edges to traverse based on runtime data. This allows you to build conditional routing, state machines, and decision trees directly into your graph topology.

By default, when a node has multiple outgoing connections, the stepper traverses all of them (parallel expansion). A knuckle intercepts this behavior and returns a filtered subset of edges.

```python
from hyperway.graph import Graph
from hyperway.nodes import Unit, as_unit
from hyperway.packer import argspack


class Router(Unit):
    """Route based on 'target' key in data."""
    
    def get_connections(self, graph, akw=None):
        # Get all outgoing edges from this node
        connections = tuple(graph.get(self.id(), ()))
        
        if akw is None:
            return connections  # No data, return all edges
        
        # Filter edges by connection name matching 'target' key
        target = akw.get('target')
        if target is None:
            return connections
        
        filtered = tuple(c for c in connections if c.name == target)
        return filtered if filtered else ()


# Build a graph with conditional routing
g = Graph()

router = Router(lambda x: x)
handler_a = as_unit(lambda x: f"Handler A: {x}")
handler_b = as_unit(lambda x: f"Handler B: {x}")

g.add(router, handler_a, name='route_a')
g.add(router, handler_b, name='route_b')

# Execute: only handler_a will be reached
g.stepper_prepare(router, argspack(10, target='route_a'))
s = g.stepper()
while s.step():
    pass

# Result in s.stash will be "Handler A: 10"
```

The `get_connections()` method receives the current data (`akw`) and can apply any logic to filter edges—based on values, predicates, state, or even external conditions.

> [!TIP]
> Use knuckles for: conditional branching, routing based on data attributes, implementing state machines, round-robin scheduling, or circuit breaker patterns.

See [`docs/knuckles.md`](docs/knuckles.md) for advanced patterns including stateful knuckles, predicate-based filtering, and round-robin routing.

---

#### Order of Operation

> [!IMPORTANT]
> Hyperway is left-associative, Therefore PEMDAS/BODMAS will not function as expected - graph chains execute linearly.

The order of precedence for operations occurs through sequential evaluation (from left to right) similar to C. Each operation is executed as it is encountered, without regard to the traditional precedence of operators.

+ [IBM z/OS Precedence and associativity][ibm-order-precedence]
+ [lagrammar.net][lag]
+ [Complexity in left-associative grammar][complexity-in-lag]


<table>
<thead><tr>
  <th align="left">Standard order precedence</th>
  <th align="left">Hyperway left-association</th>
</tr></thead>
<tbody><tr valign="top"><td>

```python
# BODMAS computes * first
 1 + 1 * 2 + 2 == 5
10 + 1 * 2 + 2 == 14
```

</td><td>

```python
# left-to-right computes linearly
( (1 + 1)  * 2) + 2 == 6
( (10 + 1) * 2) + 2 == 24
```

</td></tbody></table>

```python
# example sequential evaluation
from hyperway.tools import factory as f
from hyperway.edges import make_edge, wire

c = make_edge(f.add_1, f.add_2, through=wire(f.mul_2))

assert c.pluck(1) == 6   # (1 + 1) * 2 + 2 == 6
assert c.pluck(10) == 24 # (10 + 1) * 2 + 2 == 24
```

# Topology

![stepper classic path movement](https://raw.githubusercontent.com/Strangemother/python-hyperway/main/docs/images/stepper-value-fork.png)

+ [Graph](#graph-1): The Graph is a thin and dumb dictionary, maintaining a list of connections per node.
+ [Node](#units-and-nodes-1): The Node is also very terse, fundamentally acting as a thin wrapper around the user given function, and exposes a few methods for _on-graph_ executions.
+ [Edges](#connection-1): Edges or Connections are the primary focus of this version, where a single `Connection` is bound to two nodes, and maintains a wire-function.
+ [Stepper](#-stepper): The _Stepper_ performs most of the work for interacting with Nodes on a graph through Edges.

## Breakdown

We push _Node to Node_ Connections into the `Graph` dictionary. The Connection knows `A`, `B`, and potentially a Wire function.

When _running_ the graph we use a `Stepper` to processes each node step during iteration, collecting _results_ of each call, and the next executions to perform.

---

We _walk_ through the graph using a `Stepper`. Upon a step we call any rows of waiting callables. This may be the users first input and will yield _next callers_ and _the result_.

The `Stepper` should call each _next caller_ with the given _result_. Each _caller_ will return _next callers_ and a _result_ for the `Stepper` to call again.

In each iteration the callable resolves one or more connections. If no connections return for a node, The execution chain is considered complete.

### Understanding the Graph

The `Graph` is purposefully terse. Its build to be as minimal as possible for the task. In the raw solution the `Graph` is a `defaultdict(tuple)` with a few additional functions for node acquisition.

The graph maintains a list of `ID` to `Connection` set.

```python
{
  ID: (
        Connection(to=ID2),
    ),
  ID2: (
        Connection(to=ID),
    )
}
```

### Core Connection Knowledge

A `Connection` bind two functions and an optional wire function.

    A -> [W] -> B

When executing the connection, input starts through `A`, and returns through `B`. If the wire function exists it may alter the value before `B` receives its input values.

### Units and Nodes

A `Unit` represents a _thing_ on the graph, bound to other units through connections.

```python
def callable_func(value):
    return value * 3

as_unit(callable_func)
```

A unit is one reference

```python
unit = as_unit(callable_func)
unit2 = as_unit(callable_func)

assert unit != unit2
```

### Extras

#### `argspack`

The `argspack` simplifies the movement of arguments and keyword arguments for a function.

we can wrap the result as a pack, always ensuring its _unpackable_ when required.

```python
akw = argspack(100)
akw.a
(100, )

akw = argspack(foo=1)
akw.kw
{ 'foo': 1 }
```

---

# Project Goal

Although many existing libraries cater to graph theory, they often require a deep understanding of complex terminology and concepts. As an engineer without formal training in graph theory, these libraries are challenging.
**Hyperway** is the result of several years of research aimed at developing a simplified, functional, graph-based execution library with a minimal set of core features.


I'm slowly updating it to include the more advanced [future features](docs/future.md), such as hyper-edges and connection-decisions, bridging the gap between academic graph theory and practical application, providing developers with a low-level runtime that facilitates functional execution without the need for specialized knowledge.

# Areas of Interest

+ https://graphclasses.org/
+ https://houseofgraphs.org/
+ https://en.wikipedia.org/wiki/Cyber%E2%80%93physical_system
+ https://en.wikipedia.org/wiki/Signal-flow_graph
+ https://resources.wolframcloud.com/FunctionRepository/resources/HypergraphPlot
+ https://www.lancaster.ac.uk/stor-i-student-sites/katie-howgate/2021/04/29/hypergraphs-not-just-a-cool-name/

# Further Reading

+ [TensorFlow: Introduction to Graph and `tf.function`](https://www.tensorflow.org/guide/intro_to_graphs)
+ [Wiki: Extract, transform, load](https://en.wikipedia.org/wiki/Extract,_transform,_load)
+ https://docs.dgl.ai/en/2.0.x/notebooks/sparse/hgnn.html | https://github.com/iMoonLab/DeepHypergraph/blob/main/README.md
+ https://distill.pub/2021/gnn-intro/
+ https://renzoangles.net/gdm/

# Other Libraries

+ [Graphtik](https://graphtik.readthedocs.io/en/latest/)
+ [iGraph](https://python.igraph.org/en/stable/index.html#)
+ [graph-tool](https://graph-tool.skewed.de/)
+ [pyDot](https://github.com/pydot/pydot)
+ [FreExGraph](https://github.com/FreeYourSoul/FreExGraph)
+ [NetworkX](https://networkx.org/documentation/latest/index.html)

# Links

+ https://graphviz.org/

[ibm-order-precedence]: https://www.ibm.com/docs/en/zos/3.1.0?topic=section-precedence-associativity
[lag]: https://lagrammar.net/monographs/1999/slides/pdf/chapter-10.pdf
[complexity-in-lag]: https://lagrammar.net/papers/aij.pdf


---

+ https://pypistats.org/packages/hyperway
+ https://sonarcloud.io/summary/overall?id=Strangemother_python-hyperway&branch=main


