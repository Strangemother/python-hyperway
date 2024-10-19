from hyperway.edges import make_edge, as_unit


def foo():
    """Foo function accepts no arguments, and returns no arguments.

    Importantly, a python _no return_ is an implicit `return None`.
    """
    print('Foo')
    # return None

"""
Without a sentinal of `None`, the response value from `foo()` is given
to node B without tests.

However foo() does not accept the null args (or any for that matter).
So we can ensure this:

    var = *(), **{}
    var = foo(*var.a, **var.kw): return None
    var = foo(var): return None

becomes this:


    var = *(), **{}
    var = foo(*var.a, **var.kw): return None

    var = (*(), **{} ) if var is None else var

    var = foo(*var.a, **var.kw): return None

"""

c = make_edge(foo, as_unit(foo))

print(f'\n-- Plucking: {c} --\n')

try:
    c.pluck()
except TypeError as error:
    s = ("  ! Whoops!\n  ! Plucking arg-less connections without a sentinal"
         ", raised the following error:")
    print(f"\n{s}\n  ! \n  !", repr(error), '\n')

print('\n-- Again (with a sentinal) --')
c = make_edge(foo, as_unit(foo, sentinal=None))
c.pluck()
print('No errors occured.')