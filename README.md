# Hyperway


```py
from graph import Graph
from tools import factory as f

# Store
g = Graph(tuple)

# Connect
first_connection = g.add(f.add_10, f.add_20)

many_connections = g.connect(f.add_30, f.add_1, f.add_2, f.add_3)
compound_connection = g.add(many_connections[1].b, f.add_3)

# Setup
stepper = g.stepper(first_connection.a, 10)

# Run
concurrent_row = stepper.step()
```

Per call "row" result:

```py
(
    (<Unit(func=add_20)>, <ArgsPack(*(1,), **{})>),
)
```

## Functions

A function is our working code. We can borrow operator functions from the tools:


```py
from tools import factory as f
add_10 = f.add_10
# functools.partial(<built-in function add>, 10.0)
add_10(1)
# 11.0
add_10(14)
# 24.0
```


## Connections (Edges)

Now we can bind two or more functions in an execution chain. Notably it's a minimum of two:

```py
from edges import make_edge
from tools import factory as

c = make_edge(f.add_1, f.add_2)
# <Connection(Unit(func=P_add_1.0), Unit(func=P_add_2.0), name=None)>

c.pluck(1)
# 4.0
```

We can "pluck" a connection (like plucking a string) for it to run side _a_ (`add_1`) and _b_ (`add_2`) with our input value.

**The answer is `4`**. Because our input `1`, add `1`, add `2`.

A Connection will run node _a_ when called:

```py
>>> c(1) # call A-side `add_1`
2.0
```

We can _process_ the second part:

```py
>>> c.process(2) # call B-side `add_2`
4.0
```


### Wire Function

The connection can have a _wire_ function; a function existing between the two connections, allowing the alteration of the data "through transit" (whilst running through a connection):


```py
from edges import make_edge
from packer import argspack

import tools as t
f = t.factory

def doubler(v, *a, **kw):
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

The wire function `through` _doubles_ the given number.

    input(10) + 1 * 2 + 2

This is why a connection has two processing steps:

```py
# Call Node A: (+ 1)
c(4)
5.0

# Call Wire + B: (double then + 2)
c.process(5.0)
12.0

# Or a single pluck()
c.pluck(4)
12.0
```

But usually we won't use with connections directly.


#### Self Reference

A Connection node A and node B may be the same node, performing a _loop_ or self-referencing node connection.

```py
u = as_unit(f.add_2)
e = make_edge(u,u)
g = Graph(tuple)
g.add_edge(e)
g.stepper(u, 1)

g.step()
g.step()
...
# 3, 5, 7, 9, 11, ...
```


### Units (Nodes)

A Unit is a wrapper for a connected function. Everything on a graph and a Connection is a Unit:

```py
>>> c = make_edge(f.mul_3, f.add_4)
>>> c.a
<Unit(func=P_mul_3.0)>
>>> c.b
<Unit(func=P_add_4.0)>
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

Linear (not closed.)

```py
a = f.add_1
b = f.add_2
c = f.add_3

# a -> b -> c | done.
connection_1 = make_edge(a, b)
_ = make_edge(b, c)
_ = make_edge(c, a)

```

Loop (closed)

```py
a = as_unit(f.add_1) # sticky reference.
b = f.add_2
c = f.add_3

# a -> b -> c -> a ... forever
connection_1 = make_edge(a, b)
_ = make_edge(b, c)
_ = make_edge(c, a)
```

This is because `a` will not generate new Units upon (2) inserts. Nodes `b` and `c` do create new nodes.

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

### Graph

All Connections are stored within a single `Graph` instance. It has been purposefully designed as a small collection of connections. We can consider the graph as a dictionary register of all associated connections.

```py
from graph import Graph, add
from nodes import as_unit


g = Graph(tuple)
unit_a = as_unit(f.add_2)
unit_b = as_unit(f.mul_2)

connection = add(g, unit_a, unit_b)
```

Under the hood, The graph is just a `defaultdict` and doesn't do much.


### Stepper

The `Unit` (or node) is a function connected to other nodes through a `Connection`. The `Graph` maintains a register of all connections.

The `Stepper` run units and discovers connections through the attached Graph.
It runs concurrent units and spools the next callables for the next _step_.

```py
from graph import Graph
from tools import factory as f

g = Graph(tuple)
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


### Result Concatenation

When executing node steps, the result from the call is given to the next connected unit. If two nodes call to the same destination node, this causes _two_ calls of the next node:

             +4
     i +2 +3      print
             +5

With this layout, the `print` function will be called twice by the `+4` and `+5` node. Two calls occur:


              10
     1  3  6      print
              11
    ...
    print(10)
    print(11)

This is because there are two connections _to_ the `print` node, causing two calls.

---

We can change this and action _one_ call to the print, with two results.

1. Set `merge_node=True` on target node
2. Flag `concat_aware=True` on the stepper

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

              10
     1  3  6      print
              11
    ...
    print(10, 11)


# Topology

The _Stepper_ performs much of the work for interacting with Nodes on a graph through Edges.

The Graph is a thin and dumb dictionary, maintaining a list of connections per node.

The Node is also very terse, fundamentally acting as a thin wrapper around the user given function, and exposes a few methods for _on-graph_ executions.

Edges are the primary focus of this version, where a single `Connection` is bound to two nodes, and maintains a wire-function.

## Breakdown.

We push _Node to Node_ Connections into the Graph dictionary. The Connection knows A, B, and potentially a Wire function.

When _running_ the graph we use a Stepper to processes each node step during iteration, collecting _results_ of each call, and the next executions to perform.

---

We _walk_ through the graph using a Stepper. Upon a step we call any rows of waiting callables. This may be the users first input and will yield _next callers_ and _the result_.

The Stepper should call each _next caller_ with the given _result_. Each _caller_ will return _next callers_ and a _result_ for the Stepper to call again.

In each iteration the callable resolves one or more connections. If no connections return for a node, The execution chain is considered complete.

### Graph

The `Graph` is purposefully terse. Its build to be as minimal as possible for the task. In the raw solution the `Graph` is a `defaultdict(tuple)` with a few additional functions for node acquisition.

The graph maintains a list of `ID` to `Connection` set.

    {
        ID: (
                Connection(to=ID2),
            ),
        ID2: (
                Connection(to=ID),
            )
    }

### Connection

A `Connection` bind two functions and an optional wire function.

    A -> [W] -> B

When executing the connection, input starts through `A`, and returns through `B`. If the wire function exists it may alter the value before `B` receives its input values.

### Units and Nodes

A `Unit` represents a _thing_ on the graph, bound to other units through connections.

    def callable_func(value):
        return value * 3

    as_unit(callable_func)

A unit is one reference

    unit = as_unit(callable_func)
    unit2 = as_unit(callable_func)

    assert unit != unit2

### Extras

#### `argspack`

The `argspack` simplifies the movement of arguments and keyword arguments for a function.

we can wrap the result as a pack, always ensuring its _unpackable_ when required.

    akw = argswrap(100)
    akw.a
    (100, )

    akw = argswrap(foo=1)
    akw.kw
    { 'foo': 1 }


# Areas of Interest

+ https://graphclasses.org/
+ https://houseofgraphs.org/
+ https://en.wikipedia.org/wiki/Cyber%E2%80%93physical_system
+ https://en.wikipedia.org/wiki/Signal-flow_graph