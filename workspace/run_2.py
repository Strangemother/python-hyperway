"""
In this version we expand greatly, rather than relying upon a thin graph etc,
build the entire flow process, each unit is a complex object communicating events
to a graph stepper stash.

First lessen the algorithm:

Call from A to B through C with G

The result from B
"""
from collections import defaultdict
import operator as op
from functools import partial
from pprint import pprint as pp

from hyperway.stepper import run_stepper, StepperC
from hyperway.graph import Graph
from hyperway.edges import Connection, as_connections, make_edge, get_connections
from hyperway.packer import argspack, test_argpack
from hyperway.graph import add, connect
from hyperway.nodes import Unit, as_unit
from hyperway.reader import read_linear_chain, read_tree_chain, flat_graph

# A bunch of test functions such as add_4
import hyperway.tools as t

primary_graph = Graph(tuple)
g = primary_graph

f = t.factory


def main():
    return double_split()

def double_split():
    """A Cross topology
    """

    g = Graph(tuple)
    ua = as_unit(f.add_2)
    ub = as_unit(f['mul_.5'])
    uc = as_unit(f.add_3)

    ca = add(g, ua, ub)
    cb = add(g, ub, uc)
    cc = add(g, uc, ua)

    stepper = StepperC(g)
    res = stepper.prepare(ca.a, akw=argspack(1))

    # global p
    # p = read_tree_chain(g, ca.a)
    # print(' -- paths --')
    # pp(p)

    return stepper, res


if __name__ == '__main__':
    v = main()
