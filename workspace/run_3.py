
from collections import defaultdict
import operator as op
from functools import partial
from pprint import pprint as pp

from hyperway.graph import Graph
from hyperway.stepper import run_stepper, StepperC
from hyperway.edges import Connection, as_connections, make_edge, get_connections
from hyperway.packer import argspack, test_argpack
from hyperway.graph import add, connect
from hyperway.nodes import Unit, as_unit
from hyperway.reader import read_linear_chain, read_tree_chain, flat_graph
from hyperway.generator import fully_connected

# import smoke_tests
# A bunch of test functions such as add_4
import hyperway.tools as t


primary_graph = Graph(tuple)
g = primary_graph

f = t.factory


def main():
    return run()


def run():
    g = Graph(tuple)

    g2 = Graph(tuple)
    g2.__name__ = 'graph2'
    cns2 = g2.connect(
        f.add_5,
        f.add_6,
        f.add_8,
        f.add_9,
        )

    ua4 = as_unit(g2)
    cns = g.connect(
        f.add_1,
        ua4,
        f.add_2,
        f.add_3,
        f.add_5,
        f.add_6,
        f.add_7,
        )


    g.write('run_3')
    g.stepper_prepare(cns[0].a, 1)
    # s = g.stepper()
    conns = get_connections(g, ua4)
    print(conns)
    return g


if __name__ == '__main__':
    g = main()