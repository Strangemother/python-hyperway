
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

# import smoke_tests
# A bunch of test functions such as add_4
import hyperway.tools as t


primary_graph = Graph(tuple)
g = primary_graph

f = t.factory


def main():
    return run()


def doubler(v=0):
    return v * 2


def collector(v):
    return v


def run():
    g = Graph(tuple)

    du = as_unit(doubler)
    e = g.add(du, collector)
    e2 = g.add(du, collector)

    g.stepper_prepare(du, 4)
    # g.stepper_prepare(na, 1,1)

    # Ensure the stepper can perform concatenation
    s = g.stepper()

    g.write('simple', engine='dot')

    s.step() # call the doubler, yielding two outbound results
    s.step() # call the collector, storing two results.
    pp(dict(s.stash))
    return g, s


if __name__ == '__main__':
    g, s = main()