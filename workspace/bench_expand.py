"""
Benchmark expand() strategies: tuple-concat vs list-append.

We mirror the structure of src/hyperway/stepper.py:expand, but implement two
variants to measure performance:
- expand_tuple: builds the result via tuple concatenation in a loop
- expand_list: builds a list and converts to tuple at the end

Run this script to see which approach is faster across a few dataset shapes.
"""
from __future__ import annotations

import random
import timeit
import gc
import tracemalloc
from typing import Iterable, List, Sequence, Tuple, Union, Any

Item = Any  # stand-in for a "connection" object; here simple ints
ItemsType = Iterable[Union[Item, Sequence[Item]]]


def expand_tuple(items: ItemsType, second: Any) -> Tuple[Tuple[Item, Any], ...]:
    """Original style: tuple concatenation inside the loop."""
    res: Tuple[Tuple[Item, Any], ...] = ()
    for conn in items:
        if isinstance(conn, (tuple, list)):
            for c in conn:
                row = (c, second)
                res += (row,)
            continue
        row = (conn, second)
        res += (row,)
    return res


def expand_list(items: ItemsType, second: Any) -> Tuple[Tuple[Item, Any], ...]:
    """Optimized style: list append/extend, then convert to tuple at the end."""
    res_list: List[Tuple[Item, Any]] = []
    for conn in items:
        if isinstance(conn, (tuple, list)):
            # extend with a comprehension to avoid per-iteration tuple creation cost
            res_list.extend((c, second) for c in conn)
        else:
            res_list.append((conn, second))
    return tuple(res_list)


# Helpers to generate datasets -------------------------------------------------

def make_items_flat(n: int) -> list[int]:
    return list(range(n))


def make_items_nested(n_groups: int, group_size: int) -> list[tuple[int, ...]]:
    base = list(range(n_groups * group_size))
    return [tuple(base[i:i+group_size]) for i in range(0, len(base), group_size)]


def make_items_mixed(n: int, group_size: int, nested_ratio: float = 0.3) -> list[Union[int, tuple[int, ...]]]:
    items: list[Union[int, tuple[int, ...]]] = []
    i = 0
    while i < n:
        if random.random() < nested_ratio and i + group_size <= n:
            items.append(tuple(range(i, i + group_size)))
            i += group_size
        else:
            items.append(i)
            i += 1
    return items


# Verify functional equivalence ------------------------------------------------

def verify_equivalence():
    second = 42
    datasets = [
        ("flat_100", make_items_flat(100)),
        ("nested_50x4", make_items_nested(50, 4)),
        ("mixed_1000", make_items_mixed(1000, 5, 0.35)),
    ]
    for name, items in datasets:
        a = expand_tuple(items, second)
        b = expand_list(items, second)
        assert a == b, f"Mismatch on dataset {name}"


# Timing ----------------------------------------------------------------------

def run_benchmark():
    random.seed(1234)
    second = 42

    datasets = [
        ("flat_1k", make_items_flat(1_000), 5, 1000),
        ("flat_10k", make_items_flat(10_000), 3, 100),
        ("nested_2k_x4", make_items_nested(2_000 // 4, 4), 5, 300),
        ("mixed_10k", make_items_mixed(10_000, 5, 0.35), 3, 100),
    ]

    print("Benchmarking expand() variants (lower is better)\n")
    print(f"{'dataset':<16} {'tuple (s)':>12} {'list (s)':>12} {'speedup':>10}")
    print("-" * 54)

    for name, items, repeat, number in datasets:
        # bind args in closures so setup is excluded from timed body
        t_tuple = timeit.Timer(lambda it=items: expand_tuple(it, second))
        t_list = timeit.Timer(lambda it=items: expand_list(it, second))

        tt = min(t_tuple.repeat(repeat=repeat, number=number))
        tl = min(t_list.repeat(repeat=repeat, number=number))

        # normalize to per-call seconds
        tt /= number
        tl /= number

        speedup = tt / tl if tl > 0 else float("inf")
        print(f"{name:<16} {tt:12.6f} {tl:12.6f} {speedup:10.2f}x")


if __name__ == "__main__":
    verify_equivalence()
    run_benchmark()
    print()
    # Memory benchmark ------------------------------------------------------
    def peak_mem_bytes(func, items, second, repeats: int = 3):
        peaks = []
        for _ in range(repeats):
            gc.collect()
            tracemalloc.start()
            res = func(items, second)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            # drop reference to result before next iteration
            del res
            peaks.append(peak)
        # return best and average to reduce noise
        best = min(peaks)
        avg = sum(peaks) / len(peaks)
        return best, avg

    def fmt_bytes(n: int) -> str:
        # Display as KiB for readability
        return f"{n/1024:.1f} KiB"

    print("Memory peak (tracemalloc): tuple-concat vs list-append\n")
    print(f"{'dataset':<16} {'tuple best':>12} {'list best':>12} {'ratio':>10}    {'tuple avg':>12} {'list avg':>12} {'ratio':>10}")
    print("-" * 92)

    mem_datasets = [
        ("flat_10k", make_items_flat(10_000)),
        ("nested_2k_x4", make_items_nested(2_000 // 4, 4)),
        ("mixed_10k", make_items_mixed(10_000, 5, 0.35)),
    ]
    second = 42
    for name, items in mem_datasets:
        t_best, t_avg = peak_mem_bytes(expand_tuple, items, second)
        l_best, l_avg = peak_mem_bytes(expand_list, items, second)
        ratio_best = (t_best / l_best) if l_best else float('inf')
        ratio_avg = (t_avg / l_avg) if l_avg else float('inf')
        print(
            f"{name:<16} {fmt_bytes(t_best):>12} {fmt_bytes(l_best):>12} {ratio_best:10.2f}    "
            f"{fmt_bytes(int(t_avg)):>12} {fmt_bytes(int(l_avg)):>12} {ratio_avg:10.2f}"
        )
