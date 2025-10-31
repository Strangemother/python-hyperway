# Vector Directional Executions

Vector directional executions refer to selecting nodes through directional vectors, such as PI/2. Allowing the developer to build computational graphs through directional relationships.

> In my thoughts, I call this a "ghost edge", where we assume a (default) connection, if the directional vector plots within the radius of another node (a function with an {x,y})


## Simple Example


A node is sitting at the origin (0,0) and has a directional vector of PI/2 (90 degrees). This means that the node is pointing straight up along the positive Y-axis.

For a a higher selection count in a more dense space, we can consider a node at (0,0) with a radius of 5 units. Pi/2 will plot a point nearest a node at (0,5).

This can also be combined with other directional vectors to create more complex selection patterns. For example, using PI/4 (45 degrees) and 3*PI/4 (135 degrees) will select nodes that are diagonally positioned relative to the origin node.

Another example is an arc spread selecting nodes in an connic projection.

