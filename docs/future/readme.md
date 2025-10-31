# Research Notes, Hyperway Extensions: Knuckles, Lambda Functions, and Hyperedges

## State Machine Interaction
HyperWay interacts with state machines using non-deterministic finite automatons (NFA). This allows changing condition sets as they traverse paths or nodes. Non-deterministic functionality lets us select which steps to take going forward. This is coupled with lambda functions along the edges of nodes. When a connection is chosen or a series of connections are selected, the lambda function can serve as a state transitioning tool, allowing a parallel or sibling system to manage a state independently of the graph and its nodes.

## Knuckles and Lambda Functions

see also: [Knuckles](./knuckles.md)

To integrate additional features into HyperWay, we extend the concept of a knuckle. A knuckle allows selecting from a finite set of connections. When visualized, this will allow using a knuckle function (or lambda) for a list of connections. The lambda function not only connects to a list of nodes, reducing the list of connections upon request, but also enables event emission for an independent state machine. This state machine can have non-deterministic or epsilon transitions, where a state can transition without consuming input symbols.

## Tagged Nodes and Edges
HyperWay can utilize tagged nodes or edges in a hypergraph methodology. During a step, rather than deterministic nodes and connections, it can request or infer a new set of nodes or conditions. The request for nodes is built into the graph as a tag, enabling it to find all nodes with a particular tag. Similarly, tagged connections can be requested upon exiting a node, retrieving a list of connections defined by a tag.

## [TODO: Rename] Fiber Connections

A _fiber_ is a "thinner" connection between nodes, or the knuckles on those nodes. A fiber can bridge the graph to reference nodes in the graph, of which are not directly connected (on the path).

For example we have a ring of 6 nodes, but the output of node three, alters node one output value. A fiber connection can be made between these nodes, allowing node three to influence node one without a direct connection in the path.

The _Graph_ path and nodes don't see this connection. The stepper doesn't traverse this edge. Instead, the fiber connection is a side-channel that allows nodes to influence each other without being on the main path.

The fiber may perform a range of interactions with the destinations. The receiver node may choose to listen to the fiber connection, or ignore it. The fiber connection may also perform transformations on the data being sent, or buffer it for later use.

---

Conceptually I feel this is important for the purpose of "back talk", where the tip of a connection (the outbound node or knuckle) can send information back to an earlier point in the graph without being on the main path. 

Consider for example electronic circuits, where feedback loops are common. A fiber connection could represent a feedback loop in a graph, without affecting the main flow of data.


## Hyperedges
Hyperedges allow multiple input and exit nodes on a single connection, treating many nodes grouped under one hyperedge as a single definition. This extends to executing a sub-graph of connections that the hyperedge is connected to. Implementing a boundary around a group of nodes creates a hyperedge that can connect to another node, graph, or hyperedge.

### Functionality of Hyperedges
The value from a hyperedge yields the same count of results as the nodes inside it. Each output node receives a unique copy of the same arguments, essentially calling each node individually. When a hyperedge activates with, for example, three nodes, it results in three values. By default, these values merge into one argument set for all output nodes. Alternatively, a hyperedge can have a recombobulation function to modify arguments as they progress. This is akin to a wire function, suggesting a hypergraph edge manipulation step (wire function) to manage connections across multiple nodes or hyperedges.

### Unique Configurations
Integrating unique functionality directly into the hyperedge allows for specific manipulations, requests, or configurations unique to the edge itself. For example, a hyperedge might require all nodes on the edge to activate simultaneously or stash the results of particular nodes as the stepper walks through them. When a hyperedge is "full," it emits a result down its connections. The default method requires all nodes to be activated simultaneously, while optional methods, such as the fill method, provide flexibility in how and when results are emitted.


## Edge | Hyperedge | Fiber | Knuckle 

An edge:

+ Standard connection
+ Single input and output node
+ Deterministic path
+ Has Wire function
+ Does not contain a sub-graph

A hyperedge:

+ Multiple input and output nodes
+ Non-deterministic path
+ Can contain sub-graphs
+ Has Recombobulation function
+ multiple inputs [may] fire simultaneously for an edge reaction

A fiber:

+ Side-channel connection
+ Connects non-adjacent nodes
+ Independent of main graph path
+ Can influence nodes and knuckles
+ Does not affect stepper traversal
+ Does not contain a sub-graph

A knuckle (aka connection selection):

+ Connection selector
+ Finite set of edges
+ Can use fiber
+ Has api for connection selection







### Directing a Stepper
Assign directions to a stepper, applying a preferred path to follow. For example, when on node `ID1`, follow connections `{4,6}`:

    Stepper:
        ID1: {4, 6}
        ID2: {2, 3}

As the stepper is _walking_, this test can force the direction of a stepper.