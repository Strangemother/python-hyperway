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

def com_oper(operator_func, *values):
    return operator_func(*reversed(values))

def oper(func, commute, *values):
    p = partial(func, *values)
    if commute:
        p = partial(com_oper, func, *values)

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


import operator as operator_mod


class Factory(object):
    """A operational caller for partials, built with parts of the function
    name,

    Define if _commutative_ for the operator values. If true subtract,
    and mutliply as reversed to ensure the noncommutative values are processed
    in logical order:

        >>> from hyperway.tools import Factory
        >>> f = Factory(False)
        >>> f.sub_1(10)
        -9.0

        >>> cf = Factory(True)
        >>> cf.sub_1(10)
        9.0
    """

    # Define if _commutative_ for the operator values.
    commute = False

    def __init__(self, commute=False):
        self.commute = commute

    def __getitem__(self, k):
        return self.__getattr__(k)

    def __getattr__(self, k):
        op_name, ival, *_ = k.split('_')
        operator_func = getattr(operator_mod, op_name)
        val = float(ival)
        return oper(operator_func, self.commute, val)


factory = Factory()