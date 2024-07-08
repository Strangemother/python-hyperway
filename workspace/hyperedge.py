
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


def manual_stepped(stepper):
    v = stepper.step()
    print('1: ', v)
    v = stepper.step()
    print('2: ', v)
    v = stepper.step()
    print('3: ', v)
    v = stepper.step()
    print('4: ', v)
    v = stepper.step()
    print('5: ', v) #empty.

    ## overstep will result in a restart, #but the stash remains untouched.
    v = stepper.step()
    print('6: ', v)
    v = stepper.step()
    print('7: ', v)



def while_step(stepper):
    rows = stepper.step()
    while len(rows) > 0:
        rows = stepper.step()
        print('Rows', rows)
    print('done', stepper.stash)


def run():
    g = Graph()
                # 1 + 9 + 8 - 12 + 6 - 3 == 9
    cs = g.connect(f.add_9, f.add_8, f.sub_12, f.add_6, f.sub_3)
    con = cs[0]
    con.b = (con.b, as_unit(f.add_4),)
    cs2 = g.connect(f.add_6, f.add_5)

    stepper = g.stepper(con.a, 1)
    print('Stepper: ', stepper)

    while_step(stepper)
    # manual_stepped(stepper)
    # forloop_stepper(stepper)
    pp(stepper.stash)

    # g.write('hyperedge', direction='LR')#, engine='neato')

    # print('---')
    # cr = read_linear_chain(g, cs[0].a)
    # print('linear chain', cr)

    # print('---')
    # result = run_stepper(g, con.a, 1)
    # print(result)

    return g #, s


if __name__ == '__main__':
    g = main()