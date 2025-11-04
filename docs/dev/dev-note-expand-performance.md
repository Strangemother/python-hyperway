# Dev Note: expand() implementation performance and memory

Date: 2025-10-18

This note documents the behavior and performance differences between two
implementations of the `expand` helper used by the stepper:

- `expand_tuple(items, second)`: builds the result by concatenating tuples in a loop
- `expand_list(items, second)`: builds the result using a list accumulator and
  converts to a tuple at the end

Both implementations return a tuple of rows shaped like:

```
((next_callable, argspack), (next_callable, argspack), ...)
```

The project now exposes both variants in `src/hyperway/stepper.py` and allows
selecting the global implementation at runtime via `set_global_expand`.
By default, the faster list-based variant is selected:

```
from hyperway.stepper import expand_tuple, expand_list, set_global_expand

# pick your preference:
set_global_expand(expand_list)  # default
# set_global_expand(expand_tuple)
```

## Why another implementation?

Tuple concatenation in a loop is O(n^2) over time due to tuple immutability and
reallocation on each `+=` append. A list accumulator is O(n) for appends and
simply converted to a tuple once at the end.

## Micro-benchmark: function-level expand()

Script: `workspace/bench_expand.py`

Datasets:
- flat_1k (1,000 items)
- flat_10k (10,000 items)
- nested_2k_x4 (2,000 items grouped in tuples of 4)
- mixed_10k (mixture of scalars and small tuples)

Timing results (lower is better):

```
dataset             tuple (s)     list (s)    speedup
------------------------------------------------------
flat_1k              0.001264     0.000101      12.57x
flat_10k             0.134642     0.001107     121.67x
nested_2k_x4         0.004996     0.000217      23.04x
mixed_10k            0.133779     0.001129     118.49x
```

Conclusion (micro): The list-based version is dramatically faster for larger
inputs because it avoids repeated tuple reallocations.

### Memory (tracemalloc) results

We also added a peak memory comparison using `tracemalloc` in the same script.
Representative output:

```
dataset            tuple best    list best      ratio       tuple avg     list avg      ratio
--------------------------------------------------------------------------------------------
flat_10k            705.7 KiB    708.3 KiB       1.00       705.7 KiB    708.3 KiB       1.00
nested_2k_x4        143.2 KiB    142.7 KiB       1.00       143.2 KiB    142.7 KiB       1.00
mixed_10k           705.7 KiB    704.2 KiB       1.00       705.7 KiB    704.2 KiB       1.00
```

Conclusion (memory): Peak memory is essentially the same for both approaches in
these tests. The final data structure dominates memory use; construction strategy
has negligible impact on peak usage in this context.

## Stepper benchmark: end-to-end

Script: `workspace/bench_stepper_expand.py`

We built a small branching graph and measured two full steps of the stepper,
toggling the global `expand` implementation via `set_global_expand`.

Results:

```
variant           seconds
--------------------------
tuple            0.000062
list             0.000057

Speedup (tuple/list): 1.10x
```

Conclusion (end-to-end): The list-based variant remains slightly faster in the
context of the stepper, but the difference is smaller (~10%) because the
stepper work includes function calls, graph lookups, and object handling that
reduce the relative cost of `expand` itself.

## Code references

- `src/hyperway/stepper.py`
  - `expand_tuple(items, second)` – original style (tuple concatenation)
  - `expand_list(items, second)` – list accumulator variant
  - `expand` – currently aliased to `expand_list`
  - `set_global_expand(expand_func)` – switch global implementation

- Benchmarks
  - `workspace/bench_expand.py` – micro-benchmark and memory comparison
  - `workspace/bench_stepper_expand.py` – end-to-end stepper benchmark

## Recommendations

- Keep `expand_list` as the default implementation (`expand = expand_list`).
- Retain `expand_tuple` for reference and for quick A/B testing.
- If future workloads exhibit different characteristics (e.g., extremely small
  datasets where the difference is noise, or heavy emphasis on nested call
  costs), this can be re-evaluated using the provided benchmarks.

## Future enhancements

- Parameterize the stepper benchmark to vary depth/width and number of steps.
- Add CI job to run the micro-benchmark with a coarse sanity threshold
  (non-blocking) to detect egregious regressions.
- Consider optional use of itertools/chain for nested cases if profiles suggest
  further gains without harming readability.
