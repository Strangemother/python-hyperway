from functools import partial

from .packer import argspack


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


def oper(func, *values):
    p = partial(func, *values)
    p.__name__  = f"P_{func.__name__}_{values[0]}"
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


import operator


class Factory(object):
    """A operational caller for partials, built with parts of the function
    name,
    """

    def __getitem__(self, k):
        return self.__getattr__(k)

    def __getattr__(self, k):
        op_name, ival, *extra = k.split('_')
        func = getattr(operator, op_name)
        val = float(ival)
        # oper(op.mul, .5)
        return oper(func, val)


factory = Factory()