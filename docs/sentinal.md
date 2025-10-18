# Sentinal Values

In python the value of `None` is the same as _no value_.

```py
def func():
    return None
```

Is equivalent to:

```py
def func():
    return
``` 

However this can cause problem when chaining functions together. For example:

```py
def func_a():
    return # Shadow returns None

def func_b():
    # zero args expected
    return "egg" 

## Run chain example
value = func_a()
if value:
    func_b(value)
else:
    func_b()
# TypeError: func_b() takes 0 positional arguments but 1 was given
```

This occurs because `value` **is populated** with `None`, even though we don't explicitly return a value from `func_a`.

## Using Sentinal Values

To correct this, we apply a _sentinal_ value. A distinct object that is represents the absence of a value.

```py
_SENTINAL = object()    

def func_a():
    return _SENTINAL


def func_b():
    # no value given to this 
    return "egg" 

## Run chain example
value = func_a()
if value is not _SENTINAL:
    func_b(value)
else:
    func_b(func_a())
```

With this we can detect when a function has explicitly returned _no value_ and handle it accordingly.

## Sentinals in Hyperway

Because Hyperway chains together multiple functions, sentinal allows functions to explicitly return _no value_

When building a node, apply your preferred sentinal value:

```py
UNDEFINED = object() # considered a singleton.
def foo():
    return UNDEFINED 


unit = as_unit(foo, sentinal=UNDEFINED)
connection = make_edge(foo, unit)
```

When the node is executed, if `foo` returns `UNDEFINED`, Hyperway will treat this as _no value_ and will not pass it to downstream nodes.




