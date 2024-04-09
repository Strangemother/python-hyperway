"""
In this version we expand greatly, rather than relying upon a thin graph etc,
build the entire flow process, each unit is a complex object communicating events
to a graph stepper stash.

First lessen the algorithm:

Call from A to B through C with G

The result from B
"""
from collections import defaultdict

import operator as op
from functools import partial
from pprint import pprint as pp

from .packer import test_argpack
from .stepper import run_stepper
from .graph import Graph
from .edges import Connection, as_connections, get_connections
from .edges import make_edge
from .packer import argspack
from .graph import add
from .nodes import Unit
from .nodes import as_unit
from .reader import read_linear_chain


primary_graph = Graph(tuple)
g = primary_graph


def add_1(v):
    res = v + 1
    print('! == add_1', res)
    return res

def add_10(v):
    res =  v + 10
    print('! == add_10', res)
    return res

def add_5(v):
    res = v + 5
    print('! == add_5', res)
    return res

def add_4(v):
    res = v + 4
    print('! == add_4', res)
    return res


def sub_4(v):
    res = v - 4
    print('! == sub_4', res)
    return res


def sub_10(v):
    res =  v - 10
    print('! == sub_10', res)
    return res

def double(v):
    res =  argspack(v * 2)
    print('! == double', res)
    return res


def main():
    """>py -i run.py

        (
            (<Unit(func=add_10)>,),
            (<function double at 0x00000000025EF9D0>,
             <Unit(func=add_4)>), (<Unit(func=sub_4)>,),
            (<Unit(func=double)>,),
            (<Unit(func=add_5)>,),
            (<Unit(func=sub_10)>,)
        )

        ---Run from A Unit(func=add_10) ArgsPack(*(1,), **{})
        ---

        xx - Get for Unit(func=add_10)
        Process input:  (1,) {}
        ! == add_10 11
        Process result: 11

        >>> r=v[0].call_rows(v[1])
        Calling through ...
        ! == double ArgsPack(*(22,), **{})
        Though result ArgsPack(*(22,), **{})
        Process input:  (22,) {}
        ! == add_4 26
        Process result: 26
        xx - Get for Unit(func=add_4)

        >>> r=v[0].call_rows(r)
        xx - Get for Unit(func=sub_4)
        Process input:  (26,) {}
        ! == sub_4 22
        Process result: 22

        >>> r=v[0].call_rows(r)
        Though result ArgsPack(*(22,), **{})
        Process input:  (22,) {}
        ! == double ArgsPack(*(44,), **{})
        Process result: ArgsPack(*(44,), **{})
        xx - Get for Unit(func=double)

        >>> r=v[0].call_rows(r)
        xx - Get for Unit(func=add_5)
        Process input:  (44,) {}
        ! == add_5 49
        Process result: 49

        >>> r=v[0].call_rows(r)
        Though result ArgsPack(*(49,), **{})
        Process input:  (49,) {}
        ! == sub_10 39
        Process result: 39
        xx - Get for Unit(func=sub_10)
        NO Connections for Unit "Unit(func=sub_10)"
         ... B connections end ... ArgsPack(*(39,), **{})

        >>>
    """
    quick_tests()
    oper_c = oper_tests()

    print('\n --- Operations Complete')


def oper(func, *values):
    p = partial(func, *values)
    p.__name__  = f"P_{func.__name__}"
    return p


def doubler(v, *a, **kw):
    print('!  Doubler In: ', v, a, kw)
    res = argspack(v * 2, **kw)
    print('!  Doubler Out:', res)
    return res


def divider(val):
    r = val * .5
    print('!  Dividing', val, ' == ', r)
    return r


def subtract(val):
    r = val - 5
    print('!  subtract 5: ', val, ' == ', r)
    return r


def oper_tests():
    c = add(primary_graph, oper(op.mul, .5), oper(op.add, 3))
    assert c.pluck(10) == 8
    assert c.pluck(100) == 53
    assert c.pluck(200) == 103
    print('Plucking of op functions complete.')
    return c


def quick_tests():
    test_argpack()
    c = make_edge(divider, subtract, through=doubler)
    res = c.pluck(100)
    assert res == 95.0
    res = c.pluck(50)
    assert res == 45.0
    print('-- tests complete -- ')


if __name__ == '__main__':
    v = main()