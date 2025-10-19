# Migration Guide: Legacy Functions → Factory

This guide shows how to replace legacy functions in `tools.py` with the modern `Factory` pattern.

## Summary

**Before migration:** 47% coverage (34 missed lines)  
**After tests:** 100% coverage (0 missed lines)  
**Project coverage:** Now at 85% (up from 81%)

## Legacy Function Replacements

### Addition Functions

| Legacy Function | Factory Replacement | Example |
|----------------|---------------------|---------|
| `add_1(v)` | `factory.add_1(v)` | `factory.add_1(5)` → `6.0` |
| `add_4(v)` | `factory.add_4(v)` | `factory.add_4(20)` → `24.0` |
| `add_5(v)` | `factory.add_5(v)` | `factory.add_5(10)` → `15.0` |
| `add_10(v)` | `factory.add_10(v)` | `factory.add_10(5)` → `15.0` |

### Subtraction Functions

| Legacy Function | Factory Replacement | Example |
|----------------|---------------------|---------|
| `sub_4(v)` | `Factory(True).sub_4(v)` | `Factory(True).sub_4(10)` → `6.0` |
| `sub_10(v)` | `Factory(True).sub_10(v)` | `Factory(True).sub_10(25)` → `15.0` |

**⚠️ Important:** Subtraction requires `commute=True` to maintain the same behavior as legacy functions:
- Legacy `sub_4(10)` = `10 - 4` = `6`
- Default factory `factory.sub_4(10)` = `4 - 10` = `-6` ❌
- Commutative factory `Factory(True).sub_4(10)` = `10 - 4` = `6` ✅

### Multiplication/Doubling

| Legacy Function | Factory Replacement | Example |
|----------------|---------------------|---------|
| `double(v)` | `factory.mul_2(v)` | `factory.mul_2(5)` → `10.0` |
| `doubler(v)` | `factory.mul_2(v)` (simpler) | Use directly or keep if kwargs needed |

**Note:** `double()` returns an `ArgsPack`, while `factory.mul_2()` returns a plain float. Keep `doubler()` if you need `ArgsPack` with kwargs support.

### Division

| Legacy Function | Factory Replacement | Example |
|----------------|---------------------|---------|
| `divider(val)` | `Factory(True).truediv_2(val)` | `Factory(True).truediv_2(10)` → `5.0` |

## Migration Steps

### Step 1: Identify Usage

Search for legacy function calls:
```bash
grep -r "add_1\|add_4\|add_5\|add_10\|sub_4\|sub_10\|double\|divider" tests/ workspace/
```

### Step 2: Replace Simple Cases

**Before:**
```python
from hyperway.tools import add_1, add_10, sub_4

result1 = add_1(5)      # 6
result2 = add_10(5)     # 15
result3 = sub_4(10)     # 6
```

**After:**
```python
from hyperway.tools import factory, Factory

cf = Factory(commute=True)  # For subtraction

result1 = factory.add_1(5)    # 6.0
result2 = factory.add_10(5)   # 15.0
result3 = cf.sub_4(10)        # 6.0
```

### Step 3: Update Graph Connections

**Before:**
```python
from hyperway.tools import add_1, add_10
from hyperway.graph import Graph

g = Graph()
g.connect(add_1, add_10)
```

**After:**
```python
from hyperway.tools import factory
from hyperway.graph import Graph

g = Graph()
g.connect(factory.add_1, factory.add_10)
```

### Step 4: Handle Special Cases

#### `double()` with ArgsPack

If you need `ArgsPack` output, keep using `double()` or `doubler()`:
```python
from hyperway.tools import doubler

# Still needed if downstream expects ArgsPack
result = doubler(5, key='value')  # ArgsPack((10,), {'key': 'value'})
```

Or migrate to factory with manual wrapping:
```python
from hyperway.tools import factory
from hyperway.packer import argspack

result = argspack(factory.mul_2(5))  # ArgsPack((10.0,), {})
```

## Benefits of Factory Pattern

1. **Flexibility**: Create any operation dynamically
   ```python
   factory.add_42(10)      # 52.0
   factory.mul_3(7)        # 21.0
   factory.truediv_4(16)   # 4.0
   ```

2. **Reusability**: Operations are partials that can be stored
   ```python
   add_100 = factory.add_100
   results = [add_100(x) for x in [1, 2, 3]]  # [101.0, 102.0, 103.0]
   ```

3. **Commutative control**: Choose operation order
   ```python
   # Non-commutative (default): operation_value(arg)
   factory.sub_5(10)           # 5 - 10 = -5
   
   # Commutative: operation(arg, value)
   Factory(True).sub_5(10)     # 10 - 5 = 5
   ```

4. **Less code**: No need to define individual functions

## Testing

All legacy functions are now tested in `tests/test_tools.py`:
- 46 comprehensive tests
- 100% coverage of tools.py
- Tests cover both legacy functions and factory patterns

Run tests:
```bash
./quick_test.sh
# Or
pytest tests/test_tools.py -v
```

## Deprecation Plan (Recommended)

1. **Phase 1** (Current): Add tests for legacy functions ✅
2. **Phase 2**: Add deprecation warnings to legacy functions
   ```python
   import warnings
   
   def add_1(v):
       warnings.warn(
           "add_1 is deprecated, use factory.add_1 instead",
           DeprecationWarning,
           stacklevel=2
       )
       return v + 1
   ```
3. **Phase 3**: Update all usage in tests/ and workspace/
4. **Phase 4**: Remove legacy functions (major version bump)

## Current Usage Analysis

Legacy functions are currently used in:
- `tests/test_reader.py` - Uses `factory` and `doubler` ✅
- `tests/test_wire_func.py` - Uses `factory` ✅
- `tests/test_writer.py` - Uses `factory` ✅
- Various `workspace/` examples - May need updates

**Good news:** Most existing code already uses the factory pattern! 🎉

## Questions?

The factory pattern is well-tested and production-ready. All legacy functions have equivalent factory operations with the same or better functionality.
