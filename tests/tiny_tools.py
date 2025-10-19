from hyperway.packer import argspack

def doubler(v, *args, **kwargs):
    """Wire function that doubles the value."""
    return argspack(v * 2, **kwargs)


def add_n(n):
    """Create a function that adds n to a value."""
    def adder(v):
        return v + n
    return adder

assert add_n(10)(5) == 15


def return_n(n):
    """Create a function that returns n."""
    def returner():
        return n
    return returner

assert return_n(5)() == 5

def passthrough(v=None):
    """Standard passthrough function - returns input or None."""
    return v

assert passthrough(20) == 20


# Module-level helper functions used across multiple tests
def noop():
    """No-op function that returns None."""
    return None

assert noop() is None



def pass_attribute_error(func, *a, **kw):
    try:
        return func(*a, **kw)
    except AttributeError:
        # Expected - resolve_node not implemented
        pass

def attribute_error_raiser(do_raise=False):
    if do_raise:
        raise AttributeError("Test AttributeError")
    return None 

assert pass_attribute_error(attribute_error_raiser, do_raise=True) == None
assert pass_attribute_error(attribute_error_raiser, do_raise=False) == None


import sys 

def delete_sys_module(name):
    if name in sys.modules:
        del sys.modules[name]

temp_name = 'sys_example_injection_name'
sys.modules[temp_name] = {}
assert temp_name in sys.modules
delete_sys_module(temp_name)
assert temp_name not in sys.modules

