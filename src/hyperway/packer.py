
UNDEFINED = {}

def merge_akws(*akws):
    """Convert all given akw instances into one.
    """
    r = ArgsPack()
    for akw in akws:
        r.args += akw.args
        r.kwargs.update(r.kwargs)
    return r


def argpack(result=UNDEFINED, *more, **extra):
    """Given a result from a unit process(), convert to a chainable (a, kw)
    arg set, allowing the expansion of results arbitrarily.

        akw = argpack(  argpack(a, b, c=d, e=f)  )
        akw = argpack(a, b, c=d, e=f)
        akw = argpack(a)

        akw = argpack(
            ( (), {} )
        )

    # Calling

    Use an argpack as a parts:


        akw = argpack(1, True, 'egg', foo="bar", baz=False)
        res = some_function(*akw.args, **akw.kwargs)
        akw2 = argspack(res)

    # Info

    The _result_ given from a previous call `argpack(some_function(foo=1))`
    Is minimally tested. The _result_ should be IO as expected:

        akw = some_function(1)
        akw.args[0] # The single result.

    The only caveat is the exact structure:

        akw = some_function(1)
        # ( (), {} )  # tuple ( tuple, dict )
    """
    if isinstance(result, ArgsPack):
        return result

    pre_a = () if result is UNDEFINED else (result,)
    a = pre_a + more
    kw = extra

    if isinstance(result, (tuple, list,)):
        if isinstance(result[0], (list, tuple,)):
            if isinstance(result[1], (dict, )):
                # is ((), {})
                a, kw = result

    return ArgsPack(*a, **kw)


argspack = argpack


def test_argpack():

    a = (1,3,4,5)
    d = {'foo': 3, 'bar': 4}
    
    v = argpack(argpack(a, **d))
    assert a == v.args[0]
    assert d == v.kwargs

    v = argpack( (a, d) )
    assert a == v.args
    assert d == v.kwargs

    print('Nice.')
    return True


class ArgsPack(object):

    def __init__(self, *a, **kw):
        self.args = a
        self.kwargs = kw

    @property
    def a(self):
        return self.args

    @property
    def kw(self):
        return self.kwargs
    
    def get(self, key, default=None):
        return self.kwargs.get(key, default)

    def flat(self):
        """Extract the most natural representation from this ArgsPack.
        
        Returns:
            - Single positional arg: the value itself
            - Multiple positional args: tuple of args
            - Only kwargs: dict
            - Both args and kwargs: tuple of (args, kwargs)
            - Nothing: None
        
        Example:
            >>> akw = argspack(42)
            >>> akw.flat()
            42
            >>> akw = argspack(1, 2, 3)
            >>> akw.flat()
            (1, 2, 3)
            >>> akw = argspack(foo='bar')
            >>> akw.flat()
            {'foo': 'bar'}
        """
        has_args = bool(self.args)
        has_kw = bool(self.kwargs)
        
        if has_args and has_kw:
            # Both exist - return both as tuple
            args_val = self.args[0] if len(self.args) == 1 else self.args
            return (args_val, self.kwargs)
        
        if has_args:
            return self.args[0] if len(self.args) == 1 else self.args
        
        if has_kw:
            return self.kwargs
        
        return None

    def __str__(self):
        return self.as_str()

    def __repr__(self):
        return f"<{self.as_str()}>"

    def as_str(self):
        return f"{self.__class__.__name__}(*{self.args}, **{self.kwargs})"
