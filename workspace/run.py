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


from hyperway.stepper import run_stepper, StepperC
from hyperway.graph import Graph
from hyperway.edges import Connection, as_connections, make_edge, get_connections
from hyperway.packer import argspack, test_argpack
from hyperway.graph import add, connect
from hyperway.nodes import Unit, as_unit
from hyperway.reader import read_linear_chain, read_tree_chain

# import smoke_tests
# A bunch of test functions such as add_4
import hyperway.tools as t

primary_graph = Graph(tuple)
g = primary_graph

f = t.factory


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
    # return chain_example_add_func() # == 39
    chain_example_chain_func() # == 39

    # smoke_tests.main()
    # main_b()
    # return main_c()
    # return main_d()
    return triple_split()

def double_split():
    """A Cross topology
    """

    g = Graph(tuple)
    cs = connect(g,
        f.mul_2,
        f.add_2, # split here
        f.mul_3,
        f.truediv_10,
        f['mul_.5'],
        f.sub_10,
        f.mul_3,
        )

    cs2 = connect(g,
        cs[1].a,
        f.add_5,
        f.mul_2,
        f.add_8,
        f.sub_100,
        f['mul_4'],
        f.truediv_3,
        )

    stepper = StepperC(g)
    res = stepper.prepare(cs[0].a, akw=argspack(4))

    global p
    p = read_tree_chain(g, cs[0].a)
    print(' -- paths --')
    pp(p)

    return stepper, res

def triple_split():
    g = Graph(tuple)
    cs = connect(g,
        f.mul_2,
        f.add_2, # split here
        f.mul_3,
        f.truediv_10,
        f['mul_.5'],
        f.sub_10,
        f.mul_3,
        )

    cs2 = connect(g,
        cs[1].a,  # f.add_2
        f.add_5,
        f.mul_12,
        f.add_88,
        f.sub_100,
        f['mul_4'],
        f.truediv_3,
        )
    cs3 = connect(g,
        cs2[2].b,
        f.sub_50,
        f['mul_2'],
        f.add_7,
        through=t.doubler)

    cs4 = connect(g,
        cs2[3].a,
        f.add_2,
        through=t.doubler)

    cs5 = connect(g,
        cs4[0].b,
        f.add_10,
        through=t.doubler)

    stepper = StepperC(g)
    res = stepper.prepare(cs[0].a, akw=argspack(4))

    global p
    p = read_tree_chain(g, cs[0].a)#, with_through=False)
    print(' -- paths --')
    pp(p, indent=4)

    return stepper, res



def main_d():

    g = Graph(tuple)
    cs = connect(g,
        f.mul_2,
        f['add_2'],
        f['truediv_3'],
        f['mul_.8'],
        f['sub_5'], # 5 - v
        f['mul_.5'],
        )

    # chain: 4 * 2 + 2 / 3 * .8 - 5 * 5
    orig_v = 4
    #real:
    v = orig_v
    v = 2.0 * v
    v = 2.0 + v
    v = 3.0 / v
    v = 0.8 * v
    v = 5.0 - v
    v = 0.5 * v
    print(v)

    cr = read_linear_chain(g, cs[0].a)
    print(cr)

    stepper = StepperC(g)
    res = stepper.start(cs[0].a, akw=argspack(orig_v))
    return stepper, res


def main_c():
    print('Run C')
    g = Graph(tuple)
    # A chain
    ## 1 + [1 + 2 + 3 + 4 + 5 + 6]
    ## == 22
    # B Chain Split:
    # 1+[1+2]+[7+10+11+12]
    # == 44

    # cs = _add_func(g)
    cs = _connect_func(g)

    ca = cs[0]
    b = cs[0].b

    # _add_from(g, b)
    _chain_from(g, b)

    pp(g)
    cr = read_linear_chain(g, ca.a)
    print(cr)

    global c_g
    c_g = g
    res = run_stepper(g, ca.a, argspack(1)) # divider(100)
    return res


def main_b():
    c_a = add(g, t.divider, t.subtract, through=t.doubler)
    c_c = add(primary_graph, t.oper(op.mul, .5), t.oper(op.add, 3))
    c_b = add(g, c_a.b, c_c.a)

    # c_a.a   -> doubler -> c_a.b    -> c_b.a       -> c_c.a  -> c_c.b
    # divider -> doubler -> subtract ->> [subtract] -> op_mul -> op_add

    pp(g)
    cr = read_linear_chain(g, c_a.a) # divider
    cr2 = read_linear_chain(g, c_b.b) # subtract
    print(cr)
    print(cr2)

    # (
        # (<Unit(func=divider)>,),
        # (<function doubler at 0x00000000025B2B80>,
        #   <Unit(func=subtract)>),
        # (<Unit(func=P_mul)>,),
        # (<Unit(func=P_add)>,)
    # )

    res = run_stepper(g, c_a.a, argspack(100)) # divider(100)
    return res



def _connect_func(g):
    cs = connect(g,
        f.add_1,
        f.add_2,
        f.add_3,
        f.add_4,
        f.add_5,
        f.add_6,
    )
    return cs


def _add_func(g):
    _add = partial(add, g)
    a = as_unit(f.add_1)
    b = as_unit(f.add_2)
    c = as_unit(f.add_3)
    d = as_unit(f.add_4)
    e = as_unit(f.add_5)
    _f = as_unit(f.add_6)

    return (
        _add(a, b),
        _add(b, c),
        _add(c, d),
        _add(d, e),
        _add(e, _f),
    )


def _add_from(g, node):
    _add = partial(add, g)

    c2 = as_unit(f.add_7)
    d2 = as_unit(f.add_10)
    e2 = as_unit(f.add_11)
    f2 = as_unit(f.add_12)

    return (
        _add(node, c2), #, through=t.doubler)
        _add(c2, d2),
        _add(d2, e2),
        _add(e2, f2),
    )


def _chain_from(g, node):
    _add = partial(add, g)

    return connect(g,
        node,
        f.add_7,
        f.add_10,
        f.add_11,
        f.add_12,
        )


def chain_example_add_func():
    print('\n --- Run chain example ---\n')
    g = Graph(tuple)

    ## Here we cast the functions as Unit instances,
    # allowing us to re-user their reference. without referring to nodes
    # from within the connection.
    du = as_unit(t.double)
    add_4_u = as_unit(t.add_4)
    sub_4_u = as_unit(t.sub_4)
    add_5_u = as_unit(t.add_5)

    # Connection                   A to B
    ca = add(g, t.add_10, add_4_u, through=t.double)
    # Connect (above)              B to C
    cd = add(g, add_4_u, sub_4_u)
    cb = add(g, sub_4_u, du)     # D to E...
    cc = add(g, du, add_5_u)     # E -> F
    cd = add(g, add_5_u, t.sub_10) # F -> G

    ## This should result in a chain of int editors:
    #
    # 1  +10  *2   +4  -4   *2   +5   -10
    #     11  22  26   22   44   49   39

    # Present the functions including thr `doubler` wire function
    cr = read_linear_chain(g, ca.a)
    print(cr)
    # (
        # (<Unit(func=divider)>,),
        # (<function doubler at 0x00000000025B2B80>,
        #   <Unit(func=subtract)>),
        # (<Unit(func=P_mul)>,),
        # (<Unit(func=P_add)>,)
    # )

    # Call A: add_10(1) ...
    res = run_stepper(g, ca.a, argspack(1)) # divider(100)

    ## Continue with a recursive caller:
    # stepper, rows = res
    # ...
    #   rows = stepper.call_rows(rows)
    return res


def chain_example_chain_func():
    print('\n --- Run chain example ---\n')
    g = Graph(tuple)

    cs = connect(g, t.add_10, t.add_4, through=t.double)
    ca = cs[0]
    connect(g, ca.b, t.sub_4, t.double, t.add_5, t.sub_10)

    cr = read_linear_chain(g, ca.a)
    res = run_stepper(g, ca.a, argspack(1))
    return res


if __name__ == '__main__':
    v = main()