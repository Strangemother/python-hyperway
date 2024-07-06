
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
from hyperway.generator import fully_connected

# import smoke_tests
# A bunch of test functions such as add_4
import hyperway.tools as t

from hyperway.writer import set_graphviz
set_graphviz('./Graphviz-12.0.0-win64/bin/')


primary_graph = Graph(tuple)
g = primary_graph

f = t.factory


def main():
    return run()

def sum_f(*v):
    return sum(v[:-1]) / (v[-1] + 1)


def run():
    g = Graph(tuple)

    cns = fully_connected(
        sum_f,
        sum_f,
        sum_f,
        sum_f,
        sum_f,
        sum_f,
        sum_f,
        merge_node=True,
        )
    g.add_edges(cns)
    styles = {'bgcolor': '#111111'}
    # circo looks good for full-connect
    g.write('full-dark', engine='circo', styles=styles)
    g.stepper_prepare(cns[0].a, 1)
    s = g.stepper()
    s.concat_aware = True
    return g,s


if __name__ == '__main__':
    g,s = main()