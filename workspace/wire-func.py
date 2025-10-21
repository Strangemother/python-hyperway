from hyperway.tools import factory as f
from hyperway.edges import make_edge
from hyperway.packer import argspack


c = make_edge(f.add_1, f.add_2, through=argspack)

def assert_equal(_in, a, b):
    assert a == b, f'in={_in} {a} != {b}'

def assert_pluck(c, _in, out):
    result = c.pluck(_in)
    assert_equal(_in, result, out)


assert_pluck(c, 1, 4)
assert_pluck(c, 5, 8)
assert_pluck(c, 10, 13)
assert_pluck(c, 77, 80)   

print('wire-func.py: All tests passed.')

def wire_func(v, *a, **kw):
    """Wire func example."""
    return argspack(v + 9, **kw)

c = make_edge(f.add_1, f.add_2, through=wire_func)

assert_pluck(c, 1, 13)
assert_pluck(c, 5, 17)
assert_pluck(c, 10, 22)
assert_pluck(c, 77, 89)

print('wire-func.py: All wire func tests passed.')

from hyperway.edges import wire as auto_wire_func
c = make_edge(f.add_1, f.add_2, through=auto_wire_func(f.mul_5))
assert_pluck(c, 1, 12)    # 1 + 1 = 2 * 5 = 10 + 2 = 12
assert_pluck(c, 2, 17)   # 2 + 1 = 3 * 5 = 15 + 2 = 17
assert_pluck(c, 3, 22)   # 3 + 1 = 4 * 5 = 20 + 2 = 22
assert_pluck(c, 4, 27)   # 4 + 1 = 5 * 5 = 25 + 2 = 27

print('wire-func.py: auto wire func tests passed.')
