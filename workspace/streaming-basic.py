"""Basic streaming example - testing stream() method before integration

This demonstrates the proposed stream() method behavior using a standalone
implementation before we add it to StepperC.
"""
from hyperway import Graph, as_unit
from hyperway.tools import factory as f


def stream(stepper, unwrap=True):
    """Standalone stream implementation for testing.
    
    This is a prototype of the proposed StepperC.stream() method.
    Once validated, this will be added to the StepperC class.
    """
    ok = 1 
    while ok:
        # Execute one step
        rows = stepper.step()
        
        # Check if any new results appeared in stash
        if len(stepper.stash) == 0:
            continue

        # Pop all current results from stash (use .pop() for efficiency)
        # Create snapshot of nodes to avoid dict size change during iteration
        for node in tuple(stepper.stash.keys()):
            # Pop the entire tuple of results for this node
            akw_tuple = stepper.stash.pop(node)
            
            # Yield each result for this node
            for akw in akw_tuple:
                value = akw.flat() if unwrap else akw
                yield value
        
        # Stop when no more rows to process
        ok = len(rows)
        if not ok:
            break


def example_1_simple_linear():
    """Example 1: Simple linear graph"""
    print("\n=== Example 1: Simple Linear Graph ===")
    
    g = Graph()
    chain = g.connect(f.add_10, f.add_20, f.add_30)
    start = chain[0].a
    
    g.stepper_prepare(start, 5)
    s = g.stepper()
    
    # Stream results as they complete
    for result in stream(s):
        print(f"Result: {result}")
    
    # Verify stash is empty after streaming
    print(f"Stash after streaming: {dict(s.stash)}")
    assert len(s.stash) == 0, "Stash should be empty!"


def example_2_multiple_branches():
    """Example 2: Graph with multiple endpoints"""
    print("\n=== Example 2: Multiple Branches ===")
    
    g = Graph()
    source = as_unit(lambda x: x * 2, name='source')
    
    # Three branches from source
    g.add(source, as_unit(lambda x: x + 10, name='branch_1'))
    g.add(source, as_unit(lambda x: x + 20, name='branch_2'))
    g.add(source, as_unit(lambda x: x + 30, name='branch_3'))
    
    g.stepper_prepare(source, 5)
    s = g.stepper()
    
    results = []
    for result in stream(s):
        print(f"Got result: {result}")
        results.append(result)
    
    print(f"All results: {sorted(results)}")
    assert len(s.stash) == 0, "Stash should be empty!"


def example_3_early_termination():
    """Example 3: Early termination"""
    print("\n=== Example 3: Early Termination ===")
    
    g = Graph()
    
    # Create a chain that produces multiple values
    source = as_unit(lambda x: x, name='source')
    g.add(source, as_unit(lambda x: x + 10, name='add_10'))
    g.add(source, as_unit(lambda x: x + 20, name='add_20'))
    g.add(source, as_unit(lambda x: x + 30, name='add_30'))
    
    g.stepper_prepare(source, 5)
    s = g.stepper()
    
    # Stop after first result > 20
    for result in stream(s):
        print(f"Result: {result}")
        if result > 20:
            print(f"Found result > 20, stopping early")
            break
    
    # Stash may still have results if we stopped early
    print(f"Remaining in stash: {len(s.stash)} nodes")


def example_4_unwrap_false():
    """Example 4: Stream raw ArgsPack objects"""
    print("\n=== Example 4: Raw ArgsPack (unwrap=False) ===")
    
    g = Graph()
    chain = g.connect(f.add_10, f.add_20)
    start = chain[0].a
    
    g.stepper_prepare(start, 5)
    s = g.stepper()
    
    # Get raw ArgsPack objects
    for akw in stream(s, unwrap=False):
        print(f"ArgsPack: args={akw.args}, kwargs={akw.kwargs}")
        print(f"  Flattened: {akw.flat()}")


def example_5_collect_while_streaming():
    """Example 5: Collect results while streaming"""
    print("\n=== Example 5: Collect While Streaming ===")
    
    g = Graph()
    source = as_unit(lambda x: x * 2, name='source')
    g.add(source, as_unit(lambda x: x + 10, name='fast'))
    g.add(source, as_unit(lambda x: x + 20, name='medium'))
    g.add(source, as_unit(lambda x: x + 30, name='slow'))
    
    g.stepper_prepare(source, 5)
    s = g.stepper()
    
    # Collect results as they stream
    results = []
    for result in stream(s):
        print(f"Processing: {result}")
        results.append(result)
    
    print(f"Collected results: {sorted(results)}")
    print(f"Stash is empty: {len(s.stash) == 0}")


def example_6_loop_graph():
    """Example 6: Looped graph with safety limit"""
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
    
    # Stream with safety limit
    count = 0
    max_iterations = 10
    for result in stream(s):
        print(f"Result {count}: {result}")
        count += 1
        if count >= max_iterations:
            print(f"Safety limit reached ({max_iterations} results)")
            break
    
    print(f"Stash after streaming: {len(s.stash)} nodes")


if __name__ == '__main__':
    print("Testing stream() method prototype")
    print("=" * 50)
    
    example_1_simple_linear()
    example_2_multiple_branches()
    example_3_early_termination()
    example_4_unwrap_false()
    example_5_collect_while_streaming()
    example_6_loop_graph()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")
