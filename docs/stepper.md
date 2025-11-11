# Stepper

The stepper is the little machine that walks the graph of nodes. It executes and stores results as it progresses. 

An example graph:

```py
g = Graph(tuple)

def doubler(v=0):
    return v * 2


def collector(v):
    return v

du = as_unit(doubler)
e = g.add(du, collector)
e2 = g.add(du, collector)
```

To run a stepper, we must give it a starting node and any initial arguments.

```py
# continued from above
# We start at _some node_, with a value of 4
g.stepper_prepare(du, 4)
```

Now the stepper is ready to walk the graph, we can step through each node:

```py
stepper = g.stepper() # get the stepper instance
stepper.step() 
```

We can inspect the stepper stashed values at any time. When the stepper completes a path, the results are stored in the stash:

```py
stepper.step() # returns _the next step_
# ((<PartialConnection to Unit(func=collector)>, <ArgsPack(*(8,), **{})>),)

stepper.stash # nothing yet
# defaultdict(<class 'tuple'>, {})

stepper.step() # perform the waiting (next) step.
# C(0) "Unit(func=collector)"   # We hit the `collector` function
() # no next step

stepper.stash # We can see the result now
# defaultdict(<class 'tuple'>, {<PartialConnection to Unit(func=collector)>: (<ArgsPack(*(8,), **{})>,)})
```

That's it! It's that simple!

1. The stepper walks the graph one node at a time.
2. It executes the node, and stores the next step.
3. If there is no next step, it stores the result in the `stash`.

## Accessing Results

The stepper provides convenient methods to access results without manually unwrapping the stash structure.

### Simple Result Access

For the most common case - getting the final result value:

```python
g = Graph()
g.connect(f.add_10, f.add_20, f.add_30)

g.stepper_prepare(start_node, 10)
s = g.stepper()

# Execute the graph
while s.step():
    pass

# Get the result - simple!
result = s.get_result()  
print(result)  # 70
```

### Multiple Results

When your graph has multiple endpoints (branches), use `get_results()` to get all results as a list:

```python
# Graph with 2 endpoints
source = as_unit(f.mul_2)
g.add(source, f.add_10)  # Path 1: x * 2 + 10
g.add(source, f.add_20)  # Path 2: x * 2 + 20

g.stepper_prepare(source, 5)
s = g.stepper()

while s.step():
    pass

# Get all results
results = s.get_results()
print(results)  # [20, 30] (order may vary)
```

### Organized Results

For complex graphs with named handlers, organize results by node name:

```python
# Named handlers
handler_a = as_unit(f.add_100, name='handler_a')
handler_b = as_unit(f.add_200, name='handler_b')

g.add(source, handler_a)
g.add(source, handler_b)

g.stepper_prepare(source, 10)
s = g.stepper()

while s.step():
    pass

# Get results organized by name
results_dict = s.get_results_dict()
print(results_dict)
# {'handler_a': [120], 'handler_b': [220]}

# Access specific handler's results
handler_a_result = results_dict['handler_a'][0]
```

### Checking Results

Use `has_results()` and `result_count()` to check result availability:

```python
s = g.stepper()

if not s.has_results():
    print("No results yet")

while s.step():
    pass

if s.has_results():
    count = s.result_count()
    print(f"Execution complete with {count} results")
```

### Custom Organization

Organize results using custom keys (callable or attribute name):

```python
# By node ID
results_by_id = s.get_results_dict(key=lambda n: n.id())

# By function name
results_by_func = s.get_results_dict(key=lambda n: n.func.__name__)

# By custom attribute
results_by_type = s.get_results_dict(key='node_type')
```

### Convenience Method Reference

| Method | Use Case | Returns |
|--------|----------|---------|
| `get_result()` | Single result from single-endpoint graph | First result value or None |
| `get_results()` | All results as simple list | List of result values |
| `get_results_dict()` | Results organized by node | Dict of {node_key: [results]} |
| `has_results()` | Check if any results exist | Boolean |
| `result_count()` | Count total results | Integer |

### Advanced: Unwrapping Control

By default, results are automatically unwrapped from `ArgsPack` objects using the `.flat()` method. For advanced use cases, you can disable unwrapping:

```python
# Get raw ArgsPack objects
raw_results = s.get_results(unwrap=False)

for akw in raw_results:
    print(akw.args)  # Positional arguments tuple
    print(akw.kw)    # Keyword arguments dict
    
    # Or extract the natural representation
    value = akw.flat()  # Unwraps to most appropriate type
```

The `ArgsPack.flat()` method intelligently extracts values:
- Single arg → the value itself (`42`)
- Multiple args → tuple of args (`(1, 2, 3)`)
- Only kwargs → dict (`{'foo': 'bar'}`)
- Both args + kwargs → tuple of `(args, kwargs)`
- Empty → `None`



