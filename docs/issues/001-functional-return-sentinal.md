# Functional Return Sentinal

A limitation of python:

```py
def foo_with_return():
    return None


def foo_with_pass():
    pass


val_r = foo_with_return()

if val_r:
    print('YES "foo_with_return" as a response')
    print(val_r)
else:
    print('NO repsonse from "foo_with_return"')


if val_r is None:
    print('"foo_with_return" IS None')
    print(val_r)
else:
    print('"foo_with_return" is not None')

print('---')

val_p = foo_with_pass()

if val_p:
    print('YES "foo_with_pass" as a response')
    print(val_p)
else:
    print('NO response from "foo_with_pass"')


if val_p is None:
    print('"foo_with_pass" IS None')
    print(val_p)
else:
    print('"foo_with_pass" is not None')
```

We see both functions resolve equally. Arguably the responses are not the same.
The solution _should_ be a sentinal value:

```py
class Sentinal:
    pass

sentinal = Sentinal()

val_r = foo_with_return() or sentinal
val_p = foo_with_return() or sentinal
```

Expectation:

+ `val_r` should be `None`
+ `val_p` should be `<sentinal>`

However both values are a `<sentinal>`.

---

This leads to an issue when processing a `Connection`

```py
c = as_edge(foo_with_pass, foo_with_pass)
```

as the steps to resolve:

```py
c.pluck() #Error, the section function receives None
```

This causes an error because:

```py
def pluck(self, *a, **kw):
    val:[ArgsPack|None] = c.get_a().process(*a, *kw)
    akw = argspack(val) # unfurls if required.
    # == (None,), {}
    val:[ArgsPack|None] = c.get_b().process(*akw.a, **akw.kw)

```


It's tempting to overcome this problem with a simple nully test:


```py
def pluck(self, *a, **kw):
    val:[ArgsPack|None] = c.get_a().process(*a, *kw)
    akw = argspack() # unfurls if required.
    if val is not None:
        akw = argspack(val) # unfurls if required.
    # == (None,), {}
    val:[ArgsPack|None] = c.get_b().process(*akw.a, **akw.kw)
```

But I dislike this, as it adds an extra test to every connection.
And if the second function _expects_ `None` as its first argument, this may lead to a bug:

```py
def b_func(value):
    if value is None:
        perform()
```

And this will not work with:

```py
def pluck(self, *a, **kw):
    val:[ArgsPack|None] = c.get_a().process(*a, *kw)
    akw = argspack() # unfurls if required.
    if val is not None:
        akw = argspack(val) # unfurls if required.
    # == (None,), {}
    val:[ArgsPack|None] = c.get_b().process(*akw.a, **akw.kw)
```

As the first argument set is `()` not `(None,)`.