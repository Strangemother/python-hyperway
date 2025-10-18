# Topology

This document describes the topology of Hyperway. It may seem terse, but this absolutely covers the methodology and components of Hyperway (because Graphs are genuinely simple).


## Graph

The Hyperway graph is essentially a dumb dictionary, storing a connections against their IDs.

## Connection

A connection binds two nodes together. When executing a connection, we run two nodes and a potential wire function.

```py
from hyperway.edges import make_edge 

def node_a(x):
    return x + 1

def node_b(y):
    return y * 2

edge = make_edge(node_a, node_b)
# <Connection(Unit(func=node_a), Unit(func=node_b),  name=None)>
edge.pluck(7) 
# returns 16
```

## Node

A node is a unit of computation. Fundamentally it's a function but in Hyperway we _wrap_ the function as a unit. The unit exists within a connection.

```py
from hyperway import as_unit
def my_function(x):
    return x * 2

u = as_unit(my_function)
u.process(4)  # returns 8
```

```py
from hyperway.nodes import Unit
u = Unit(print)
u.get_name()
# returns "print"
u.process("Hello", "Hyperway!")
# prints "Hello Hyperway!"
``` 

## Wire function

A wire function exists within a connection between two nodes. It accepts the output of _'node A'_. Its result is sent to _'node B'_ as input.

## Stepper

Arguably the most important component of hyperway, the stepper is the "machine" running the graph. 

The stepper walks the graph, executing nodes and connections as it goes. Each step calls a node and stores its result. 

### Stepping process

The stepper is given a starting point (node ID) and an initial arguments. It executes the node and steps through the a connect to the next node.

As it steps to the new node, it may encounter a wire function of which optionally edits the data in transit. 

A node may have multiple outgoing connections. The stepper will branch, stepping each connection with its own copy stash of data.

The stepper will stop when there are no connections remaining.

