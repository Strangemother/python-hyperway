
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


def and_gate(a=0, b=0):
    print(f'Gate in: "{a}" "{b}"')
    out = a & b
    print('Gate out:', out)
    return out


def collector(v):
    return v


def store_gate(v):
    print('\nGate Value:', v, '\n')
    return v


def run():
    g = Graph(tuple)
    e = g.add(and_gate, store_gate)
    na = e.a
    na.merge_node = True

    # Two legs to the gate
    la = g.add(collector, na)
    lb = g.add(collector, na)

    # Assign 1,1 along the legs.
    g.stepper_prepare((la.a, lb.a), 1)
    # g.stepper_prepare(na, 1,1)

    # Ensure the stepper can perform concatenation
    s = g.stepper()
    s.concat_aware = True

    # g.write('and_gate')
    g.write('and_gate', engine='dot')

    s.step() # Step onto collectors with 1,1
    s.step() # Run the gate, storing 1
    s.step() # Print the result.

    # Read result

    print("\nResult:", dict(s.stash))
    return g, s

if __name__ == '__main__':
    g, s = main()