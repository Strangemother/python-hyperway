"""
Circuit Demo: Logic gates combining AND and NOT with OR

Based on the and-gate.py pattern but extended with multiple gates.
"""

from hyperway.graph import Graph


def and_gate(a=0, b=0):
    """Logical AND gate"""
    result = a and b
    print(f"  AND({a}, {b}) = {result}")
    return result


def not_gate(x=0):
    """Logical NOT gate"""
    result = not x
    print(f"  NOT({x}) = {result}")
    return result


def or_gate(a=0, b=0):
    """Logical OR gate"""
    result = a or b
    print(f"  OR({a}, {b}) = {result}")
    return result


def collector(v):
    """Pass through value"""
    return v


def store_result(v):
    """Store final result"""
    print(f"\n✓ Final Output: {v}\n")
    return v


def run_circuit(a_val, b_val, c_val):
    """
    Build circuit:
    
      A ──→ [AND] ──┐
                    ├──→ [OR] ──→ Output
      B ──→ [NOT] ──┘
      
      C is the second input to AND
    """
    print(f"\n{'='*50}")
    print(f"Circuit: A={a_val}, B={b_val}, C={c_val}")
    print(f"{'='*50}")
    
    g = Graph(tuple)
    
    # Build backwards from output, like the and-gate example
    # Final OR gate
    or_edge = g.add(or_gate, store_result)
    or_node = or_edge.a
    or_node.merge_node = True  # Accepts two inputs
    
    # AND gate feeds into OR
    and_edge = g.add(and_gate, or_node)
    and_node = and_edge.a
    and_node.merge_node = True  # Accepts two inputs
    
    # NOT gate feeds into OR
    not_edge = g.add(not_gate, or_node)
    not_node = not_edge.a
    
    # Input paths to the gates (these are our entry points)
    input_a_path = g.add(collector, and_node)
    input_c_path = g.add(collector, and_node)
    input_b_path = g.add(collector, not_node)
    
    # Prepare stepper with start nodes (entry points)
    g.stepper_prepare_many(
        (input_a_path.a, a_val),
        (input_c_path.a, c_val),
        (input_b_path.a, b_val),
    )
    
    # Create stepper with concatenation enabled
    s = g.stepper()
    s.concat_aware = True
    
    # Execute step by step
    print("Execution steps:")
    step_num = 0
    while True:
        rows = s.step()
        if not rows:
            break
        step_num += 1
        print(f"  Step {step_num}: {len(rows)} node(s)")
    
    # Get result from stash
    # The stash stores final values using the PartialConnection to the final node as key
    result = None
    if s.stash:
        # Get all values from the stash
        for key, value_tuple in s.stash.items():
            if value_tuple and len(value_tuple) > 0:
                first_argpack = value_tuple[0]
                if hasattr(first_argpack, 'args') and first_argpack.args:
                    result = first_argpack.args[0]
                    break
    return g, s, result


if __name__ == '__main__':
    print("\n" + "="*70)
    print("CIRCUIT DEMONSTRATION: AND + NOT + OR with Hyperway")
    print("="*70)
    
    # Test truth table
    test_cases = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 1),
        (1, 1, 0),
        (1, 1, 1),
    ]
    
    results = []
    for a, b, c in test_cases:
        g, stepper, output = run_circuit(a, b, c)
        and_result = a and c
        not_result = not b
        or_result = and_result or not_result
        results.append((a, b, c, and_result, not_result, or_result, output))
    
    # Summary
    print("\n" + "="*70)
    print("TRUTH TABLE: OR(AND(A,C), NOT(B))")
    print("="*70)
    print("A | B | C | AND(A,C) | NOT(B) | OR Result | Stepper Output")
    print("-" * 70)
    for a, b, c, and_r, not_r, or_r, out in results:
        output_str = str(int(out)) if out is not None else "?"
        print(f"{a} | {b} | {c} |    {int(and_r)}     |   {int(not_r)}    |    {int(or_r)}     |   {output_str}")
    
    print("\n✓ Demo complete!\n")
