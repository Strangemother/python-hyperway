
from collections import defaultdict
import operator as op
from functools import partial
from pprint import pprint as pp

from hyperway.stepper import run_stepper, StepperC
from hyperway.graph import Graph
# from hyperway.edges import Connection, as_connections, make_edge, get_connections
# from hyperway.packer import argspack, test_argpack
# from hyperway.graph import add, connect
from hyperway.nodes import Unit, as_unit
# from hyperway.reader import read_linear_chain, read_tree_chain, flat_graph

# import smoke_tests
# A bunch of test functions such as add_4
import hyperway.tools as t

from hyperway.writer import set_graphviz
set_graphviz('./Graphviz-12.0.0-win64/bin/')


primary_graph = Graph()
g = primary_graph

f = t.factory


def main():
    g = Graph()
    cs = g.connect(f.add_1, sum)
    # connections      | - 0 - | | - 1 - | | - 2 - |
    cs2 = g.connect(f.add_1, f.add_2, f.add_3)
    cs3 = g.connect(cs[0].a, f.add_4, cs[0].b,  cs2[1].b)
    cs4 = g.connect(cs2[0].a, cs[0].b)

    d = {'directory': 'renders/'}
    g.write('hyperway-neato-default', **d, engine='neato')
    g.write('hyperway-neato-horiz', **d, direction='LR')
    g.write('hyperway', **d)
    g.write('hyperway-fdp', **d, engine='fdp') # force-directed placement
    g.write('hyperway-twopi', **d, engine='twopi') # two pi
    return g #, s


if __name__ == '__main__':
    g = main()