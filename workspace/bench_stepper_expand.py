"""
Benchmark the Hyperway stepper using alternative expand strategies.

We toggle between expand_tuple and expand_list via set_global_expand and
measure the end-to-end stepper stepping time on a simple branching graph.
"""
import timeit

from hyperway.graph import Graph
from hyperway.nodes import as_unit
from hyperway.packer import argspack
from hyperway.stepper import expand_tuple, expand_list, set_global_expand


def make_graph():
    g = Graph(tuple)

    def source(v):
        return v * 2

    def branch_a(v):
        return v + 1

    def branch_b(v):
        return v + 2

    def branch_c(v):
        return v * 3

    n_source = as_unit(source)
    g.add(n_source, branch_a)
    g.add(n_source, branch_b)
    g.add(n_source, branch_c)

    # add a second layer to increase work
    n_a = as_unit(branch_a)
    n_b = as_unit(branch_b)
    n_c = as_unit(branch_c)

    g.add(n_a, branch_b)
    g.add(n_b, branch_c)
    g.add(n_c, branch_a)

    return g, n_source


def run_once(g, start_node, input_value):
    """Prepare stepper, execute two steps to propagate through graph."""
    g.stepper_prepare(start_node, input_value)
    stepper = g.stepper()
    stepper.step()  # first layer
    stepper.step()  # second layer
    # Return number of stashed results to avoid optimization away
    # (depends on implementation, but ensures side effects)
    return sum(len(v) for v in stepper.stash.values())


def bench_variant(expand_fn, g, start_node, value, repeat=5, number=200):
    set_global_expand(expand_fn)

    # Bind arguments for the timed callable
    def _call():
        return run_once(g, start_node, value)

    t = timeit.Timer(_call)
    best = min(t.repeat(repeat=repeat, number=number)) / number
    return best


def main():
    g, start_node = make_graph()
    value = 10

    t_tuple = bench_variant(expand_tuple, g, start_node, value)
    t_list = bench_variant(expand_list, g, start_node, value)

    print("Stepper expand() benchmark (lower is better)\n")
    print(f"{'variant':<12} {'seconds':>12}")
    print("-" * 26)
    print(f"{'tuple':<12} {t_tuple:12.6f}")
    print(f"{'list':<12} {t_list:12.6f}")

    speedup = (t_tuple / t_list) if t_list > 0 else float('inf')
    print(f"\nSpeedup (tuple/list): {speedup:.2f}x")


if __name__ == "__main__":
    main()
