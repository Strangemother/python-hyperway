from hyperway.graph import Graph
from hyperway.tools import factory as f

"""A defaultdict, to store the connections in one place."""
g = Graph(tuple)

"""Bind three functions +10, +20, +30"""
a_connections = g.connect(f.add_10, f.add_20, f.add_30)

"""Bind three functions +1, +2, +3"""
b_connections = g.connect(f.add_1, f.add_2, f.add_3)
"""Bind one function at the tip of the previous, +1, +2, +3, +3 """
c_connections = g.add(b_connections[1].b, f.add_3)

first_connection_first_node = a_connections[0].a
second_connection_first_node = b_connections[0].a


"""Generate a "stepper", to walk the graph from a start node.
We can provide expected arguments to the initial node, in this case (1).
"""
s = stepper = g.stepper(first_connection_first_node, 1)
# <stepper.StepperC object at 0x000000000258FEB0>
print('First node:', first_connection_first_node)

"""The stepper is prepared. Execute the _step_ function 3 times,
each time the stepper will work the graph, executing nodes and updating the
concurrent nodes.

The last call (in this case) yields zero rows. This is because we run out of
connections to step, and the no-rows is presenting
"next things to call is ...nothing."

At this point we can inspect the `stepper.stash` to see the result values
"""
# input(1) + 10 + 20 + 30 == 61
s.step(count=3) # n-1 then +1 to stash
print(s.stash) # 61.0

print('--')

""" Another Stepper, same graph - this time starting from a different node and
step four times.
"""
s = g.stepper(second_connection_first_node, 3)
s.step(count=4)
print(s.stash) # 12.0

""" We can split the path, adding multiple connections to one node.

When stepping the result, the _rows_ will fork, yielding two stashed values.


                         |- (split with 9.0)
                         |
                         | +3       -> 12
    input(3) -> +1 +2 +3 |
                         | +12 *.5  -> 10.5

"""
d_connections = g.connect(b_connections[1].b, f.add_12, f['mul_.5'])
s = g.stepper(second_connection_first_node, 3)

s.step() # 4, 6, [9, 9], [12, 21] [x, 10.5]