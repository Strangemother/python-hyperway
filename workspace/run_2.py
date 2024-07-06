
from collections import defaultdict
import operator as op
from functools import partial
from pprint import pprint as pp

from hyperway.stepper import run_stepper, StepperC
from hyperway.graph import Graph
from hyperway.edges import Connection, as_connections, make_edge, get_connections
from hyperway.graph import add, connect
from hyperway.nodes import Unit, as_unit
from hyperway.reader import read_linear_chain, read_tree_chain, flat_graph

# import smoke_tests
import hyperway.tools as t

primary_graph = Graph(tuple)
g = primary_graph

f = t.factory


def main():
    return run()


def run():
    g = Graph(tuple)
    #            I ->  [ conn  ][ conn  ][ conn  ][ conn  ] -> O
    cs = g.connect(f.add_9, f.add_8, f.add_7, f.add_6, f.add_5)
    cs2 = g.connect(f.add_1, f.add_2, f.add_3, f.add_4, f.add_5)
    e = g.add(cs[2].a, cs2[0].a)

    # g.stepper_prepare(cs[0].a, 4)
    # g.stepper_prepare(na, 1,1)

    # Ensure the stepper can perform concatenation
    # s = g.stepper()

    g.write('run_2')#, engine='neato')

    return g #, s


if __name__ == '__main__':
    g = main()