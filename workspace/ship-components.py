"""
Ship Components: Basic wiring between hardware units

Demonstrates the core concept from the spaceship framework article:
components as nodes, cables as connections with wire functions.

    Reactor --[power_cable]--> Shield
    Reactor --[power_cable]--> Weapons

Run:
    python ship-components.py
"""

from hyperway.graph import Graph
from hyperway.edges import make_edge
from hyperway.nodes import as_unit
from hyperway.packer import argspack


# -- Ship Components (nodes) --------------------------------------------------

class Reactor:
    """A power reactor that burns fuel to generate watts."""

    def __init__(self, name, max_output=100):
        self.name = name
        self.max_output = max_output
        self.efficiency = 1.0
        self.fuel = 1000

    def generate(self, throttle=1.0):
        """Generate power based on throttle setting."""
        if self.fuel <= 0:
            print(f"  [{self.name}] Out of fuel!")
            return 0
        self.fuel -= throttle * 0.1
        watts = self.max_output * throttle * self.efficiency
        print(f"  [{self.name}] Generating {watts:.1f}W "
              f"(fuel: {self.fuel:.1f}, throttle: {throttle})")
        return watts


class Shield:
    """A shield generator that absorbs power to build charge."""

    def __init__(self, name='Shields'):
        self.name = name
        self.charge = 0
        self.max_charge = 100

    def receive_power(self, watts=0):
        """Absorb incoming power to charge shields."""
        gained = watts * 0.1
        self.charge = min(self.max_charge, self.charge + gained)
        print(f"  [{self.name}] +{gained:.1f}W absorbed, "
              f"charge: {self.charge:.1f}/{self.max_charge}")
        return self.charge


class Weapons:
    """A weapons system that stores power for firing."""

    def __init__(self, name='Weapons'):
        self.name = name
        self.charge = 0

    def receive_power(self, watts=0):
        """Store incoming power for weapons."""
        self.charge += watts * 0.05
        print(f"  [{self.name}] +{watts * 0.05:.1f}W stored, "
              f"charge: {self.charge:.1f}")
        return self.charge


# -- Cable Wire Functions (edge transforms) ------------------------------------

def power_cable(watts, *a, **kw):
    """Standard power cable with 10% transmission loss."""
    delivered = watts * 0.9
    print(f"    [cable] {watts:.1f}W in -> {delivered:.1f}W out (10% loss)")
    return argspack(delivered, **kw)


def heavy_cable(watts, *a, **kw):
    """Heavy-duty cable with only 5% loss."""
    delivered = watts * 0.95
    print(f"    [heavy cable] {watts:.1f}W in -> {delivered:.1f}W out (5% loss)")
    return argspack(delivered, **kw)


# -- Example 1: Single Connection with pluck() --------------------------------

def example_single_connection():
    """Connect a reactor to shields through a cable and pluck it."""
    print("=" * 60)
    print("Example 1: Single connection (pluck)")
    print("=" * 60)
    print()

    reactor = Reactor('Main Reactor')
    shield = Shield()

    # Make a single edge: reactor -> cable -> shield
    connection = make_edge(reactor.generate, shield.receive_power,
                           through=power_cable)

    # Pluck it with a throttle value
    print("Plucking with throttle=0.8:")
    result = connection.pluck(0.8)
    print(f"\nShield charge after pluck: {shield.charge:.1f}")
    print(f"Reactor fuel remaining: {reactor.fuel:.1f}")
    print()


# -- Example 2: Fan-out (one reactor, multiple consumers) ---------------------

def example_fan_out():
    """One reactor feeds shields and weapons through separate cables."""
    print("=" * 60)
    print("Example 2: Fan-out (one source, two consumers)")
    print("=" * 60)
    print()

    reactor = Reactor('Main Reactor', max_output=200)
    shield = Shield()
    weapons = Weapons()

    g = Graph(tuple)

    # Pre-wrap with as_unit so the same Unit is reused across connections
    reactor_unit = as_unit(reactor.generate)

    # Connect reactor to both systems through cables
    g.add(reactor_unit, shield.receive_power, through=power_cable)
    g.add(reactor_unit, weapons.receive_power, through=heavy_cable)

    # Prepare and run
    g.stepper_prepare(reactor_unit, 1.0)
    s = g.stepper()

    print("Tick 1: Reactor generates, cables transmit...")
    s.step()   # Reactor generates
    print()
    print("Tick 2: Consumers receive power...")
    s.step()   # Shield and weapons receive

    print(f"\nAfter one tick:")
    print(f"  Shield charge: {shield.charge:.1f}")
    print(f"  Weapons charge: {weapons.charge:.1f}")
    print(f"  Reactor fuel: {reactor.fuel:.1f}")
    print()


# -- Example 3: Swapping cables -----------------------------------------------

def example_cable_swap():
    """Show how swapping wire functions changes behaviour."""
    print("=" * 60)
    print("Example 3: Swapping cables (wire function comparison)")
    print("=" * 60)
    print()

    # Standard cable
    reactor_a = Reactor('Reactor A')
    shield_a = Shield('Shield-Standard')
    conn_standard = make_edge(reactor_a.generate, shield_a.receive_power,
                              through=power_cable)

    print("Standard cable:")
    conn_standard.pluck(1.0)
    print(f"  Shield charge: {shield_a.charge:.1f}")
    print()

    # Heavy-duty cable (same components, different cable)
    reactor_b = Reactor('Reactor B')
    shield_b = Shield('Shield-Heavy')
    conn_heavy = make_edge(reactor_b.generate, shield_b.receive_power,
                           through=heavy_cable)

    print("Heavy-duty cable:")
    conn_heavy.pluck(1.0)
    print(f"  Shield charge: {shield_b.charge:.1f}")
    print()

    print("Same reactor, same shield — different cable, different result.")
    print(f"  Standard delivered: {shield_a.charge:.1f}")
    print(f"  Heavy-duty delivered: {shield_b.charge:.1f}")
    print()


# -- Run all examples ----------------------------------------------------------

if __name__ == '__main__':
    print()
    print("*" * 60)
    print("SPACESHIP COMPONENTS: Basic Wiring with Hyperway")
    print("*" * 60)
    print()

    example_single_connection()
    example_fan_out()
    example_cable_swap()

    print("*" * 60)
    print("Done! See docs/spaceship-operating-framework.md for details.")
    print("*" * 60)
