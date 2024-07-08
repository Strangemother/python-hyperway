"""Hyperway is left-associative, meaning the order of precedence for operations
occurs through sequential evaluation (from left to right).

Each operation is executed as it is encountered, without regard to the
traditional precedence of operators -

Therefore PEMDAS/BODMAS will not function as expected - graph chains execute linearly.

Standard:

    1 + 1 * 2 + 2 == 5
    10 + 1 * 2 + 2 == 24

Left-association:

    ( (1 + 1) * 2) + 2 == 6
    ( (10 + 1) * 2) + 2 == 24

"""
from hyperway.tools import factory as f
from hyperway.edges import make_edge, wire

c = make_edge(f.add_1, f.add_2, through=wire(f.mul_2))


assert c.pluck(1) == 10 # (1 + 1) * 2 + 2 == 6
assert c.pluck(10) == 24 # (10 + 1) * 2 + 2 == 24

