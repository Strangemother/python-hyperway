# Kwargs Bubbling

Wire functions can pass metadata through the graph without polluting function signatures. This is _kwargs bubbling_ - setup kwargs flow through the pipeline in the `ArgsPack`, independent of runtime function calls.

## The Problem

Consider passing metadata through a graph pipeline:

```py
def add(x, y, **metadata):
    # Function forced to accept **metadata
    # even though it doesn't use it
    return x + y

def multiply(value, **metadata):
    # Every function needs **metadata
    return value * 2
```

This is noisy. Functions have to accept kwargs they don't use.

## Kwargs Bubbling

Wire functions separate runtime kwargs from pipeline metadata:

```py
from hyperway.edges import wire

def add(x, y):
    # Clean signature
    return x + y

def multiply(value):
    # No **kwargs noise
    return value * 2

# Setup wire with pipeline metadata
wire_add = wire(add, stage='sum', pipeline='data-transform')
wire_mul = wire(multiply, stage='amplify')
```

When called:

```py
result = wire_add(10, 20)
# Function receives: add(10, 20)
# ArgsPack contains: (30, stage='sum', pipeline='data-transform')
```

The metadata _bubbles_ through the `ArgsPack`, never touching the function signature.

## Call-time vs Setup-time

Two distinct flows:

**Call-time kwargs** → Go to the function
```py
def add_with_multiplier(x, y, multiplier=1):
    return (x + y) * multiplier

wire_func = wire(add_with_multiplier, pipeline='test')
result = wire_func(10, 20, multiplier=5)
# Function receives: add_with_multiplier(10, 20, multiplier=5)
# ArgsPack contains: (150, pipeline='test')
```

**Setup-time kwargs** → Bubble through `ArgsPack`
```py
wire_func = wire(add, stage='sum', meta='important')
result = wire_func(10, 20)
# Function receives: add(10, 20)
# ArgsPack contains: (30, stage='sum', meta='important')
```

## Usage in Graphs

This keeps graph pipelines clean while preserving metadata for debugging, logging, or conditional execution:

```py
from hyperway.edges import make_edge

g = Graph()

# Each wire carries stage metadata
edge1 = g.add(node_a, node_b, through=wire(transform, stage='normalize'))
edge2 = g.add(node_b, node_c, through=wire(validate, stage='check'))

# Metadata flows through without touching function signatures
g.stepper_prepare(node_a, initial_data)
stepper = g.stepper()

for rows in stepper:
    for caller, argpack in rows:
        # Access bubbled metadata
        print(f"Stage: {argpack.kwargs.get('stage')}")
```

## wire vs wire_partial

Both support kwargs bubbling:

**`wire`** - No pre-applied args, just metadata:
```py
wire_func = wire(my_function, pipeline='prod', version='2.0')
result = wire_func(x, y)  # Clean call
```

**`wire_partial`** - Pre-applied args AND result goes to function:
```py
wire_func = wire_partial(my_function, preset_arg, foo=2)
result = wire_func(runtime_arg, foo=5)  # foo=5 overrides foo=2
# Function receives all merged kwargs
```

## Key Insight

Kwargs bubbling separates concerns:
- **Function signature** = What the function needs to compute
- **Pipeline metadata** = What the graph needs to track

Functions stay clean. Metadata flows through. The graph stays debuggable.
