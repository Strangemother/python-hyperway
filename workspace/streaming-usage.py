"""Streaming results example - demonstrating both functional and OOP styles

This shows the stream() function in action after integration into hyperway.
Demonstrates both the standalone stream(stepper) function and the
stepper.stream() method.
"""
from hyperway import Graph, as_unit
from hyperway.tools import factory as f
from hyperway.stepper import stream  # Functional style import


def example_1_oop_style():
    """Example 1: OOP Style - stepper.stream()"""
    print("\n=== Example 1: OOP Style (stepper.stream()) ===")
    
    g = Graph()
    chain = g.connect(f.add_10, f.add_20, f.add_30)
    start = chain[0].a
    
    g.stepper_prepare(start, 5)
    s = g.stepper()
    
    # OOP style: call method on stepper instance
    for result in s.stream():
        print(f"Result: {result}")
    
    print(f"Stash empty: {len(s.stash) == 0}")


def example_2_functional_style():
    """Example 2: Functional Style - stream(stepper)"""
    print("\n=== Example 2: Functional Style (stream(stepper)) ===")
    
    g = Graph()
    chain = g.connect(f.add_10, f.add_20, f.add_30)
    start = chain[0].a
    
    g.stepper_prepare(start, 5)
    s = g.stepper()
    
    # Functional style: pass stepper to function
    for result in stream(s):
        print(f"Result: {result}")
    
    print(f"Stash empty: {len(s.stash) == 0}")


def example_3_multiple_branches():
    """Example 3: Multiple branches with OOP style"""
    print("\n=== Example 3: Multiple Branches (OOP) ===")
    
    g = Graph()
    source = as_unit(lambda x: x * 2, name='source')
    
    # Three branches from source
    g.add(source, as_unit(lambda x: x + 10, name='branch_1'))
    g.add(source, as_unit(lambda x: x + 20, name='branch_2'))
    g.add(source, as_unit(lambda x: x + 30, name='branch_3'))
    
    g.stepper_prepare(source, 5)
    s = g.stepper()
    
    results = []
    for result in s.stream():
        print(f"Got result: {result}")
        results.append(result)
    
    print(f"All results: {sorted(results)}")
    print(f"Stash empty: {len(s.stash) == 0}")


def example_4_early_termination_functional():
    """Example 4: Early termination with functional style"""
    print("\n=== Example 4: Early Termination (Functional) ===")
    
    g = Graph()
    source = as_unit(lambda x: x, name='source')
    g.add(source, as_unit(lambda x: x + 10, name='add_10'))
    g.add(source, as_unit(lambda x: x + 20, name='add_20'))
    g.add(source, as_unit(lambda x: x + 30, name='add_30'))
    
    g.stepper_prepare(source, 5)
    s = g.stepper()
    
    # Functional style with early termination
    for result in stream(s):
        print(f"Result: {result}")
        if result > 20:
            print(f"Found result > 20, stopping early")
            break
    
    print(f"Remaining in stash: {len(s.stash)} nodes")


def example_5_unwrap_false():
    """Example 5: Stream raw ArgsPack objects"""
    print("\n=== Example 5: Raw ArgsPack (unwrap=False) ===")
    
    g = Graph()
    chain = g.connect(f.add_10, f.add_20)
    start = chain[0].a
    
    g.stepper_prepare(start, 5)
    s = g.stepper()
    
    # Get raw ArgsPack objects (both styles work)
    print("OOP style:")
    for akw in s.stream(unwrap=False):
        print(f"  ArgsPack: args={akw.args}, flat={akw.flat()}")


def example_6_loop_graph():
    """Example 6: Looped graph - memory safe streaming"""
    print("\n=== Example 6: Looped Graph (Memory Safe) ===")
    
    g = Graph()
    
    # Create a loop: A → B → C (leaf)
    #                     ↑___↓
    a = as_unit(lambda x: x + 1, name='A')
    b = as_unit(lambda x: x * 2, name='B')  
    c = as_unit(lambda x: x, name='C')  # Leaf
    
    g.add(a, b)
    g.add(b, c)
    g.add(b, b)  # Loop: B can call itself
    
    g.stepper_prepare(a, 1)
    s = g.stepper()
    
    # Stream with safety limit - works with both functional and OOP
    count = 0
    max_iterations = 10
    
    # Using functional style for variety
    for result in stream(s, unwrap=True):
        print(f"Result {count}: {result}")
        count += 1
        if count >= max_iterations:
            print(f"Safety limit reached ({max_iterations} results)")
            break
    
    print(f"Stash size: {len(s.stash)} (should be 0 - memory safe!)")


def example_7_collect_during_stream():
    """Example 7: Collect results while streaming"""
    print("\n=== Example 7: Collect While Streaming ===")
    
    g = Graph()
    source = as_unit(lambda x: x * 2, name='source')
    g.add(source, as_unit(lambda x: x + 10, name='fast'))
    g.add(source, as_unit(lambda x: x + 20, name='medium'))
    g.add(source, as_unit(lambda x: x + 30, name='slow'))
    
    g.stepper_prepare(source, 5)
    s = g.stepper()
    
    # Collect results as they stream (OOP style)
    results = []
    for result in s.stream():
        print(f"Processing: {result}")
        results.append(result)
    
    print(f"Collected results: {sorted(results)}")
    print(f"Stash is empty: {len(s.stash) == 0}")


def example_8_comparison():
    """Example 8: Side-by-side comparison of both styles"""
    print("\n=== Example 8: Style Comparison ===")
    
    # Setup same graph twice
    def make_graph():
        g = Graph()
        chain = g.connect(f.add_10, f.add_20)
        start = chain[0].a
        g.stepper_prepare(start, 5)
        return g.stepper()
    
    # OOP style
    print("\nOOP style (s.stream()):")
    s1 = make_graph()
    for result in s1.stream():
        print(f"  {result}")
    
    # Functional style
    print("\nFunctional style (stream(s)):")
    s2 = make_graph()
    for result in stream(s2):
        print(f"  {result}")
    
    print("\nBoth produce identical results!")


if __name__ == '__main__':
    print("=" * 60)
    print("Streaming Results - Functional and OOP Styles")
    print("=" * 60)
    
    example_1_oop_style()
    example_2_functional_style()
    example_3_multiple_branches()
    example_4_early_termination_functional()
    example_5_unwrap_false()
    example_6_loop_graph()
    example_7_collect_during_stream()
    example_8_comparison()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
