
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
    # smoke_tests.main()
    return run()


class Printer:
    """In this example, we want to reference the print count.
    We _could_ globalise the var - but instead we generate an instance
    and supply a function to the graph.

        printer = Printer()
        g.add(f.add_4, printer.print_out)

    """
    print_count = 0
    def print_out(self, *a, **kw):
        # global print_count
        self.print_count += 1
        print(' -- print_out', self.print_count, a, kw)
        return (a, kw)


def run():
    # v = run_a()
    v = run_b()
    return v


def run_a():
    """
             +4
     i +2 +3      print
             +5

              10
     1  3  6      print
              11
    """
    printer = Printer()
    g = Graph(tuple)

    u_add_3 = as_unit(f.add_3)
    u_print = as_unit(printer.print_out)

    ca = g.add(f.add_2, u_add_3)
    g.connect(u_add_3, f.add_4, u_print)
    g.connect(u_add_3, f.add_5, u_print)

    g.stepper_prepare(ca.a, 1)
    s = g.stepper()
    s.step(count=4)

    print_count = printer.print_count
    assert print_count == 2, f"Fail, print_count == {print_count}"
    print('Good; two individual prints detected.')

    return g


def run_b():
    """
             +4
     i +2 +3      print
             +5

              10
     1  3  6      print
              11
    """
    printer = Printer()
    g = Graph(tuple)

    u_add_2 = as_unit(f.add_2)
    u_add_2.set_id(2)#hash(u_print))

    u_add_3 = as_unit(f.add_3)
    u_print = as_unit(printer.print_out)
    u_print.concat_input = True
    u_print.set_id(1)#hash(u_print))

    ca = g.add(u_add_2, u_add_3)
    g.connect(u_add_3, f.add_4, u_print)
    g.connect(u_add_3, f.add_5, u_print)

    g.stepper_prepare(ca.a, 1)
    s = g.stepper()
    s.step(count=4)

    # print_count = printer.print_count
    # assert print_count == 2, f"Fail, print_count == {print_count}"
    # print('Good; two individual prints detected.')

    return g


if __name__ == '__main__':
    g = main()