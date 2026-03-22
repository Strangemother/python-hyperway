"""
Ship Power Bus: Merge nodes and fan-in wiring

Demonstrates the power bus concept from the spaceship framework article:
multiple reactors feeding a single bus, which then distributes to consumers.

    Reactor A --\
                 +--> [Power Bus] --[cable]--> Shield
    Reactor B --/

Run:
    python ship-power-bus.py
"""

from hyperway.graph import Graph
from hyperway.nodes import as_unit
from hyperway.packer import argspack


# -- Ship Components -----------------------------------------------------------

class Reactor:
    """A power reactor that burns fuel to generate watts."""

    def __init__(self, name, max_output=100):
        self.name = name
        self.max_output = max_output
        self.fuel = 500

    def generate(self, throttle=1.0):
        """Generate power based on throttle setting."""
        self.fuel -= throttle * 0.1
        watts = self.max_output * throttle
        print(f"  [{self.name}] Generating {watts:.1f}W")
        return watts


class Shield:
    """A shield generator that absorbs power to build charge."""

    def __init__(self):
        self.charge = 0
        self.max_charge = 200

    def receive_power(self, watts=0):
        """Absorb incoming power."""
        gained = watts * 0.1
        self.charge = min(self.max_charge, self.charge + gained)
        print(f"  [Shields] +{gained:.1f}W -> charge: {self.charge:.1f}/{self.max_charge}")
        return self.charge


class LifeSupport:
    """Life support systems."""

    def __init__(self):
        self.active = True

    def receive_power(self, watts=0):
        """Needs at least 20W to stay online."""
        self.active = watts >= 20
        status = "ONLINE" if self.active else "OFFLINE"
        print(f"  [Life Support] Receiving {watts:.1f}W -> {status}")
        return watts


# -- Bus and Cable Functions ---------------------------------------------------

def power_bus(a=0, b=0):
    """Combine power from multiple sources.

    As a merge node, this receives all incoming values at once.
    """
    total = a + b
    print(f"  [Power Bus] Input {a:.1f}W + {b:.1f}W = {total:.1f}W total")
    return total


def power_cable(watts, *a, **kw):
    """Standard cable with 10% loss."""
    delivered = watts * 0.9
    print(f"    [cable] {watts:.1f}W -> {delivered:.1f}W (10% loss)")
    return argspack(delivered, **kw)


def collector(v):
    """Pass-through node for input routing."""
    return v


def display_result(v):
    """Terminal node to display final value."""
    print(f"  [Output] Final value: {v}")
    return v


# -- Example 1: Dual reactor power bus ----------------------------------------

def example_dual_reactor_bus():
    """Two reactors feed a single power bus, which feeds shields."""
    print("=" * 60)
    print("Example 1: Dual Reactor Power Bus")
    print("  Reactor A (100W) --\\")
    print("                      +--> [Bus] --[cable]--> Shield")
    print("  Reactor B (150W) --/")
    print("=" * 60)
    print()

    reactor_a = Reactor('Reactor A', max_output=100)
    reactor_b = Reactor('Reactor B', max_output=150)
    shield = Shield()

    g = Graph(tuple)

    # Power bus merges two inputs, then feeds shield through cable
    bus_edge = g.add(power_bus, shield.receive_power, through=power_cable)
    bus_node = bus_edge.a
    bus_node.merge_node = True  # Accept multiple inputs

    # Two input legs to the bus
    leg_a = g.add(collector, bus_node)
    leg_b = g.add(collector, bus_node)

    # Prepare with both reactors generating at full throttle
    # We use collectors as entry points, feeding reactor output values
    g.stepper_prepare_many(
        (leg_a.a, reactor_a.generate(1.0)),
        (leg_b.a, reactor_b.generate(1.0)),
    )

    s = g.stepper()
    s.concat_aware = True

    print("\nStepping through the power bus:")
    step = 0
    while True:
        rows = s.step()
        if not rows:
            break
        step += 1
        print(f"  -- Step {step}: {len(rows)} node(s) executed --")

    print(f"\nResult: Shield charge = {shield.charge:.1f}")
    print()


# -- Example 2: Bus distributing to multiple consumers ------------------------

def example_bus_distribution():
    """One bus feeds both shields and life support."""
    print("=" * 60)
    print("Example 2: Bus Distribution to Multiple Consumers")
    print("  Reactor (200W) --> [Bus] --+--> Shield")
    print("                             +--> Life Support")
    print("=" * 60)
    print()

    reactor = Reactor('Main Reactor', max_output=200)
    shield = Shield()
    life_support = LifeSupport()

    g = Graph(tuple)

    # Pre-wrap so stepper can find connections
    reactor_unit = as_unit(reactor.generate)

    # Reactor fans out to shield and life support through cables
    g.add(reactor_unit, shield.receive_power, through=power_cable)
    g.add(reactor_unit, life_support.receive_power, through=power_cable)

    g.stepper_prepare(reactor_unit, 1.0)
    s = g.stepper()

    print("Stepping:")
    step = 0
    while True:
        rows = s.step()
        if not rows:
            break
        step += 1
        print(f"  -- Step {step}: {len(rows)} node(s) --")

    print(f"\nResults:")
    print(f"  Shield charge: {shield.charge:.1f}")
    print(f"  Life support: {'ONLINE' if life_support.active else 'OFFLINE'}")
    print()


# -- Example 3: Low power scenario ---------------------------------------------

def example_low_power():
    """What happens when the reactor is almost out of fuel?"""
    print("=" * 60)
    print("Example 3: Low Power - Life Support at Risk")
    print("=" * 60)
    print()

    reactor = Reactor('Dying Reactor', max_output=30)
    life_support = LifeSupport()

    g = Graph(tuple)

    reactor_unit = as_unit(reactor.generate)
    g.add(reactor_unit, life_support.receive_power, through=power_cable)

    # Throttle to 50% — only 15W output, cable drops it to 13.5W
    g.stepper_prepare(reactor_unit, 0.5)
    s = g.stepper()

    print("Stepping with low throttle (0.5):")
    while True:
        rows = s.step()
        if not rows:
            break

    print(f"\nLife support needs 20W minimum.")
    print(f"  Status: {'ONLINE' if life_support.active else 'OFFLINE - CRITICAL!'}")
    print()


# -- Run all examples ----------------------------------------------------------

if __name__ == '__main__':
    print()
    print("*" * 60)
    print("SPACESHIP POWER BUS: Merge Nodes with Hyperway")
    print("*" * 60)
    print()

    example_dual_reactor_bus()
    example_bus_distribution()
    example_low_power()

    print("*" * 60)
    print("Done! See docs/spaceship-operating-framework.md for details.")
    print("*" * 60)
