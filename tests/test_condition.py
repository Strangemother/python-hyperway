
import operator as op
from functools import partial

from hyperway.graph import add, Graph
from hyperway.edges import make_edge
from hyperway.packer import argspack


def oper(func, *values):
    p = partial(func, *values)
    p.__name__  = f"P_{func.__name__}"
    return p


def doubler(v, *a, **kw):
    res = argspack(v * 2, **kw)
    return res


def divider(val):
    r = val * .5
    return r


def subtract(val):
    r = val - 5
    return r


def test_add_pluck():
    primary_graph = Graph(tuple)
    c = add(primary_graph, oper(op.mul, .5), oper(op.add, 3))
    assert c.pluck(10) == 8
    assert c.pluck(100) == 53
    assert c.pluck(200) == 103


def test_makeedge_pluck():
    c = make_edge(divider, subtract, through=doubler)
    res = c.pluck(100)
    assert res == 95.0
    res = c.pluck(50)
    assert res == 45.0