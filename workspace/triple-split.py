"""

Double

https://houseofgraphs.org/graphs/422

"""
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

from hyperway.writer import set_graphviz
set_graphviz('./Graphviz-12.0.0-win64/bin/')

f = t.factory
f.commute = True


def main():
    return run()


def forloop_stepper(stepper):
    try:
        for rows in stepper:
            print('-- result', rows)
    except StopIteration as e:
        print('-- Stop called: ', e)


def forloop_iterator(stepper):
    try:
        it = stepper.iterator()
        for rows in next(it):
            print('-- result', rows)
    except StopIteration as e:
        print('-- Stop called: ', e)


def while_step(stepper):
    rows = stepper.step()
    while len(rows) > 0:
        rows = stepper.step()
        print('Rows', rows)
    print('done', stepper.stash)


def run():
    g = Graph()

    split = as_unit(f.add_2)
    join = as_unit(f.add_2)

    cs = g.connect(f.add_1, split)
    g.connect(split, f.add_3, join)
    g.connect(split, f.add_4, join)
    g.connect(join, f.add_1)

    g.connect(join, f.sub_1)

    s = g.stepper(cs[0].a, 1)

    while_step(s)

    pp(s.stash)
    g.write('triple-split', directory='renders/', direction='LR')#, engine='neato')

    # print('---')
    # cr = read_linear_chain(g, cs[0].a)
    # print('linear chain', cr)

    # print('---')
    # result = run_stepper(g, con.a, 1)
    # print(result)

    return g #, s


if __name__ == '__main__':
    g = main()