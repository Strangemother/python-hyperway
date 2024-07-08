<div align="center">

# Hyperway

Python graph based functional execution library, with a unique API.

[![Upload Python Package](https://github.com/Strangemother/python-hyperway/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Strangemother/python-hyperway/actions/workflows/python-publish.yml)
![PyPI](https://img.shields.io/pypi/v/hyperway?label=hyperway)
![PyPI - Downloads](https://img.shields.io/pypi/dm/hyperway)

---

</div>

+ [Functions](#functions)
+ [Connections (Edges)](#connections-edges)
+ [Wire Functions](#wire-function)
+ [Units Nodes](#units-nodes)
+ [Graph](#graph)
+ [Stepper](#stepper)
+ [Reference Links](#areas-of-interest)

Hyperway is a graph based functional execution library, allowing you to connect functions arbitrarily through a unique API. Mimic a large range of programming paradigms such as procedural, parallel, or aspect-oriented-programming. Build B-trees or decision trees, circuitry or logic gates; all with a simple _wiring_ methodology.

## Install

```bash
pip install hyperway
```

## Example

Connect functions, then run your chain:

```py
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

Render with graphviz:

```py
g.write('intro-example', directory='renders', direction='LR')
```

![connection diagram](./docs/images/intro-example.gv.png)

# What's In The Box

> The `Unit` (or node) is a function connected to other nodes through a `Connection`.  The `Graph` maintains a register of all connections.

+ `Graph`: A thing to hold all connections
+ `Unit`: A function on a graph, bound through edges
+ `Edge`: A connection between Units
+ `Stepper`: A graph walking tool

This library aims to simplify graph based execution chains, allowing a developer to use functional graphs without managing the connections.


## Graph

The `Graph` is a fancy `defaultdict` of tuples, used to store connections:


```py
import hyperway

g = hyperway.Graph()
```


## Connections (Edges)

Bind functions in an execution chain. Notably it's a minimum of two:

![connection diagram of two nodes with an optional wire function](./docs/images/connection.png)


<table>
<thead><tr>
  <th align="left">Functional</th>
  <th align="left">Hyperway Graph</th>
</tr></thead>
<tbody><tr valign="top"><td>

```py
from hyperway.edges import make_edge

c = make_edge(f.add_1, f.add_2)
# <Connection>
```

</td><td>


```py
import hyperway
from hyperway.tools import factory as f

g = hyperway.Graph()

connection = g.add(f.add_1, f.add_2)
# <Connection>
```

</td></tbody></table>


> [!IMPORTANT]
> A `Connection` runs in two processing steps, due to a potential _wire_ function. Use `pluck()` to run both steps.

A standard call will run node `a`:

```py
>>> value_part_a = connection(1) # call A-side `add_1`
2.0
```

Then process the second part `b` (providing the value from the first call):

```py
>>> connection.process(value_part_a) # call B-side `add_2`
4.0
```

### Plucking Edges

We can "pluck" a connection (like plucking a string) to run it with any arguments.

```py
from hyperway.tools import factory as f
from hyperway.edges import make_edge

c = make_edge(f.add_1, f.add_2)
# Run side _a_ (`add_1`) and _b_ (`add_2`) with our input value.

c.pluck(1)
# 4.0 == 1 + 1 + 2

c.pluck(10)
# 13.0 == 10 + 1 + 2
```

### Wire Function

The connection can have a _wire_ function; a function existing between the two connections, allowing the alteration of the data through transit (whilst running through a connection)

```py
from hyperway.tools import factory as f
from hyperway.edges import make_edge, wire

c = make_edge(f.add_1, f.add_2, through=wire(f.mul_2))
# <Connection(Unit(func=P_add_1.0), Unit(func=P_add_2.0), through="P_mul_2.0" name=None)>

assert c.pluck(1) == 10 # (1 + 1) * 2 + 2 == 6
assert c.pluck(10) == 24 # (10 + 1) * 2 + 2 == 24
```

---

**Why use a wire function?**

It's easy to argue a wire function is a _node_, and you can implement the wire function without this connection tap.

+ Wire functions are optional: node to node connections are inherently not optional)
+ Removing a wire function does not remove the edge: Edges are persistent to the graph
+ Wire functions may be inert (e.g. just logging); Nodes cannot be inert as they must be bound to edges.

Fundamentally a wire function exists for topological clarity and may be ignored.

---

`make_edge` can accept the wire function. It receives the concurrent values transmitting through the attached edge:

```py
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

c.pluck(1)
6.0

c.pluck(2)
8.0

c.pluck(3)
10.0
```

The wire function is the reason for a two-step process when executing connections:

```py
# Call Node A: (+ 1)
c(4)
5.0

# Call Wire + B: (double then + 2)
c.process(5.0)
12.0
```

Or a single `pluck()`:

```py
c.pluck(4)
12.0
```

#### Self Reference

A connection `A -> B` may be the same node, performing a _loop_ or self-referencing node connection.

![self referencing connection](./docs/images/self-reference.png)


We can use the `as_unit` function, and reference the same unit on the graph:

```py
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

```py
from hyperway.tools import factory as f
add_10 = f.add_10
# functools.partial(<built-in function add>, 10.0)
add_10(1)
# 11.0
add_10(14)
# 24.0
```


## Units (Nodes)


The `Unit` (or node) is a function connected to other nodes through a `Connection`. A `Unit` is a wrapper for a connected function. Everything on a graph (and within a connection) is a `Unit`:

```py
c = make_edge(f.mul_3, f.add_4)
c.a
# <Unit(func=P_mul_3.0)>
c.b
# <Unit(func=P_add_4.0)>
```

A Unit has additional methods used by the graph tools, such as the `process` method:

```py
# Call our add_4 function:
>>> c.b.process(1)
5.0
```

A new unit is unique, ensuring each new addition to the graph is will insert as a new node, allowing you to use the many times:

```py
c = make_edge(f.add_4, f.add_4)
c.pluck(4)
12.0
```

We can create a unit before insertion, to allow references to an _existing_ node.
For example we can close a loop or a linear chain of function calls.

### Very Unique `Unit`

> [!IMPORTANT]
> A `Unit` is unique, even when using the same function:
> `Unit(my_func)` != `Unit(my_func)`


If you create a Unit using the same function, this will produce two unique units:

```py
unit_a = as_unit(f.add_2)
unit_a_2 = as_unit(f.add_2)
assert unit_a != unit_a_2  # Not the same.
```

Attempting to recast a `Unit`, will return the same `Unit`:

```py
unit_a = as_unit(f.add_2)
unit_a_2 = as_unit(unit_a) # unit_a is already a Unit
assert unit_a == unit_a_2  # They are the same
```

### Linear (not closed)

Generally when inserting functions, a new reference is created. This allows us to use the same function at different points in a chain:

![3 nodes linear chain](./docs/images/3-nodes.png)

```py
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

![3 nodes loop](./docs/images/3-node-loop.png)

To ensure a node is reused when applied, we pre-convert it to a `Unit`:

```py
a = as_unit(f.add_1) # sticky reference.
b = f.add_2
c = f.add_2

# a -> b -> c -> a ... forever
connection_1 = make_edge(a, b)
_ = make_edge(b, c)
_ = make_edge(c, a)
```


## Graph

All Connections are stored within a single `Graph` instance. It has been purposefully designed as a small collection of connections. We can consider the graph as a dictionary register of all associated connections.

```py
from hyperway.graph import Graph, add
from hyperway.nodes import as_units

g = Graph()
unit_a, unit_b = as_unit(f.add_2, f.mul_2)

connection = add(g, unit_a, unit_b)
```

Under the hood, The graph is just a `defaultdict` and doesn't do much.


## Stepper

The `Stepper` run units and discovers connections through the attached Graph. It runs concurrent units and spools the next callables for the next _step_.

![self referencing connection](./docs/images/stepper.png)

```py
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

```py
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

```py
# Many (1) rows to call next.
(
    (<Unit(func=P_add_30.0)>, <ArgsPack(*(40.0,), **{})>),
)
```

We see one row, with `f.add_30` as the _next_ function to call.


### `run_stepper` Function

The stepper can run once (allowing us to loop it), or we can use the built-in `run_stepper` function, to walk the nodes until the chain is complete

```py
from hyperway.graph import Graph
from hyperway.tools import factory as f

from hyperway.packer import argspack
from hyperway.stepper import run_stepper


g = Graph()
connections = g.connect(f.add_10, f.add_20, f.add_30)

# run until exhausted
result = run_stepper(g, connections[0].a, argspack(10))
```

# Results

The value of the stepper is concurrent. When a path ends, the value is stored in the `stepper.stash`.
When executing node steps, the result from the call is given to the next connected unit.

![stepper classic path movement](./docs/images/stepper-classic-path.png)

If two nodes call to the same destination node, this causes _two_ calls of the next node:

```py
           +4
i  +2  +3       print
           +5
```

With this layout, the `print` function will be called twice by the `+4` and `+5` node. Two calls occur:

```py

          10
 1  3  6      print
          11

# Two results
print(10)
print(11)
```

This is because there are two connections _to_ the `print` node, causing two calls.


## Result Concatenation (Merge Nodes)

Use merge nodes to action _one_ call to a node, with two results.

1. Set `merge_node=True` on target node
2. Flag `concat_aware=True` on the stepper

![stepper merge node](./docs/images/stepper-merge.png)


```py
g = Graph()
u = as_unit(print)
u.merge_node = True

s = g.stepper()
s.concat_aware = True

s.step()
...
```

When processing a print merge-node, one call is executed when events occur through multiple connections during one step:

```py
         10
1  3  6      print
         11

print(10, 11) # resultant
```

## Results Explode!

> [!IMPORTANT]
> Every _fork_ within the graph will yield a new path.

A _path_ defines the flow of a `stepper` through a single processing chain. A function connected to more than one function will _fork_ the stepper and produce a result per connection.

![stepper classic path movement](./docs/images/stepper-value-2-fork-wires.png)

For example a graph with a a split path will yield two results:

```py
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

```py
# Continued from above
g.write('double-split', direction='LR')
```

![double split](./docs/images/double-split.gv.png)

---

Connecting nodes will grow the result count. For example creating in two exits nodes will double the result count

![stepper classic path movement](./docs/images/stepper-value-4-fork-wires.png)

To model this, we can extend the _above_ code with an extra connection: `g.connect(join, f.sub_1)`:

```py
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

![double split with two exit nodes](./docs/images/double-double-split.png)

> [!NOTE]
> The count of results is a _product_ of the node count - and may result exponential paths if unmanaged.
> Hyperway can **and will** execute this forever.

_Wire functions have been removed for clarity_

![stepper classic path movement](./docs/images/stepper-value-9-fork.png)

```py
from hyperway import Graph, as_unit

g = Graph()

split = as_unit(f.add_2, name='split')
join_a = as_unit(f.add_2)

# sum([1,2,3]) accepts an array - so we merge the args for the response.
join = as_unit(lambda *x: sum(x) name='sum')

cs = g.connect(f.add_1, split)
g.connect(split, f.add_3, join)
g.connect(split, f.add_4, join)
g.connect(split, f.add_5, join)

g.connect(join, f.add_1)
g.connect(join, f.sub_1)
g.connect(join, f.sub_2)
g.write('triple-split', direction='LR')
```

![triple split with three exit nodes](./docs/images/triple-split-3.gv.png)


#### Order of Operation

> [!IMPORTANT]
> Hyperway is left-associative, Therefore PEMDAS/BODMAS will not function as expected - graph chains execute linearly.

The order of precedence for operations occurs through sequential evaluation (from left to right) similar to C++. Each operation is executed as it is encountered, without regard to the traditional precedence of operators.

<table>
<thead><tr>
  <th align="left">Standard order precedence</th>
  <th align="left">Hyperway left-association</th>
</tr></thead>
<tbody><tr valign="top"><td>

```py
# BODMAS computes * first
 1 + 1 * 2 + 2 == 5
10 + 1 * 2 + 2 == 14
```

</td><td>

```py
# left-to-right computes linearly
( (1 + 1)  * 2) + 2 == 6
( (10 + 1) * 2) + 2 == 24
```

</td></tbody></table>

```py
# example sequential evaluation
from hyperway.tools import factory as f
from hyperway.edges import make_edge, wire

c = make_edge(f.add_1, f.add_2, through=wire(f.mul_2))

assert c.pluck(1) == 10 # (1 + 1) * 2 + 2
assert c.pluck(10) == 24 # (10 + 1) * 2 + 2
```

# Topology

![stepper classic path movement](./docs/images/stepper-value-fork.png)

+ [Graph](#graph-1): The Graph is a thin and dumb dictionary, maintaining a list of connections per node.
+ [Node](#units-and-nodes): The Node is also very terse, fundamentally acting as a thin wrapper around the user given function, and exposes a few methods for _on-graph_ executions.
+ [Edges](#connection): Edges or Connections are the primary focus of this version, where a single `Connection` is bound to two nodes, and maintains a wire-function.
+ Stepper: The _Stepper_ performs much of the work for interacting with Nodes on a graph through Edges.

## Breakdown

We push _Node to Node_ Connections into the `Graph` dictionary. The Connection knows `A`, `B`, and potentially a Wire function.

When _running_ the graph we use a `Stepper` to processes each node step during iteration, collecting _results_ of each call, and the next executions to perform.

---

We _walk_ through the graph using a `Stepper`. Upon a step we call any rows of waiting callables. This may be the users first input and will yield _next callers_ and _the result_.

The `Stepper` should call each _next caller_ with the given _result_. Each _caller_ will return _next callers_ and a _result_ for the `Stepper` to call again.

In each iteration the callable resolves one or more connections. If no connections return for a node, The execution chain is considered complete.

### Graph

The `Graph` is purposefully terse. Its build to be as minimal as possible for the task. In the raw solution the `Graph` is a `defaultdict(tuple)` with a few additional functions for node acquisition.

The graph maintains a list of `ID` to `Connection` set.

```py
{
  ID: (
        Connection(to=ID2),
    ),
  ID2: (
        Connection(to=ID),
    )
}
```

### Connection

A `Connection` bind two functions and an optional wire function.

    A -> [W] -> B

When executing the connection, input starts through `A`, and returns through `B`. If the wire function exists it may alter the value before `B` receives its input values.

### Units and Nodes

A `Unit` represents a _thing_ on the graph, bound to other units through connections.

```py
def callable_func(value):
    return value * 3

as_unit(callable_func)
```

A unit is one reference

```py
unit = as_unit(callable_func)
unit2 = as_unit(callable_func)

assert unit != unit2
```

### Extras

#### `argspack`

The `argspack` simplifies the movement of arguments and keyword arguments for a function.

we can wrap the result as a pack, always ensuring its _unpackable_ when required.

```py
akw = argswrap(100)
akw.a
(100, )

akw = argswrap(foo=1)
akw.kw
{ 'foo': 1 }
```

# Areas of Interest

+ https://graphclasses.org/
+ https://houseofgraphs.org/
+ https://en.wikipedia.org/wiki/Cyber%E2%80%93physical_system
+ https://en.wikipedia.org/wiki/Signal-flow_graph
+ https://resources.wolframcloud.com/FunctionRepository/resources/HypergraphPlot
+ https://www.lancaster.ac.uk/stor-i-student-sites/katie-howgate/2021/04/29/hypergraphs-not-just-a-cool-name/

# Links

+ https://graphviz.org/