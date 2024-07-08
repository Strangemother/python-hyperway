
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
from hyperway.tools import factory as f

from hyperway.writer import set_graphviz
set_graphviz('./Graphviz-12.0.0-win64/bin/')

g = Graph()


def main():

    cs = g.connect(f.add_1, sum)
    sum_node = cs[0].b
    u = as_unit
    # d = {'directory': 'renders/'}
    # g.write('hyperway', **d)

if __name__ == '__main__':
    main()