# Stepper

The stepper is the little machine that walks the graph of nodes. It executes and stores results as it progresses. 

An example graph:

```py
g = Graph(tuple)

def doubler(v=0):
    return v * 2


def collector(v):
    return v

du = as_unit(doubler)
e = g.add(du, collector)
e2 = g.add(du, collector)
```

To run a stepper, we must give it a starting node and any initial arguments.

```py
# continued from above
# We start at _some node_, with a value of 4
g.stepper_prepare(du, 4)
```

Now the stepper is ready to walk the graph, we can step through each node:

```py
stepper = g.stepper() # get the stepper instance
stepper.step() 
```

We can inspect the stepper stashed values at any time. When the stepper completes a path, the results are stored in the stash:

```py
stepper.step() # returns _the next step_
# ((<PartialConnection to Unit(func=collector)>, <ArgsPack(*(8,), **{})>),)

stepper.stash # nothing yet
# defaultdict(<class 'tuple'>, {})

stepper.step() # perform the waiting (next) step.
# C(0) "Unit(func=collector)"   # We hit the `collector` function
() # no next step

stepper.stash # We can see the result now
# defaultdict(<class 'tuple'>, {<PartialConnection to Unit(func=collector)>: (<ArgsPack(*(8,), **{})>,)})
```

That's it! It's that simple!

1. The stepper walks the graph one node at a time.
2. It executes the node, and stores the next step.
3. If there is no next step, it stores the result in the `stash`.


