"""Example demonstrating the use of INITIATE_* constants.

This shows how to use the constants instead of magic strings when
configuring the stepper's initiation mode.
"""

from hyperway import Graph, as_unit, argspack
from hyperway import INITIATE_DISTRIBUTED, INITIATE_UNIFIED


def multiply_by_2(x):
    return x * 2


def add_10(x):
    return x + 10


def main():
    g = Graph()
    
    # Create a node with two outgoing connections
    start = as_unit(multiply_by_2)
    g.add(start, add_10)
    g.add(start, add_10)
    
    print("=" * 60)
    print("INITIATE_DISTRIBUTED Mode (default - edge-centric)")
    print("=" * 60)
    
    # Using the constant instead of 'distributed' string
    g.stepper_prepare(start, 5)
    s = g.stepper()
    s.initiate = INITIATE_DISTRIBUTED  # Can also be set this way
    
    rows = s.step()
    print(f"Start node called per connection: {len(rows)} rows")
    print(f"Initiate mode: {s.initiate}")
    
    print("\n" + "=" * 60)
    print("INITIATE_UNIFIED Mode (node-centric)")
    print("=" * 60)
    
    # Using the constant instead of 'unified' string
    s2 = g.stepper()
    s2.prepare(start, akw=argspack(5), initiate=INITIATE_UNIFIED)
    
    rows2 = s2.step()
    print(f"Start node called once, result distributed: {len(rows2)} rows")
    print(f"Initiate mode: {s2.initiate}")
    
    print("\n" + "=" * 60)
    print("Type-safe constants prevent typos!")
    print("=" * 60)
    
    # These constants are the actual string values
    print(f"INITIATE_DISTRIBUTED = '{INITIATE_DISTRIBUTED}'")
    print(f"INITIATE_UNIFIED = '{INITIATE_UNIFIED}'")
    
    # But using constants means typos become NameErrors, not silent bugs
    # INITIATE_UNIFFIED would raise NameError instead of silently failing
    

if __name__ == '__main__':
    main()
